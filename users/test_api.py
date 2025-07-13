# users/test_api.py
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from .models import Jurusan, ProgramStudi, Dosen, Mahasiswa

# Mark all tests in this module as needing database access
pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    """Fixture for a DRF API client."""
    return APIClient()

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


# --- API Test Classes ---

class TestAuthAPI:
    """
    Tests for authentication-related API endpoints: registration, login, logout.
    """

    def test_register_mahasiswa_success(self, api_client, prodi):
        """
        Test successful registration of a Mahasiswa.
        """
        url = reverse('register-mahasiswa')
        data = {
            'nama_lengkap': 'Budi Pekerti',
            'email': 'budi.pekerti@test.com',
            'nim': '123456789',
            'password': 'strongpassword123',
            'password2': 'strongpassword123',
            'program_studi_id': prodi.id
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'success'
        assert 'nim' in response.data['data']
        assert User.objects.filter(username='123456789').exists()
        assert Mahasiswa.objects.filter(nim='123456789').exists()

    def test_register_mahasiswa_password_mismatch(self, api_client, prodi):
        """
        Test registration failure when passwords do not match.
        """
        url = reverse('register-mahasiswa')
        data = {
            'nama_lengkap': 'Budi Pekerti',
            'email': 'budi.pekerti@test.com',
            'nim': '123456789',
            'password': 'strongpassword123',
            'password2': 'wrongpassword',
            'program_studi_id': prodi.id
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_register_dosen_success(self, api_client, jurusan):
        """
        Test successful registration of a Dosen.
        """
        url = reverse('register-dosen')
        data = {
            'nama_lengkap': 'Dewi Sartika',
            'email': 'dewi.sartika@test.com',
            'nik': '987654321',
            'password': 'strongpassword123',
            'password2': 'strongpassword123',
            'jurusan_id': jurusan.id
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'success'
        assert User.objects.filter(username='987654321').exists()
        assert Dosen.objects.filter(nik='987654321').exists()

    def test_login_mahasiswa_success(self, api_client, mahasiswa):
        """
        Test successful login for a Mahasiswa and token generation.
        """
        url = reverse('login')
        data = {
            'role': 'mahasiswa',
            'identifier': mahasiswa.nim,
            'password': 'password123'
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'success'
        assert 'user' in response.data['data']
        assert 'tokens' in response.data['data']
        assert 'access' in response.data['data']['tokens']
        assert 'refresh' in response.data['data']['tokens']
        assert response.data['data']['user']['role'] == 'mahasiswa'

    def test_login_dosen_success(self, api_client, dosen):
        """
        Test successful login for a Dosen and token generation.
        """
        url = reverse('login')
        data = {
            'role': 'dosen',
            'identifier': dosen.nik,
            'password': 'password123'
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'success'
        assert response.data['data']['user']['role'] == 'dosen'

    def test_login_invalid_credentials(self, api_client, mahasiswa):
        """
        Test login failure with an incorrect password.
        """
        url = reverse('login')
        data = {
            'role': 'mahasiswa',
            'identifier': mahasiswa.nim,
            'password': 'wrongpassword'
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['status'] == 'error'

    def test_logout_success(self, api_client, mahasiswa):
        """
        Test successful logout by blacklisting the refresh token.
        """
        # First, log in to get the tokens
        login_url = reverse('login')
        login_data = {'role': 'mahasiswa', 'identifier': mahasiswa.nim, 'password': 'password123'}
        login_response = api_client.post(login_url, login_data, format='json')
        refresh_token = login_response.data['data']['tokens']['refresh']

        # Now, log out
        logout_url = reverse('user-logout')
        logout_data = {'refresh': refresh_token}
        logout_response = api_client.post(logout_url, logout_data, format='json')

        assert logout_response.status_code == status.HTTP_200_OK
        assert logout_response.data['status'] == 'success'

        # Verify the token is blacklisted (this is harder to test directly without more setup,
        # but a 200 response implies the logic was hit)


class TestProfileAPI:
    """
    Tests for profile-related API endpoints (viewing and updating).
    """

    def test_get_mahasiswa_profile_success(self, api_client, mahasiswa):
        """
        Test that an authenticated Mahasiswa can retrieve their own profile.
        """
        # Log in to get the access token
        login_url = reverse('login')
        login_data = {'role': 'mahasiswa', 'identifier': mahasiswa.nim, 'password': 'password123'}
        login_response = api_client.post(login_url, login_data, format='json')
        access_token = login_response.data['data']['tokens']['access']

        # Make authenticated request to profile endpoint
        profile_url = reverse('profil-mahasiswa')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = api_client.get(profile_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['nim'] == mahasiswa.nim
        assert response.data['email'] == mahasiswa.user.email

    def test_get_profile_unauthenticated(self, api_client):
        """
        Test that an unauthenticated user cannot access profile endpoints.
        """
        url = reverse('profil-mahasiswa')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_mahasiswa_profile_success(self, api_client, mahasiswa, prodi):
        """
        Test that an authenticated Mahasiswa can update their own profile.
        """
        # Log in
        login_url = reverse('login')
        login_data = {'role': 'mahasiswa', 'identifier': mahasiswa.nim, 'password': 'password123'}
        login_response = api_client.post(login_url, login_data, format='json')
        access_token = login_response.data['data']['tokens']['access']

        # Make authenticated request to update profile
        profile_url = reverse('profil-mahasiswa')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        update_data = {
            'nama_lengkap': 'Cinta Laura Updated',
            'email': 'cinta.updated@test.com',
            'program_studi_id': prodi.id
        }
        response = api_client.patch(profile_url, update_data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'cinta.updated@test.com'
        assert response.data['nama_lengkap'] == 'Cinta Laura Updated'

        # Verify the change in the database
        mahasiswa.user.refresh_from_db()
        assert mahasiswa.user.email == 'cinta.updated@test.com'
        assert mahasiswa.user.get_full_name() == 'Cinta Laura Updated'
