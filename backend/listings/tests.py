import shutil
import tempfile
from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from .models import Amenity, Listing, ListingImage
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