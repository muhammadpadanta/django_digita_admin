# users/tests.py
import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.core import mail

from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from .models import Jurusan, ProgramStudi, Dosen, Mahasiswa
from .forms import UserCreationAdminForm, UserEditForm
from .backends import NimNikAuthBackend
from tugas_akhir.models import TugasAkhir


pytestmark = pytest.mark.django_db

@pytest.fixture
def admin_user():
    """Fixture for creating a superuser."""
    return User.objects.create_superuser(
        'admin', 'admin@test.com', 'adminpassword'
    )

@pytest.fixture
def jurusan():
    """Fixture for a Jurusan instance."""
    return Jurusan.objects.create(nama_jurusan='Teknik Informatika')

@pytest.fixture
def prodi(jurusan):
    """Fixture for a ProgramStudi, depending on the 'jurusan' fixture."""
    return ProgramStudi.objects.create(nama_prodi='S1 Informatika', jurusan=jurusan)

@pytest.fixture
def dosen_user():
    """Fixture for the User object for a Dosen."""
    return User.objects.create_user(
        username='112233', email='dosen.test@test.com', password='password123',
        first_name='Budi', last_name='Darmawan'
    )

@pytest.fixture
def dosen(dosen_user, jurusan):
    """Fixture for a Dosen instance."""
    return Dosen.objects.create(user=dosen_user, nik='112233', jurusan=jurusan)

@pytest.fixture
def mahasiswa_user():
    """Fixture for the User object for a Mahasiswa."""
    return User.objects.create_user(
        username='998877', email='mahasiswa.test@test.com', password='password123',
        first_name='Cinta', last_name='Laura'
    )

@pytest.fixture
def mahasiswa(mahasiswa_user, prodi, dosen):
    """Fixture for a Mahasiswa instance."""
    return Mahasiswa.objects.create(
        user=mahasiswa_user, nim='998877', program_studi=prodi, dosen_pembimbing=dosen
    )

@pytest.fixture
def tugas_akhir(mahasiswa, dosen):
    """Fixture for a TugasAkhir instance to test view logic dependencies."""
    return TugasAkhir.objects.create(
        mahasiswa=mahasiswa,
        judul="Test Judul TA",
        dosen_pembimbing=dosen
    )


## --- Model Tests ---
# Testing basic creation, string representations, and database constraints.

def test_jurusan_str(jurusan):
    """Test the string representation of Jurusan model."""
    assert str(jurusan) == 'Teknik Informatika'

def test_dosen_str(dosen):
    """Test the string representation of Dosen model."""
    assert str(dosen) == 'Budi Darmawan (112233)'

def test_mahasiswa_creation(mahasiswa, prodi, dosen):
    """Test that Mahasiswa is created correctly."""
    assert mahasiswa.nim == '998877'
    assert mahasiswa.user.first_name == 'Cinta'
    assert mahasiswa.program_studi == prodi
    assert mahasiswa.dosen_pembimbing == dosen




## --- Form Tests ---
# Testing form validation, cleaning logic, and the save method.

def test_user_creation_form_valid_mahasiswa(prodi):
    """Test the user creation form with valid data for a Mahasiswa."""
    form_data = {
        'role': 'mahasiswa', 'nama_lengkap': 'Andi Budiman',
        'email': 'andi.b@test.com', 'password': 'password123',
        'password2': 'password123', 'nim': '123456',
        'program_studi_id': prodi.id
    }
    form = UserCreationAdminForm(data=form_data)
    assert form.is_valid(), form.errors
    user = form.save()
    assert user.username == '123456'
    assert hasattr(user, 'mahasiswa_profile')

def test_user_creation_form_valid_dosen(jurusan):
    """Test the user creation form with valid data for a Dosen."""
    form_data = {
        'role': 'dosen', 'nama_lengkap': 'Dewi Lestari',
        'email': 'dewi.l@test.com', 'password': 'password123',
        'password2': 'password123', 'nik': '654321',
        'jurusan_id': jurusan.id
    }
    form = UserCreationAdminForm(data=form_data)
    assert form.is_valid(), form.errors
    user = form.save()
    assert user.username == '654321'
    assert hasattr(user, 'dosen_profile')

def test_user_creation_form_password_mismatch(prodi):
    """Test that the form catches password mismatches."""
    form_data = {
        'role': 'mahasiswa', 'nama_lengkap': 'Andi Budiman',
        'email': 'andi.b@test.com', 'password': 'password123',
        'password2': 'password456', 'nim': '123456',
        'program_studi_id': prodi.id
    }
    form = UserCreationAdminForm(data=form_data)
    assert not form.is_valid()
    assert 'password2' in form.errors

