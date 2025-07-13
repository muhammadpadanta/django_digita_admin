# core/tests.py
import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from .models import ActivityLog, FCMDevice
from users.models import Mahasiswa, Dosen, Jurusan, ProgramStudi
from announcements.models import Pengumuman
from tugas_akhir.models import Dokumen, TugasAkhir

pytestmark = pytest.mark.django_db


# --- Fixtures ---

@pytest.fixture
def staff_user():
    """Fixture for a staff user."""
    return User.objects.create_user(
        username='staffuser',
        password='password123',
        is_staff=True
    )

@pytest.fixture
def regular_user():
    """Fixture for a non-staff user."""
    return User.objects.create_user(
        username='regularuser',
        password='password123',
        is_staff=False
    )

@pytest.fixture
def another_user():
    """Fixture for another regular user."""
    return User.objects.create_user(
        username='anotheruser',
        password='password123'
    )

@pytest.fixture
def jurusan():
    return Jurusan.objects.create(nama_jurusan='Teknik Sipil')

@pytest.fixture
def prodi(jurusan):
    return ProgramStudi.objects.create(nama_prodi='D4 Perancangan Jalan dan Jembatan', jurusan=jurusan)

@pytest.fixture
def mahasiswa(regular_user, prodi):
    return Mahasiswa.objects.create(user=regular_user, nim='12345', program_studi=prodi)

@pytest.fixture
def dosen(staff_user, jurusan):
    return Dosen.objects.create(user=staff_user, nik='54321', jurusan=jurusan)

@pytest.fixture
def tugas_akhir(mahasiswa, dosen):
    return TugasAkhir.objects.create(mahasiswa=mahasiswa, dosen_pembimbing=dosen, judul="Analisis Struktur Baja")

@pytest.fixture
def document(mahasiswa, tugas_akhir):
    return Dokumen.objects.create(pemilik=mahasiswa, tugas_akhir=tugas_akhir, bab='BAB_I', nama_dokumen='Pendahuluan')

@pytest.fixture
def announcement():
    from django.utils import timezone
    now = timezone.now()
    return Pengumuman.objects.create(
        judul="Info Penting",
        deskripsi="Ini adalah info penting.",
        tanggal_mulai=now,
        tanggal_selesai=now + timezone.timedelta(days=7)
    )


# --- Model Tests ---

class TestCoreModels:
    """
    Tests for the models in the core app.
    """

    def test_activity_log_creation(self, staff_user, document):
        """
        Test creating an ActivityLog instance.
        """
        log = ActivityLog.objects.create(
            actor=staff_user,
            verb='approved',
            target=document,
            description='Document was approved by staff.'
        )
        assert log.actor == staff_user
        assert str(log) == f"{staff_user.username} approved {document}"

    def test_fcm_device_creation(self, regular_user):
        """
        Test creating an FCMDevice instance.
        """
        device = FCMDevice.objects.create(user=regular_user, fcm_token='some_unique_fcm_token_123')
        assert device.user == regular_user
        assert device.fcm_token == 'some_unique_fcm_token_123'
        assert str(device) == f"Device for {regular_user.username}"

    def test_fcm_device_token_uniqueness(self, regular_user, another_user):
        """
        Test the unique constraint on the fcm_token field.
        """
        FCMDevice.objects.create(user=regular_user, fcm_token='a_very_unique_token')
        with pytest.raises(IntegrityError):
            FCMDevice.objects.create(user=another_user, fcm_token='a_very_unique_token')


# --- View Tests ---

class TestCoreViews:
    """
    Tests for the views in the core app.
    """

    def test_login_view_get_unauthenticated(self, client):
        """
        Test that an unauthenticated user can access the login page.
        """
        url = reverse('core:login')
        response = client.get(url)
        assert response.status_code == 200
        assert 'core/login.html' in [t.name for t in response.templates]

    def test_login_view_redirects_if_authenticated(self, client, staff_user):
        """
        Test that a logged-in user is redirected from the login page to the dashboard.
        """
        client.login(username='staffuser', password='password123')
        url = reverse('core:login')
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == reverse('core:dashboard')

    def test_login_success_for_staff(self, client, staff_user):
        """
        Test successful login for a user with staff privileges.
        """
        url = reverse('core:login')
        response = client.post(url, {'username': 'staffuser', 'password': 'password123'}, follow=True)
        assert response.status_code == 200
        assert response.redirect_chain[0][0] == reverse('core:dashboard')
        assert '_auth_user_id' in client.session # Check if user is logged in

    def test_login_fail_for_non_staff(self, client, regular_user):
        """
        Test that a non-staff user cannot log in to the admin panel.
        """
        url = reverse('core:login')
        response = client.post(url, {'username': 'regularuser', 'password': 'password123'})
        assert response.status_code == 200
        assert "Akun ini tidak memiliki hak akses admin." in response.content.decode()
        assert '_auth_user_id' not in client.session

    def test_login_fail_wrong_password(self, client, staff_user):
        """
        Test login failure with an incorrect password.
        """
        url = reverse('core:login')
        response = client.post(url, {'username': 'staffuser', 'password': 'wrongpassword'})
        assert response.status_code == 200
        assert "Username atau password salah." in response.content.decode()
        assert '_auth_user_id' not in client.session

    def test_logout_view(self, client, staff_user):
        """
        Test that the logout view successfully logs out the user.
        """
        client.login(username='staffuser', password='password123')
        assert '_auth_user_id' in client.session
        url = reverse('core:logout')
        response = client.post(url, follow=True)
        assert response.status_code == 200
        assert '_auth_user_id' not in client.session
        assert response.redirect_chain[0][0] == reverse('core:home')

    def test_dashboard_view_authenticated(self, client, staff_user, mahasiswa, dosen, document, announcement):
        """
        Test that an authenticated staff user can access the dashboard and it has the correct context.
        """
        client.login(username='staffuser', password='password123')
        url = reverse('core:dashboard')
        response = client.get(url)
        assert response.status_code == 200
        assert 'core/dashboard.html' in [t.name for t in response.templates]
        assert response.context['total_mahasiswa'] == 1
        assert response.context['total_dosen'] == 1
        assert response.context['total_dokumen'] == 1
        assert list(response.context['recent_announcements']) == [announcement]

    def test_dashboard_view_unauthenticated(self, client):
        """
        Test that an unauthenticated user is redirected from the dashboard.
        """
        url = reverse('core:dashboard')
        response = client.get(url)
        assert response.status_code == 302
        assert reverse('core:login') in response.url

    def test_document_management_view_authenticated(self, client, staff_user, document):
        """
        Test that an authenticated staff user can access the document management page.
        """
        client.login(username='staffuser', password='password123')
        url = reverse('tugas_akhir:document-list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'core/documents.html' in [t.name for t in response.templates]
        assert list(response.context['documents']) == [document]

    def test_document_management_view_unauthenticated(self, client):
        """
        Test that an unauthenticated user is redirected from the document management page.
        """
        url = reverse('tugas_akhir:document-list')
        response = client.get(url)
        assert response.status_code == 302
        assert reverse('core:login') in response.url
