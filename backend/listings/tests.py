from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User
from .models import Listing


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