def test_user_creation_form_missing_nim_for_mahasiswa(prodi):
    """Test validation error when NIM is missing for a Mahasiswa."""
    form_data = {
        'role': 'mahasiswa', 'nama_lengkap': 'Andi Budiman',
        'email': 'andi.b@test.com', 'password': 'password123',
        'password2': 'password123', 'nim': '', # Missing NIM
        'program_studi_id': prodi.id
    }
    form = UserCreationAdminForm(data=form_data)
    assert not form.is_valid()
    assert 'nim' in form.errors

def test_user_creation_form_existing_email(prodi, mahasiswa_user):
    """Test that the form raises a validation error for a duplicate email."""
    form_data = {
        'role': 'mahasiswa', 'nama_lengkap': 'Andi Budiman',
        'email': mahasiswa_user.email, # Existing email
        'password': 'password123', 'password2': 'password123',
        'nim': '123456', 'program_studi_id': prodi.id
    }
    form = UserCreationAdminForm(data=form_data)
    assert not form.is_valid()
    assert 'email' in form.errors

def test_user_edit_form_save(mahasiswa, prodi, dosen):
    """Test that the UserEditForm correctly saves updated data."""
    form_data = {
        'nama_lengkap': 'Cinta Laura Kiehl', 'email': 'new.email@test.com',
        'is_active': True, 'nim': mahasiswa.nim,
        'program_studi': prodi.id, 'dosen_pembimbing': dosen.user.id
    }
    # The form needs the user instance to be edited
    form = UserEditForm(instance=mahasiswa.user, data=form_data)
    assert form.is_valid(), form.errors

    updated_user = form.save()
    assert updated_user.email == 'new.email@test.com'
    assert updated_user.get_full_name() == 'Cinta Laura Kiehl'


## --- Auth Backend Tests ---
# Testing the custom authentication backend.

def test_authenticate_mahasiswa_success(mahasiswa_user, mahasiswa):
    """Test successful authentication for a Mahasiswa."""
    user = authenticate(identifier='998877', password='password123', role='mahasiswa')
    assert user is not None
    assert user == mahasiswa_user

def test_authenticate_dosen_success(dosen_user, dosen):
    """Test successful authentication for a Dosen."""
    user = authenticate(identifier='112233', password='password123', role='dosen')
    assert user is not None
    assert user == dosen_user

def test_authenticate_wrong_password(mahasiswa_user):
    """Test authentication failure with an incorrect password."""
    user = authenticate(identifier='998877', password='wrongpassword', role='mahasiswa')
    assert user is None

def test_authenticate_nonexistent_user():
    """Test authentication failure with a non-existent identifier."""
    user = authenticate(identifier='000000', password='password123', role='mahasiswa')
    assert user is None

def test_authenticate_invalid_role():
    """Test authentication failure with an invalid role."""
    user = authenticate(identifier='998877', password='password123', role='staff')
    assert user is None


## --- View Tests ---
# Testing that views render correctly, handle data, and manage permissions.

def test_user_management_view_get(admin_client):
    """Test that the user management page is accessible to an admin."""
    url = reverse('users:user_management_list')
    response = admin_client.get(url)
    assert response.status_code == 200
    assert 'core/user_management.html' in [t.name for t in response.templates]
    assert 'user_list' in response.context

def test_user_management_search_and_filter(admin_client, mahasiswa, dosen):
    """Test the search and role filters on the user management page."""
    base_url = reverse('users:user_management_list')

    # Test filter by role 'mahasiswa'
    response = admin_client.get(f"{base_url}?role=mahasiswa")
    assert response.status_code == 200
    user_list_pks = [user['id'] for user in response.context['user_list']]
    assert mahasiswa.user.pk in user_list_pks
    assert dosen.user.pk not in user_list_pks

    # Test search by name
    response = admin_client.get(f"{base_url}?q=Cinta")
    assert response.status_code == 200
    assert len(response.context['user_list']) == 1
    assert response.context['user_list'][0]['full_name'] == 'Cinta Laura'

def test_user_management_unauthenticated(client):
    """Test that unauthenticated users are redirected."""
    url = reverse('users:user_management_list')
    response = client.get(url)
    assert response.status_code == 302
    assert '/login/' in response.url

