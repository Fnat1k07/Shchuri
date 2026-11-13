import shutil
import tempfile
from io import BytesIO
from unittest.mock import patch

from django.db import IntegrityError, transaction, connection
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from datetime import timedelta
from PIL import Image

from .models import Amenity, Listing, ListingImage, ViewingRequest, Favorite
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User


def make_listing(owner, **kwargs):
    data = dict(
        title='Квартира', description='Опис', price=10000,
        property_type='apartment', rooms=2, area=45,
        city='Львів', district='Галицький', address='вул. Тестова, 1',
    )
    data.update(kwargs)
    return Listing.objects.create(owner=owner, **data)


def items(response):
    data = response.data
    return data['results'] if isinstance(data, dict) else data


class ListingApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            'owner@example.com', 'Pass12345!', first_name='О', last_name='В', role='owner')
        self.other = User.objects.create_user(
            'other@example.com', 'Pass12345!', first_name='І', last_name='Н', role='owner')
        self.tenant = User.objects.create_user(
            'tenant@example.com', 'Pass12345!', first_name='Т', last_name='Н', role='tenant')
        self.list_url = reverse('listing-list')
        self.mine_url = reverse('listing-mine')
        self.payload = dict(
            title='Нова квартира', description='Гарна', price='12000.00',
            property_type='apartment', rooms=2, area='50.0',
            city='Львів', district='Франківський', address='вул. Нова, 5',
        )

    def test_guest_sees_only_published(self):
        make_listing(self.owner, status='published', title='Public')
        make_listing(self.owner, status='draft', title='Hidden')
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [i['title'] for i in items(response)]
        self.assertEqual(titles, ['Public'])

    def test_guest_cannot_see_draft_detail(self):
        draft = make_listing(self.owner, status='draft')
        response = self.client.get(reverse('listing-detail', args=[draft.pk]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_see_own_draft_detail(self):
        draft = make_listing(self.owner, status='draft')
        self.client.force_authenticate(self.owner)
        response = self.client.get(reverse('listing-detail', args=[draft.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_guest_cannot_create(self):
        response = self.client.post(self.list_url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tenant_cannot_create(self):
        self.client.force_authenticate(self.tenant)
        response = self.client.post(self.list_url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_creates_listing(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.list_url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        listing = Listing.objects.get(pk=response.data['id'])
        self.assertEqual(listing.owner, self.owner)
        self.assertEqual(listing.status, 'draft')

    def test_cannot_create_as_published(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            self.list_url, {**self.payload, 'status': 'published'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_set_owner_via_payload(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            self.list_url, {**self.payload, 'owner': self.other.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Listing.objects.get(pk=response.data['id']).owner, self.owner)

    def test_invalid_price(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            self.list_url, {**self.payload, 'price': '-5'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_coordinates_must_be_a_pair(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            self.list_url, {**self.payload, 'latitude': '49.84'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_updates_own_listing(self):
        listing = make_listing(self.owner, status='published')
        self.client.force_authenticate(self.owner)
        response = self.client.patch(
            reverse('listing-detail', args=[listing.pk]), {'price': '15000.00'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        listing.refresh_from_db()
        self.assertEqual(float(listing.price), 15000.0)

    def test_other_owner_cannot_update(self):
        listing = make_listing(self.owner, status='published')
        self.client.force_authenticate(self.other)
        response = self.client.patch(
            reverse('listing-detail', args=[listing.pk]), {'price': '1.00'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_other_owner_cannot_delete(self):
        listing = make_listing(self.owner, status='published')
        self.client.force_authenticate(self.other)
        response = self.client.delete(reverse('listing-detail', args=[listing.pk]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_deletes_own_listing(self):
        listing = make_listing(self.owner)
        self.client.force_authenticate(self.owner)
        response = self.client.delete(reverse('listing-detail', args=[listing.pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_status_draft_to_pending_allowed(self):
        listing = make_listing(self.owner, status='draft')
        self.client.force_authenticate(self.owner)
        response = self.client.patch(
            reverse('listing-detail', args=[listing.pk]), {'status': 'pending'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_owner_cannot_publish_himself(self):
        listing = make_listing(self.owner, status='pending')
        self.client.force_authenticate(self.owner)
        response = self.client.patch(
            reverse('listing-detail', args=[listing.pk]), {'status': 'published'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mine_returns_only_own_listings(self):
        make_listing(self.owner, status='draft', title='Mine draft')
        make_listing(self.owner, status='published', title='Mine pub')
        make_listing(self.other, status='published', title='Not mine')
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.mine_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = sorted(i['title'] for i in items(response))
        self.assertEqual(titles, ['Mine draft', 'Mine pub'])

    def test_mine_requires_authentication(self):
        response = self.client.get(self.mine_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_title_too_short(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            self.list_url, {**self.payload, 'title': 'abc'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_price_too_high(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            self.list_url, {**self.payload, 'price': '5000000'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rooms_too_many(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            self.list_url, {**self.payload, 'rooms': 50}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_required_fields_missing(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.list_url, {'title': 'Квартира тест'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ('description', 'price', 'city', 'address'):
            self.assertIn(field, response.data)

    def test_mine_filter_by_status(self):
        make_listing(self.owner, status='draft', title='Draft one')
        make_listing(self.owner, status='published', title='Pub one')
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.mine_url, {'status': 'draft'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([i['title'] for i in items(response)], ['Draft one'])

    def test_mine_invalid_status_filter(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.mine_url, {'status': 'nonsense'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_archives_listing(self):
        listing = make_listing(self.owner, status='published', title='To archive')
        self.client.force_authenticate(self.owner)
        response = self.client.patch(
            reverse('listing-detail', args=[listing.pk]), {'status': 'archived'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mine = self.client.get(self.mine_url, {'status': 'archived'})
        self.assertEqual([i['title'] for i in items(mine)], ['To archive'])

        self.client.force_authenticate(None)
        public = self.client.get(self.list_url)
        self.assertEqual(items(public), [])

    def test_mine_includes_images_field(self):
        make_listing(self.owner)
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.mine_url)
        self.assertIn('images', items(response)[0])

def make_image(name='photo.png', fmt='PNG'):
    buf = BytesIO()
    Image.new('RGB', (20, 20), 'red').save(buf, format=fmt)
    return SimpleUploadedFile(name, buf.getvalue())

            
TEMP_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ListingImageTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.owner = User.objects.create_user(
            'owner@example.com', 'Pass12345!', first_name='О', last_name='В', role='owner')
        self.other = User.objects.create_user(
            'other@example.com', 'Pass12345!', first_name='І', last_name='Н', role='owner')
        self.tenant = User.objects.create_user(
            'tenant@example.com', 'Pass12345!', first_name='Т', last_name='Н', role='tenant')
        self.listing = make_listing(self.owner, status='published')
        self.upload_url = reverse('listing-upload-image', args=[self.listing.pk])

    def upload(self, **kwargs):
        return self.client.post(
            self.upload_url, {'image': make_image(**kwargs)}, format='multipart')

    def test_first_image_becomes_cover(self):
        self.client.force_authenticate(self.owner)
        r1 = self.upload(name='a.png')
        r2 = self.upload(name='b.png')
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        self.assertTrue(r1.data['is_cover'])
        self.assertFalse(r2.data['is_cover'])

    def test_max_8_images(self):
        self.client.force_authenticate(self.owner)
        for i in range(8):
            self.assertEqual(self.upload(name=f'{i}.png').status_code, 201)
        response = self.upload(name='9.png')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.listing.images.count(), 8)

    def test_invalid_format_rejected(self):
        self.client.force_authenticate(self.owner)
        response = self.upload(name='a.gif', fmt='GIF')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_not_an_image_rejected(self):
        self.client.force_authenticate(self.owner)
        fake = SimpleUploadedFile('a.png', b'this is not an image')
        response = self.client.post(self.upload_url, {'image': fake}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_too_large_rejected(self):
        self.client.force_authenticate(self.owner)
        with patch('listings.serializers.MAX_IMAGE_SIZE', 10):
            response = self.upload()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_guest_cannot_upload(self):
        self.assertEqual(self.upload().status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tenant_cannot_upload(self):
        self.client.force_authenticate(self.tenant)
        self.assertEqual(self.upload().status_code, status.HTTP_403_FORBIDDEN)

    def test_other_owner_cannot_upload(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.upload().status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_image(self):
        self.client.force_authenticate(self.owner)
        image_id = self.upload().data['id']
        url = reverse('listing-delete-image', kwargs={'pk': self.listing.pk, 'image_id': image_id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.listing.images.count(), 0)

    def test_other_owner_cannot_delete_image(self):
        self.client.force_authenticate(self.owner)
        image_id = self.upload().data['id']
        self.client.force_authenticate(self.other)
        url = reverse('listing-delete-image', kwargs={'pk': self.listing.pk, 'image_id': image_id})
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_403_FORBIDDEN)

    def test_deleting_cover_promotes_next_image(self):
        self.client.force_authenticate(self.owner)
        cover_id = self.upload(name='a.png').data['id']
        second_id = self.upload(name='b.png').data['id']
        url = reverse('listing-delete-image', kwargs={'pk': self.listing.pk, 'image_id': cover_id})
        self.client.delete(url)
        self.assertTrue(ListingImage.objects.get(pk=second_id).is_cover)

    def test_set_cover(self):
        self.client.force_authenticate(self.owner)
        first_id = self.upload(name='a.png').data['id']
        second_id = self.upload(name='b.png').data['id']
        url = reverse('listing-set-cover', kwargs={'pk': self.listing.pk, 'image_id': second_id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(ListingImage.objects.get(pk=first_id).is_cover)
        self.assertTrue(ListingImage.objects.get(pk=second_id).is_cover)
        self.assertEqual(self.listing.images.filter(is_cover=True).count(), 1)

    def test_listing_detail_includes_images(self):
        self.client.force_authenticate(self.owner)
        self.upload()
        response = self.client.get(reverse('listing-detail', args=[self.listing.pk]))
        self.assertEqual(len(response.data['images']), 1)


class AmenityApiTests(APITestCase):
    def test_amenities_list_is_public(self):
        Amenity.objects.create(name='Wi-Fi')
        Amenity.objects.create(name='Паркінг')
        response = self.client.get(reverse('amenity-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = sorted(a['name'] for a in items(response))
        self.assertEqual(names, ['Wi-Fi', 'Паркінг'])

class ListingSearchTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            'owner@example.com', 'Pass12345!', first_name='О', last_name='В', role='owner')
        self.url = reverse('listing-list')
        self.wifi = Amenity.objects.create(name='Wi-Fi')
        self.parking = Amenity.objects.create(name='Паркінг')

        self.a = make_listing(self.owner, status='published', title='Затишна квартира в центрі',
                              city='Львів', price=8000, rooms=1, area=30)
        self.b = make_listing(self.owner, status='published', title='Простора квартира',
                              city='Київ', price=20000, rooms=3, area=90,
                              property_type='apartment', district='Печерський')
        self.c = make_listing(self.owner, status='published', title='Будинок біля лісу',
                              city='Львів', price=15000, rooms=4, area=120,
                              property_type='house')
        self.hidden = make_listing(self.owner, status='draft', title='Чернетка', city='Львів')
        self.a.amenities.add(self.wifi, self.parking)
        self.b.amenities.add(self.wifi)

    def titles(self, **params):
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return sorted(i['title'] for i in items(response))

    def test_only_published_returned(self):
        self.assertNotIn('Чернетка', self.titles())

    def test_text_search(self):
        self.assertEqual(self.titles(search='лісу'), ['Будинок біля лісу'])

    def test_search_by_city_in_text(self):
        self.assertEqual(len(self.titles(search='Київ')), 1)

    def test_filter_city(self):
        self.assertEqual(len(self.titles(city='львів')), 2)

    def test_filter_property_type(self):
        self.assertEqual(self.titles(property_type='house'), ['Будинок біля лісу'])

    def test_filter_price_range(self):
        self.assertEqual(
            self.titles(price_min=10000, price_max=16000), ['Будинок біля лісу'])

    def test_filter_rooms_and_rooms_min(self):
        self.assertEqual(self.titles(rooms=1), ['Затишна квартира в центрі'])
        self.assertEqual(len(self.titles(rooms_min=3)), 2)

    def test_filter_area(self):
        self.assertEqual(len(self.titles(area_min=80)), 2)

    def test_filter_amenities_requires_all(self):
        self.assertEqual(len(self.titles(amenities=f'{self.wifi.id}')), 2)
        self.assertEqual(
            self.titles(amenities=f'{self.wifi.id},{self.parking.id}'),
            ['Затишна квартира в центрі'])

    def test_combined_filters(self):
        self.assertEqual(
            self.titles(city='Львів', price_max=10000), ['Затишна квартира в центрі'])

    def test_ordering_by_price(self):
        response = self.client.get(self.url, {'ordering': 'price'})
        prices = [float(i['price']) for i in items(response)]
        self.assertEqual(prices, sorted(prices))
        response = self.client.get(self.url, {'ordering': '-price'})
        prices = [float(i['price']) for i in items(response)]
        self.assertEqual(prices, sorted(prices, reverse=True))

    def test_invalid_number_returns_400(self):
        response = self.client.get(self.url, {'price_min': 'abc'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('price_min', response.data)

    def test_invalid_property_type_returns_400(self):
        response = self.client.get(self.url, {'property_type': 'villa'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_price_min_greater_than_max_returns_400(self):
        response = self.client.get(self.url, {'price_min': 20000, 'price_max': 5000})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_amenities_returns_400(self):
        response = self.client.get(self.url, {'amenities': 'a,b'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pagination(self):
        for i in range(12):
            make_listing(self.owner, status='published', title=f'Додаткове {i}')
        response = self.client.get(self.url, {'page_size': 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)
        self.assertEqual(len(response.data['results']), 5)
        self.assertIsNotNone(response.data['next'])

    def test_page_size_is_capped(self):
        response = self.client.get(self.url, {'page_size': 1000})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class ListingDetailTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            'owner@example.com', 'Pass12345!', first_name='Іван', last_name='Петренко',
            role='owner', phone='+380501234567')
        self.viewer = User.objects.create_user(
            'viewer@example.com', 'Pass12345!', first_name='Т', last_name='Н', role='tenant')
        self.listing = make_listing(self.owner, status='published')
        self.url = reverse('listing-detail', args=[self.listing.pk])

    def test_guest_sees_name_but_not_phone(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['contact']['name'], 'Іван Петренко')
        self.assertIsNone(response.data['contact']['phone'])

    def test_authenticated_user_sees_phone(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.get(self.url)
        self.assertEqual(response.data['contact']['phone'], '+380501234567')

    def test_phone_not_in_list_response(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.get(reverse('listing-list'))
        self.assertNotIn('contact', items(response)[0])

    def test_view_counter_increments_for_guest(self):
        first = self.client.get(self.url)
        second = self.client.get(self.url)
        self.assertEqual(first.data['views_count'], 1)
        self.assertEqual(second.data['views_count'], 2)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.views_count, 2)

    def test_view_counter_increments_for_other_user(self):
        self.client.force_authenticate(self.viewer)
        self.client.get(self.url)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.views_count, 1)

    def test_owner_views_do_not_count(self):
        self.client.force_authenticate(self.owner)
        self.client.get(self.url)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.views_count, 0)

    def test_draft_views_do_not_count(self):
        draft = make_listing(self.owner, status='draft')
        self.client.force_authenticate(self.owner)
        self.client.get(reverse('listing-detail', args=[draft.pk]))
        draft.refresh_from_db()
        self.assertEqual(draft.views_count, 0)

    def test_nonexistent_listing_returns_404(self):
        response = self.client.get(reverse('listing-detail', args=[999999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class FavoriteApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            'owner@example.com', 'Pass12345!', first_name='О', last_name='В', role='owner')
        self.tenant = User.objects.create_user(
            'tenant@example.com', 'Pass12345!', first_name='Т', last_name='Н', role='tenant')
        self.other = User.objects.create_user(
            'other@example.com', 'Pass12345!', first_name='І', last_name='Н', role='tenant')
        self.listing = make_listing(self.owner, status='published', title='Опубліковане')
        self.draft = make_listing(self.owner, status='draft', title='Чернетка')
        self.url = reverse('favorite-list')

    def detail_url(self, listing_id):
        return reverse('favorite-detail', kwargs={'listing_id': listing_id})

    def test_guest_cannot_access(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(self.url, {'listing_id': self.listing.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_favorite(self):
        self.client.force_authenticate(self.tenant)
        response = self.client.post(self.url, {'listing_id': self.listing.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['listing']['id'], self.listing.pk)
        self.assertTrue(Favorite.objects.filter(user=self.tenant, listing=self.listing).exists())

    def test_cannot_add_draft(self):
        self.client.force_authenticate(self.tenant)
        response = self.client.post(self.url, {'listing_id': self.draft.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_add_nonexistent(self):
        self.client.force_authenticate(self.tenant)
        response = self.client.post(self.url, {'listing_id': 999999}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_add_twice(self):
        self.client.force_authenticate(self.tenant)
        self.client.post(self.url, {'listing_id': self.listing.pk}, format='json')
        response = self.client.post(self.url, {'listing_id': self.listing.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Favorite.objects.filter(user=self.tenant).count(), 1)

    def test_list_returns_only_own_favorites(self):
        second = make_listing(self.owner, status='published', title='Інше')
        Favorite.objects.create(user=self.tenant, listing=self.listing)
        Favorite.objects.create(user=self.other, listing=second)
        self.client.force_authenticate(self.tenant)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [i['listing']['id'] for i in items(response)]
        self.assertEqual(ids, [self.listing.pk])

    def test_list_hides_archived_listings(self):
        Favorite.objects.create(user=self.tenant, listing=self.listing)
        self.listing.status = 'archived'
        self.listing.save()
        self.client.force_authenticate(self.tenant)
        self.assertEqual(items(self.client.get(self.url)), [])

    def test_remove_favorite(self):
        Favorite.objects.create(user=self.tenant, listing=self.listing)
        self.client.force_authenticate(self.tenant)
        response = self.client.delete(self.detail_url(self.listing.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Favorite.objects.filter(user=self.tenant).exists())

    def test_cannot_remove_someone_elses_favorite(self):
        Favorite.objects.create(user=self.other, listing=self.listing)
        self.client.force_authenticate(self.tenant)
        response = self.client.delete(self.detail_url(self.listing.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Favorite.objects.filter(user=self.other).exists())

    def test_remove_nonexistent_favorite(self):
        self.client.force_authenticate(self.tenant)
        response = self.client.delete(self.detail_url(self.listing.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class FavoriteAndViewingRequestModelTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            'owner@example.com', 'Pass12345!', first_name='О', last_name='В', role='owner')
        self.tenant = User.objects.create_user(
            'tenant@example.com', 'Pass12345!', first_name='Т', last_name='Н', role='tenant')
        self.listing = make_listing(self.owner, status='published')

    def test_favorite_is_unique_per_user_and_listing(self):
        Favorite.objects.create(user=self.tenant, listing=self.listing)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Favorite.objects.create(user=self.tenant, listing=self.listing)

    def test_viewing_request_defaults(self):
        request = ViewingRequest.objects.create(
            listing=self.listing, tenant=self.tenant, message='Хочу переглянути')
        self.assertEqual(request.status, 'pending')
        self.assertIsNotNone(request.created_at)

    def test_only_one_pending_request_per_tenant_and_listing(self):
        ViewingRequest.objects.create(listing=self.listing, tenant=self.tenant)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ViewingRequest.objects.create(listing=self.listing, tenant=self.tenant)

    def test_new_request_allowed_after_previous_was_decided(self):
        first = ViewingRequest.objects.create(listing=self.listing, tenant=self.tenant)
        first.status = 'rejected'
        first.save()
        ViewingRequest.objects.create(listing=self.listing, tenant=self.tenant)
        self.assertEqual(ViewingRequest.objects.filter(tenant=self.tenant).count(), 2)

class IsFavoriteFieldTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            'owner@example.com', 'Pass12345!', first_name='О', last_name='В', role='owner')
        self.tenant = User.objects.create_user(
            'tenant@example.com', 'Pass12345!', first_name='Т', last_name='Н', role='tenant')
        self.other = User.objects.create_user(
            'other@example.com', 'Pass12345!', first_name='І', last_name='Н', role='tenant')
        self.fav = make_listing(self.owner, status='published', title='Обране')
        self.plain = make_listing(self.owner, status='published', title='Звичайне')
        Favorite.objects.create(user=self.tenant, listing=self.fav)
        self.list_url = reverse('listing-list')

    def flags(self, response):
        return {i['title']: i['is_favorite'] for i in items(response)}

    def test_guest_gets_false(self):
        response = self.client.get(self.list_url)
        self.assertEqual(self.flags(response), {'Обране': False, 'Звичайне': False})

    def test_user_sees_own_favorites_in_list(self):
        self.client.force_authenticate(self.tenant)
        response = self.client.get(self.list_url)
        self.assertEqual(self.flags(response), {'Обране': True, 'Звичайне': False})

    def test_other_users_favorites_do_not_count(self):
        self.client.force_authenticate(self.other)
        response = self.client.get(self.list_url)
        self.assertEqual(self.flags(response), {'Обране': False, 'Звичайне': False})

    def test_detail_has_is_favorite(self):
        self.client.force_authenticate(self.tenant)
        yes = self.client.get(reverse('listing-detail', args=[self.fav.pk]))
        no = self.client.get(reverse('listing-detail', args=[self.plain.pk]))
        self.assertTrue(yes.data['is_favorite'])
        self.assertFalse(no.data['is_favorite'])

    def test_flag_updates_after_removing_favorite(self):
        self.client.force_authenticate(self.tenant)
        self.client.delete(reverse('favorite-detail', kwargs={'listing_id': self.fav.pk}))
        response = self.client.get(self.list_url)
        self.assertEqual(self.flags(response), {'Обране': False, 'Звичайне': False})

    def test_flag_updates_after_adding_favorite(self):
        self.client.force_authenticate(self.tenant)
        self.client.post(reverse('favorite-list'), {'listing_id': self.plain.pk}, format='json')
        response = self.client.get(self.list_url)
        self.assertEqual(self.flags(response), {'Обране': True, 'Звичайне': True})

    def test_is_favorite_cannot_be_set_by_client(self):
        self.client.force_authenticate(self.owner)
        payload = dict(
            title='Нова квартира', description='Гарна', price='12000.00',
            property_type='apartment', rooms=2, area='50.0',
            city='Львів', district='Франківський', address='вул. Нова, 5',
            is_favorite=True,
        )
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['is_favorite'])

    def test_favorites_are_loaded_with_a_single_query(self):
        for i in range(5):
            make_listing(self.owner, status='published', title=f'Ще {i}')
        self.client.force_authenticate(self.tenant)
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        favorite_queries = [q for q in ctx.captured_queries if 'listings_favorite' in q['sql']]
        self.assertEqual(len(favorite_queries), 1)

class ViewingRequestApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            'owner@example.com', 'Pass12345!', first_name='Іван', last_name='Власник', role='owner')
        self.other_owner = User.objects.create_user(
            'other.owner@example.com', 'Pass12345!', first_name='О', last_name='І', role='owner')
        self.tenant = User.objects.create_user(
            'tenant@example.com', 'Pass12345!', first_name='Марія', last_name='Орендар',
            role='tenant', phone='+380671112233')
        self.tenant2 = User.objects.create_user(
            'tenant2@example.com', 'Pass12345!', first_name='Т', last_name='Два', role='tenant')
        self.listing = make_listing(self.owner, status='published', title='Опубліковане')
        self.draft = make_listing(self.owner, status='draft', title='Чернетка')
        self.url = reverse('viewing-request-list')
        self.incoming_url = reverse('viewing-request-incoming')

    def detail(self, pk):
        return reverse('viewing-request-detail', args=[pk])

    def action_url(self, name, pk):
        return reverse(f'viewing-request-{name}', args=[pk])

    def make_request(self, tenant=None, listing=None, **kwargs):
        return ViewingRequest.objects.create(
            tenant=tenant or self.tenant, listing=listing or self.listing, **kwargs)

    # ---- створення ----
    def test_guest_cannot_access(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(self.incoming_url).status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(self.url, {'listing_id': self.listing.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tenant_creates_request(self):
        self.client.force_authenticate(self.tenant)
        response = self.client.post(
            self.url, {'listing_id': self.listing.pk, 'message': 'Хочу переглянути'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'pending')
        self.assertEqual(response.data['listing']['id'], self.listing.pk)
        self.assertEqual(response.data['tenant']['name'], 'Марія Орендар')
        self.assertTrue(ViewingRequest.objects.filter(tenant=self.tenant).exists())

    def test_owner_role_cannot_create(self):
        self.client.force_authenticate(self.other_owner)
        response = self.client.post(self.url, {'listing_id': self.listing.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_request_draft_listing(self):
        self.client.force_authenticate(self.tenant)
        response = self.client.post(self.url, {'listing_id': self.draft.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_request_nonexistent_listing(self):
        self.client.force_authenticate(self.tenant)
        response = self.client.post(self.url, {'listing_id': 999999}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_listing_id_is_required(self):
        self.client.force_authenticate(self.tenant)
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('listing_id', response.data)

    def test_cannot_create_second_pending_request(self):
        self.client.force_authenticate(self.tenant)
        self.client.post(self.url, {'listing_id': self.listing.pk}, format='json')
        response = self.client.post(self.url, {'listing_id': self.listing.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ViewingRequest.objects.filter(tenant=self.tenant).count(), 1)

    def test_can_create_again_after_decision(self):
        self.make_request(status='rejected')
        self.client.force_authenticate(self.tenant)
        response = self.client.post(self.url, {'listing_id': self.listing.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_past_datetime_rejected(self):
        self.client.force_authenticate(self.tenant)
        past = (timezone.now() - timedelta(days=1)).isoformat()
        response = self.client.post(
            self.url, {'listing_id': self.listing.pk, 'preferred_datetime': past}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_future_datetime_accepted(self):
        self.client.force_authenticate(self.tenant)
        future = (timezone.now() + timedelta(days=2)).isoformat()
        response = self.client.post(
            self.url, {'listing_id': self.listing.pk, 'preferred_datetime': future}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_message_too_long_rejected(self):
        self.client.force_authenticate(self.tenant)
        response = self.client.post(
            self.url, {'listing_id': self.listing.pk, 'message': 'a' * 1001}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tenant_cannot_set_status_via_payload(self):
        self.client.force_authenticate(self.tenant)
        response = self.client.post(
            self.url, {'listing_id': self.listing.pk, 'status': 'approved'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'pending')

    # ---- списки ----
    def test_list_returns_only_own_requests(self):
        mine = self.make_request(tenant=self.tenant)
        self.make_request(tenant=self.tenant2)
        self.client.force_authenticate(self.tenant)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([i['id'] for i in items(response)], [mine.pk])

    def test_incoming_returns_requests_for_own_listings(self):
        req = self.make_request()
        foreign_listing = make_listing(self.other_owner, status='published', title='Чуже')
        self.make_request(listing=foreign_listing)
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.incoming_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([i['id'] for i in items(response)], [req.pk])

    def test_owner_sees_tenant_contact_in_incoming(self):
        self.make_request()
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.incoming_url)
        self.assertEqual(items(response)[0]['tenant']['phone'], '+380671112233')

    def test_other_owner_sees_nothing_incoming(self):
        self.make_request()
        self.client.force_authenticate(self.other_owner)
        self.assertEqual(items(self.client.get(self.incoming_url)), [])

    def test_status_filter(self):
        self.make_request(tenant=self.tenant, status='pending')
        self.make_request(tenant=self.tenant, listing=make_listing(
            self.owner, status='published', title='Друге'), status='approved')
        self.client.force_authenticate(self.tenant)
        response = self.client.get(self.url, {'status': 'approved'})
        self.assertEqual([i['status'] for i in items(response)], ['approved'])

    def test_invalid_status_filter(self):
        self.client.force_authenticate(self.tenant)
        response = self.client.get(self.url, {'status': 'nonsense'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---- деталі ----
    def test_retrieve_by_tenant_and_owner(self):
        req = self.make_request()
        for user in (self.tenant, self.owner):
            self.client.force_authenticate(user)
            response = self.client.get(self.detail(req.pk))
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_by_stranger_is_404(self):
        req = self.make_request()
        for user in (self.tenant2, self.other_owner):
            self.client.force_authenticate(user)
            response = self.client.get(self.detail(req.pk))
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_methods_not_allowed(self):
        req = self.make_request()
        self.client.force_authenticate(self.tenant)
        self.assertEqual(
            self.client.patch(self.detail(req.pk), {'status': 'approved'}, format='json').status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED)

    # ---- approve / reject ----
    def test_owner_approves(self):
        req = self.make_request()
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.action_url('approve', req.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'approved')
        req.refresh_from_db()
        self.assertEqual(req.status, 'approved')

    def test_owner_rejects(self):
        req = self.make_request()
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.action_url('reject', req.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        req.refresh_from_db()
        self.assertEqual(req.status, 'rejected')

    def test_tenant_cannot_approve_or_reject(self):
        req = self.make_request()
        self.client.force_authenticate(self.tenant)
        for name in ('approve', 'reject'):
            response = self.client.post(self.action_url(name, req.pk))
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        req.refresh_from_db()
        self.assertEqual(req.status, 'pending')

    def test_other_owner_cannot_approve(self):
        req = self.make_request()
        self.client.force_authenticate(self.other_owner)
        response = self.client.post(self.action_url('approve', req.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_guest_cannot_approve(self):
        req = self.make_request()
        response = self.client.post(self.action_url('approve', req.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_decide_twice(self):
        req = self.make_request(status='approved')
        self.client.force_authenticate(self.owner)
        for name in ('approve', 'reject'):
            response = self.client.post(self.action_url(name, req.pk))
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        req.refresh_from_db()
        self.assertEqual(req.status, 'approved')

    def test_cannot_approve_if_listing_not_published(self):
        req = self.make_request()
        self.listing.status = 'archived'
        self.listing.save()
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.action_url('approve', req.pk))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_reject_even_if_listing_archived(self):
        req = self.make_request()
        self.listing.status = 'archived'
        self.listing.save()
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.action_url('reject', req.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ---- скасування ----
    def test_tenant_cancels_pending_request(self):
        req = self.make_request()
        self.client.force_authenticate(self.tenant)
        response = self.client.delete(self.detail(req.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ViewingRequest.objects.filter(pk=req.pk).exists())

    def test_cannot_cancel_decided_request(self):
        req = self.make_request(status='approved')
        self.client.force_authenticate(self.tenant)
        response = self.client.delete(self.detail(req.pk))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(ViewingRequest.objects.filter(pk=req.pk).exists())

    def test_owner_cannot_delete_request(self):
        req = self.make_request()
        self.client.force_authenticate(self.owner)
        response = self.client.delete(self.detail(req.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_stranger_cannot_delete_request(self):
        req = self.make_request()
        self.client.force_authenticate(self.tenant2)
        response = self.client.delete(self.detail(req.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AccessMatrixTests(APITestCase):
    """S3-BE-16: що бачать і можуть гість, орендар, власник та чужий власник."""

    OWNER_PHONE = '+380501234567'

    def setUp(self):
        self.owner = User.objects.create_user(
            'owner@example.com', 'Pass12345!', first_name='Іван', last_name='Власник',
            role='owner', phone=self.OWNER_PHONE)
        self.other_owner = User.objects.create_user(
            'other.owner@example.com', 'Pass12345!', first_name='О', last_name='І', role='owner')
        self.tenant = User.objects.create_user(
            'tenant@example.com', 'Pass12345!', first_name='Т', last_name='Н', role='tenant')
        self.published = make_listing(self.owner, status='published', title='Опубліковане')
        self.draft = make_listing(self.owner, status='draft', title='Чернетка')
        self.published_url = reverse('listing-detail', args=[self.published.pk])
        self.draft_url = reverse('listing-detail', args=[self.draft.pk])

    def call(self, method, url):
        return self.client.generic(method.upper(), url)

    def check(self, cases):
        for method, url, expected in cases:
            with self.subTest(method=method, url=url):
                self.assertEqual(self.call(method, url).status_code, expected)

    def test_guest_access(self):
        self.check([
            ('get', reverse('listing-list'), 200),
            ('get', self.published_url, 200),
            ('get', self.draft_url, 404),
            ('get', reverse('amenity-list'), 200),
            ('post', reverse('listing-list'), 401),
            ('patch', self.published_url, 401),
            ('delete', self.published_url, 401),
            ('get', reverse('listing-mine'), 401),
            ('get', reverse('favorite-list'), 401),
            ('post', reverse('favorite-list'), 401),
            ('get', reverse('viewing-request-list'), 401),
            ('post', reverse('viewing-request-list'), 401),
            ('get', reverse('viewing-request-incoming'), 401),
            ('post', reverse('listing-upload-image', args=[self.published.pk]), 401),
        ])

    def test_tenant_access(self):
        self.client.force_authenticate(self.tenant)
        self.check([
            ('get', reverse('listing-list'), 200),
            ('get', self.published_url, 200),
            ('get', self.draft_url, 404),
            ('post', reverse('listing-list'), 403),
            ('patch', self.published_url, 403),
            ('delete', self.published_url, 403),
            ('get', reverse('listing-mine'), 200),
            ('get', reverse('favorite-list'), 200),
            ('get', reverse('viewing-request-list'), 200),
            ('get', reverse('viewing-request-incoming'), 200),
            ('post', reverse('listing-upload-image', args=[self.published.pk]), 403),
        ])

    def test_listing_owner_access(self):
        self.client.force_authenticate(self.owner)
        self.check([
            ('get', self.published_url, 200),
            ('get', self.draft_url, 200),
            ('get', reverse('listing-mine'), 200),
            ('get', reverse('viewing-request-incoming'), 200),
            ('post', reverse('viewing-request-list'), 403),
        ])

    def test_other_owner_access(self):
        self.client.force_authenticate(self.other_owner)
        self.check([
            ('get', self.published_url, 200),
            ('get', self.draft_url, 404),
            ('patch', self.published_url, 403),
            ('delete', self.published_url, 403),
            ('post', reverse('listing-upload-image', args=[self.published.pk]), 403),
        ])

    def test_guest_does_not_see_private_data(self):
        for url in (reverse('listing-list'), self.published_url):
            body = self.call('get', url).content.decode()
            with self.subTest(url=url):
                self.assertNotIn(self.OWNER_PHONE, body)
                self.assertNotIn('owner@example.com', body)

    def test_phone_only_in_detail_for_authenticated(self):
        self.client.force_authenticate(self.tenant)
        listing_body = self.call('get', reverse('listing-list')).content.decode()
        detail_body = self.call('get', self.published_url).content.decode()
        self.assertNotIn(self.OWNER_PHONE, listing_body)
        self.assertIn(self.OWNER_PHONE, detail_body)
        self.assertNotIn('owner@example.com', detail_body)

    def test_favorites_do_not_expose_contacts(self):
        Favorite.objects.create(user=self.tenant, listing=self.published)
        self.client.force_authenticate(self.tenant)
        body = self.call('get', reverse('favorite-list')).content.decode()
        self.assertNotIn(self.OWNER_PHONE, body)
        self.assertNotIn('owner@example.com', body)

    def test_archived_listing_hidden_from_public_but_visible_to_owner(self):
        self.published.status = 'archived'
        self.published.save()
        self.assertEqual(self.call('get', self.published_url).status_code, 404)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.call('get', self.published_url).status_code, 200)