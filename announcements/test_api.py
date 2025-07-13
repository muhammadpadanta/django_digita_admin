# announcements/test_api.py
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Pengumuman
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

# Mark all tests in this module as needing database access
pytestmark = pytest.mark.django_db


# --- Fixtures ---

@pytest.fixture
def api_client():
    """Fixture for a DRF API client."""
    return APIClient()

@pytest.fixture
def pengumuman_tanpa_lampiran():
    """Fixture for a Pengumuman instance without an attachment."""
    return Pengumuman.objects.create(
        judul="Pengumuman Tanpa Lampiran",
        deskripsi="Ini adalah deskripsi untuk pengumuman tanpa lampiran.",
        tanggal_mulai=timezone.now().date(),
        tanggal_selesai=(timezone.now() + timezone.timedelta(days=7)).date()
    )

@pytest.fixture
def pengumuman_dengan_lampiran():
    """Fixture for a Pengumuman instance with an attachment."""
    # Create a dummy file for the attachment
    dummy_file = SimpleUploadedFile(
        "test_file.txt",
        b"file_content",
        content_type="text/plain"
    )
    return Pengumuman.objects.create(
        judul="Pengumuman Dengan Lampiran",
        deskripsi="Ini adalah deskripsi untuk pengumuman dengan lampiran.",
        tanggal_mulai=timezone.now().date(),
        tanggal_selesai=(timezone.now() + timezone.timedelta(days=7)).date(),
        lampiran=dummy_file
    )


# --- API Test Classes ---

class TestPengumumanAPI:
    """
    Tests for the Pengumuman API endpoints.
    """

    def test_get_pengumuman_list_success(self, api_client, pengumuman_tanpa_lampiran, pengumuman_dengan_lampiran):
        """
        Test successfully retrieving the list of announcements.
        """
        url = reverse('api-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 2
        titles = [item['judul'] for item in response.json()]
        assert pengumuman_tanpa_lampiran.judul in titles
        assert pengumuman_dengan_lampiran.judul in titles

    def test_get_pengumuman_list_includes_lampiran_url(self, api_client, pengumuman_dengan_lampiran):
        """
        Test that the announcement list correctly includes the attachment URL.
        """
        url = reverse('api-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Find the specific announcement in the response
        announcement_data = next(
            (item for item in response.json() if item['id'] == pengumuman_dengan_lampiran.id),
            None
        )
        assert announcement_data is not None
        assert 'lampiran_url' in announcement_data
        assert announcement_data['lampiran_url'] is not None
        assert pengumuman_dengan_lampiran.lampiran.name in announcement_data['lampiran_url']

    def test_get_pengumuman_list_no_lampiran_url(self, api_client, pengumuman_tanpa_lampiran):
        """
        Test that the announcement list has a null lampiran_url for items without attachments.
        """
        url = reverse('api-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        announcement_data = next(
            (item for item in response.json() if item['id'] == pengumuman_tanpa_lampiran.id),
            None
        )
        assert announcement_data is not None
        assert 'lampiran_url' in announcement_data
        assert announcement_data['lampiran_url'] is None

    def test_get_pengumuman_detail_success(self, api_client, pengumuman_dengan_lampiran):
        """
        Test successfully retrieving the detail of a single announcement.
        """
        url = reverse('api-detail', kwargs={'pk': pengumuman_dengan_lampiran.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['id'] == pengumuman_dengan_lampiran.id
        assert response.json()['judul'] == pengumuman_dengan_lampiran.judul
        assert 'lampiran_url' in response.json()
        assert response.json()['lampiran_url'] is not None

    def test_get_pengumuman_detail_not_found(self, api_client):
        """
        Test that a 404 is returned for a non-existent announcement.
        """
        url = reverse('api-detail', kwargs={'pk': 999}) # Non-existent PK
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'error' in response.json()