def test_user_create_view_post_success(admin_client, jurusan):
    """Test creating a user via the AJAX POST view successfully."""
    url = reverse('users:user_create')
    form_data = {
        'role': 'dosen', 'nama_lengkap': 'Siti Hartini',
        'email': 'siti.h@test.com', 'password': 'password123',
        'password2': 'password123', 'nik': '789012', 'jurusan_id': jurusan.id
    }
    response = admin_client.post(url, form_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    assert response.json()['status'] == 'success'
    assert User.objects.filter(username='789012').exists()

def test_user_create_view_post_fail(admin_client, jurusan):
    """Test creating a user via AJAX with invalid data."""
    url = reverse('users:user_create')
    form_data = {'role': 'dosen', 'nama_lengkap': 'Siti Hartini', 'nik': '789012'} # Missing fields
    response = admin_client.post(url, form_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 400
    response_json = response.json()
    assert response_json['status'] == 'error'
    assert 'email' in response_json['errors']
    assert 'password' in response_json['errors']

def test_user_edit_view_get_data(admin_client, mahasiswa):
    """Test the GET request to fetch user data for the edit modal."""
    url = reverse('users:user_edit', kwargs={'pk': mahasiswa.user.pk})
    response = admin_client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == mahasiswa.user.pk
    assert data['role'] == 'mahasiswa'
    assert data['nim'] == mahasiswa.nim

def test_user_edit_view_post_updates_ta_dospem(admin_client, mahasiswa, tugas_akhir):
    """Test that editing a Mahasiswa's advisor also updates the related TugasAkhir."""
    # Create a new Dosen to be the new advisor
    new_dosen_user = User.objects.create_user('newdosen', 'new@dosen.com', 'pw')
    new_dosen = Dosen.objects.create(user=new_dosen_user, nik='000111', jurusan=mahasiswa.program_studi.jurusan)

    url = reverse('users:user_edit', kwargs={'pk': mahasiswa.user.pk})
    form_data = {
        'nama_lengkap': mahasiswa.user.get_full_name(),
        'email': mahasiswa.user.email,
        'is_active': True,
        'nim': mahasiswa.nim,
        'program_studi': mahasiswa.program_studi.id,
        'dosen_pembimbing': new_dosen.user.id # Change the advisor
    }
    admin_client.post(url, form_data)
    tugas_akhir.refresh_from_db()
    assert tugas_akhir.dosen_pembimbing == new_dosen

def test_user_delete_view_success(admin_client):
    """Test deleting a user successfully."""
    user_to_delete = User.objects.create_user(username='deleteme', password='pw')
    url = reverse('users:user_delete', kwargs={'pk': user_to_delete.pk})
    response = admin_client.post(url)
    assert response.status_code == 302 # Redirects on success
    assert response.url == reverse('users:user_management_list')
    assert not User.objects.filter(pk=user_to_delete.pk).exists()

def test_user_cannot_delete_self(admin_client, admin_user):
    """Test that an admin cannot delete their own account."""
    url = reverse('users:user_delete', kwargs={'pk': admin_user.pk})
    admin_client.post(url)
    assert User.objects.filter(pk=admin_user.pk).exists()

def test_user_export_view(admin_client, mahasiswa):
    """Test that the user export view returns an Excel file."""
    url = reverse('users:user_export')
    response = admin_client.get(url)
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    assert 'attachment; filename="users_export.xlsx"' in response['Content-Disposition']


## --- Password Reset View Tests ---

def test_password_reset_request_view_get(client):
    """Test that the password reset request page loads."""
    url = reverse('users:password_reset_request_form')
    response = client.get(url)
    assert response.status_code == 200

def test_password_reset_request_sends_email(client, mahasiswa_user):
    """Test that a POST to the reset view sends an email."""
    url = reverse('users:password_reset_request_form')
    client.post(url, {'email': mahasiswa_user.email})
    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert email.to == [mahasiswa_user.email]
    assert "Password Reset Request" in email.subject

def test_password_reset_confirm_view_get_valid_token(client, mahasiswa_user):
    """Test the confirmation view with a valid token."""
    token = default_token_generator.make_token(mahasiswa_user)
    uid = urlsafe_base64_encode(force_bytes(mahasiswa_user.pk))
    url = reverse('users:password_reset_confirm_page', kwargs={'uidb64': uid, 'token': token})
    response = client.get(url)
    assert response.status_code == 200
    assert 'password_reset/password_reset_confirm_form.html' in [t.name for t in response.templates]

def test_password_reset_confirm_view_post_success(client, mahasiswa_user):
    """Test that posting a new password successfully resets it."""
    token = default_token_generator.make_token(mahasiswa_user)
    uid = urlsafe_base64_encode(force_bytes(mahasiswa_user.pk))
    url = reverse('users:password_reset_confirm_page', kwargs={'uidb64': uid, 'token': token})

    post_data = {'new_password': 'newpassword123', 'confirm_password': 'newpassword123'}
    response = client.post(url, post_data)

    assert response.status_code == 302 # Redirect on success
    assert response.url == reverse('users:password_reset_complete_page')

    # Check that the password has actually changed
    mahasiswa_user.refresh_from_db()
    assert mahasiswa_user.check_password('newpassword123')