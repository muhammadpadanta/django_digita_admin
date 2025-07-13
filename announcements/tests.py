# announcements/tests.py
import pytest
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Pengumuman
from .forms import PengumumanForm
from django.contrib.auth.models import User


# Mark all tests in this module as needing database access
pytestmark = pytest.mark.django_db


# --- Fixtures ---

@pytest.fixture
def user():
    """Fixture for a regular user."""
    return User.objects.create_user(username='testuser', password='password123')

@pytest.fixture
def pengumuman_data():
    """Fixture for Pengumuman data."""
    return {
        'judul': 'Judul Pengumuman Test',
        'deskripsi': 'Deskripsi untuk pengumuman test.',
        'tanggal_mulai': timezone.now().date(),
        'tanggal_selesai': (timezone.now() + timezone.timedelta(days=10)).date(),
    }

@pytest.fixture
def dummy_file():
    """Fixture for a simple dummy file."""
    return SimpleUploadedFile(
        "lampiran_test.txt",
        b"Ini adalah konten file lampiran.",
        content_type="text/plain"
    )


# --- Model Tests ---

class TestPengumumanModel:
    """
    Tests for the Pengumuman model.
    """

    def test_pengumuman_creation_tanpa_lampiran(self, pengumuman_data):
        """
        Test creating a Pengumuman instance without an attachment.
        """
        pengumuman = Pengumuman.objects.create(**pengumuman_data)
        assert pengumuman.judul == pengumuman_data['judul']
        assert str(pengumuman) == pengumuman_data['judul']
        assert pengumuman.lampiran_hash == ''

    def test_pengumuman_creation_dengan_lampiran(self, pengumuman_data, dummy_file, user):
        """
        Test creating a Pengumuman instance with an attachment and hash generation.
        """
        form = PengumumanForm(data=pengumuman_data, files={'lampiran': dummy_file}, user=user)
        assert form.is_valid()
        pengumuman = form.save()

        assert pengumuman.lampiran is not None
        assert 'lampiran_test' in pengumuman.lampiran.name
        assert pengumuman.lampiran_hash != ''
        # Check if the hash is a valid SHA256 hash (64 hex characters)
        assert len(pengumuman.lampiran_hash) == 64

    def test_pengumuman_str_representation(self, pengumuman_data):
        """
        Test the string representation of the Pengumuman model.
        """
        pengumuman = Pengumuman.objects.create(**pengumuman_data)
        assert str(pengumuman) == 'Judul Pengumuman Test'

    def test_pengumuman_ordering(self):
        """
        Test that announcements are ordered by tanggal_mulai in descending order.
        """
        today = timezone.now().date()
        Pengumuman.objects.create(
            judul="Pengumuman Lama",
            deskripsi="...",
            tanggal_mulai=today - timezone.timedelta(days=5),
            tanggal_selesai=today
        )
        Pengumuman.objects.create(
            judul="Pengumuman Baru",
            deskripsi="...",
            tanggal_mulai=today,
            tanggal_selesai=today + timezone.timedelta(days=5)
        )
        announcements = list(Pengumuman.objects.all())
        assert announcements[0].judul == "Pengumuman Baru"
        assert announcements[1].judul == "Pengumuman Lama"


# --- Form Tests ---

class TestPengumumanForm:
    """
    Tests for the PengumumanForm.
    """

    def test_pengumuman_form_valid_tanpa_lampiran(self, pengumuman_data):
        """
        Test that the PengumumanForm is valid with core data and no attachment.
        """
        form = PengumumanForm(data=pengumuman_data)
        assert form.is_valid(), form.errors

    def test_pengumuman_form_valid_dengan_lampiran(self, pengumuman_data, dummy_file, user):
        """
        Test that the PengumumanForm is valid with an attachment.
        """
        # When testing forms with files, the files dict must be passed separately.
        form = PengumumanForm(data=pengumuman_data, files={'lampiran': dummy_file}, user=user)
        assert form.is_valid(), form.errors
        instance = form.save()
        assert instance.lampiran is not None
        assert instance.lampiran_hash != ''

    def test_pengumuman_form_invalid_missing_data(self):
        """
        Test that the form is invalid if required fields are missing.
        """
        form = PengumumanForm(data={})
        assert not form.is_valid()
        assert 'judul' in form.errors
        assert 'deskripsi' in form.errors
        assert 'tanggal_mulai' in form.errors
        assert 'tanggal_selesai' in form.errors

    def test_pengumuman_form_tanggal_selesai_before_mulai(self, pengumuman_data):
        """
        Test that the form's clean method raises a validation error if
        tanggal_selesai is before tanggal_mulai.
        """
        pengumuman_data['tanggal_selesai'] = pengumuman_data['tanggal_mulai'] - timezone.timedelta(days=1)
        form = PengumumanForm(data=pengumuman_data)
        assert not form.is_valid()
        assert 'tanggal_selesai' in form.errors
        assert "Tanggal selesai tidak boleh sebelum tanggal mulai." in form.errors['tanggal_selesai']

# --- View Tests ---

from django.urls import reverse
from unittest.mock import patch

class TestAnnouncementViews:
    """
    Tests for the views in the announcements app.
    """

    @patch('announcements.views.send_notification_to_all_users')
    def test_announcement_creation_sends_notification(self, mock_send_notification, client, user, pengumuman_data):
        """
        Test that creating an announcement triggers a notification.
        """
        client.login(username='testuser', password='password123')
        url = reverse('announcements:create')
        response = client.post(url, pengumuman_data)

        assert response.status_code == 200
        assert response.json()['status'] == 'success'
        
        # Check that the notification function was called
        mock_send_notification.assert_called_once()
        
        # Check the arguments passed to the notification function
        announcement = Pengumuman.objects.latest('created_at')
        expected_data = {
            'announcement_id': str(announcement.id),
            'click_action': 'FLUTTER_NOTIFICATION_CLICK',
            'screen': 'announcement_detail',
        }
        mock_send_notification.assert_called_with(
            title=pengumuman_data['judul'],
            body=pengumuman_data['deskripsi'],
            data=expected_data
        )