from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail
from unittest.mock import patch

from rest_framework.test import APITestCase
from rest_framework import status

from .models import Jurusan, ProgramStudi, Mahasiswa, Dosen
from .backends import NimNikAuthBackend

# Get the User model, which is standard Django practice
User = get_user_model()


class BaseUserTestCase(APITestCase):
    """
    A base test case that sets up common data needed for other tests.
    This runs once before each test method in inheriting classes.
    """
    def setUp(self):
        # Create common lookup data
        self.jurusan = Jurusan.objects.create(nama_jurusan='Teknik Informatika')
        self.prodi = ProgramStudi.objects.create(
            nama_prodi='Rekayasa Perangkat Lunak',
            jurusan=self.jurusan
        )

        # Common data for creating users
        self.mahasiswa_data = {
            'nim': '12345678',
            'email': 'mahasiswa.test@example.com',
            'nama_lengkap': 'Test Mahasiswa',
            'password': 'StrongPassword123',
            'password2': 'StrongPassword123',
            'program_studi_id': self.prodi.id
        }

        self.dosen_data = {
            'nik': '87654321',
            'email': 'dosen.test@example.com',
            'nama_lengkap': 'Test Dosen',
            'password': 'StrongPassword123',
            'password2': 'StrongPassword123',
            'jurusan_id': self.jurusan.id
        }


class ModelTests(BaseUserTestCase):
    """
    Tests for the models in the 'users' app.
    """
    def test_jurusan_creation(self):
        self.assertEqual(str(self.jurusan), 'Teknik Informatika')

    def test_program_studi_creation(self):
        self.assertEqual(str(self.prodi), 'Rekayasa Perangkat Lunak')
        self.assertEqual(self.prodi.jurusan, self.jurusan)

    def test_mahasiswa_creation(self):
        user = User.objects.create_user(
            username=self.mahasiswa_data['nim'],
            email=self.mahasiswa_data['email'],
            first_name=self.mahasiswa_data['nama_lengkap']
        )
        mahasiswa = Mahasiswa.objects.create(
            user=user,
            nim=self.mahasiswa_data['nim'],
            program_studi=self.prodi
        )
        self.assertEqual(str(mahasiswa), f"Test Mahasiswa ({self.mahasiswa_data['nim']})")
        self.assertEqual(mahasiswa.user.mahasiswa_profile, mahasiswa)

    def test_dosen_creation(self):
        user = User.objects.create_user(
            username=self.dosen_data['nik'],
            email=self.dosen_data['email'],
            first_name=self.dosen_data['nama_lengkap']
        )
        dosen = Dosen.objects.create(
            user=user,
            nik=self.dosen_data['nik'],
            jurusan=self.jurusan
        )
        self.assertEqual(str(dosen), f"Test Dosen ({self.dosen_data['nik']})")
        self.assertEqual(dosen.user.dosen_profile, dosen)


class AuthBackendTests(BaseUserTestCase):
    """
    Tests for the custom NimNikAuthBackend.
    """
    def setUp(self):
        super().setUp()
        self.backend = NimNikAuthBackend()

        # Create a Mahasiswa and a Dosen for authentication tests
        self.mahasiswa_user = User.objects.create_user(
            username=self.mahasiswa_data['nim'], password=self.mahasiswa_data['password'])
        Mahasiswa.objects.create(user=self.mahasiswa_user, nim=self.mahasiswa_data['nim'], program_studi=self.prodi)

        self.dosen_user = User.objects.create_user(
            username=self.dosen_data['nik'], password=self.dosen_data['password'])
        Dosen.objects.create(user=self.dosen_user, nik=self.dosen_data['nik'], jurusan=self.jurusan)

    def test_authenticate_mahasiswa_success(self):
        user = self.backend.authenticate(
            None,
            identifier=self.mahasiswa_data['nim'],
            password=self.mahasiswa_data['password'],
            role='mahasiswa'
        )
        self.assertEqual(user, self.mahasiswa_user)

    def test_authenticate_dosen_success(self):
        user = self.backend.authenticate(
            None,
            identifier=self.dosen_data['nik'],
            password=self.dosen_data['password'],
            role='dosen'
        )
        self.assertEqual(user, self.dosen_user)

    def test_authenticate_wrong_password(self):
        user = self.backend.authenticate(
            None,
            identifier=self.mahasiswa_data['nim'],
            password='wrongpassword',
            role='mahasiswa'
        )
        self.assertIsNone(user)

    def test_authenticate_wrong_role(self):
        # Try to authenticate a mahasiswa with the role 'dosen'
        user = self.backend.authenticate(
            None,
            identifier=self.mahasiswa_data['nim'],
            password=self.mahasiswa_data['password'],
            role='dosen'
        )
        self.assertIsNone(user)

    def test_authenticate_nonexistent_user(self):
        user = self.backend.authenticate(
            None,
            identifier='000000',
            password='anypassword',
            role='mahasiswa'
        )
        self.assertIsNone(user)

    def test_get_user(self):
        user = self.backend.get_user(self.mahasiswa_user.id)
        self.assertEqual(user, self.mahasiswa_user)

    def test_get_user_nonexistent(self):
        user = self.backend.get_user(9999)
        self.assertIsNone(user)


class UserAPITests(BaseUserTestCase):
    """
    Tests for the API endpoints (views and serializers).
    """
    # --- Registration Tests ---
    def test_register_mahasiswa_success(self):
        url = reverse('register-mahasiswa')
        response = self.client.post(url, self.mahasiswa_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username=self.mahasiswa_data['nim']).exists())
        self.assertTrue(Mahasiswa.objects.filter(nim=self.mahasiswa_data['nim']).exists())

    def test_register_dosen_success(self):
        url = reverse('register-dosen')
        response = self.client.post(url, self.dosen_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username=self.dosen_data['nik']).exists())
        self.assertTrue(Dosen.objects.filter(nik=self.dosen_data['nik']).exists())

    def test_register_password_mismatch(self):
        url = reverse('register-mahasiswa')
        data = self.mahasiswa_data.copy()
        data['password2'] = 'mismatched'
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_register_nim_already_exists(self):
        # Create user first
        self.client.post(reverse('register-mahasiswa'), self.mahasiswa_data, format='json')
        # Attempt to register again
        response = self.client.post(reverse('register-mahasiswa'), self.mahasiswa_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nim', response.data)

    # --- Login and Logout Tests ---
    def test_login_mahasiswa_success(self):
        self.client.post(reverse('register-mahasiswa'), self.mahasiswa_data, format='json')
        url = reverse('login')
        login_data = {
            'identifier': self.mahasiswa_data['nim'],
            'password': self.mahasiswa_data['password'],
            'role': 'mahasiswa'
        }
        response = self.client.post(url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertEqual(response.data['data']['role'], 'mahasiswa')

    def test_login_failure(self):
        self.client.post(reverse('register-mahasiswa'), self.mahasiswa_data, format='json')
        url = reverse('login')
        login_data = {
            'identifier': self.mahasiswa_data['nim'],
            'password': 'wrongpassword',
            'role': 'mahasiswa'
        }
        response = self.client.post(url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_success(self):
        # Register and Login to get tokens
        self.client.post(reverse('register-mahasiswa'), self.mahasiswa_data, format='json')
        login_response = self.client.post(reverse('login'), {
            'identifier': self.mahasiswa_data['nim'], 'password': self.mahasiswa_data['password'], 'role': 'mahasiswa'
        }, format='json')
        refresh_token = login_response.data['tokens']['refresh']
        access_token = login_response.data['tokens']['access']

        # Authenticate for logout
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Perform logout
        logout_url = reverse('user-logout')
        response = self.client.post(logout_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify token is blacklisted by trying to refresh it
        refresh_url = reverse('token_refresh')
        response = self.client.post(refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Data Endpoint Tests ---
    def test_jurusan_list_is_public(self):
        url = reverse('jurusan-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nama_jurusan'], self.jurusan.nama_jurusan)

    def test_program_studi_list_is_public_and_filterable(self):
        # Test without filter
        url = reverse('program-studi-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Test with filter
        url_with_filter = f"{url}?jurusan_id={self.jurusan.id}"
        response_filtered = self.client.get(url_with_filter)
        self.assertEqual(response_filtered.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_filtered.data), 1)

    def test_dosen_list_is_protected(self):
        # Create a Dosen to be listed
        self.client.post(reverse('register-dosen'), self.dosen_data, format='json')

        url = reverse('dosen-list')
        # Attempt access without authentication
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticate as Mahasiswa and try again
        self.client.post(reverse('register-mahasiswa'), self.mahasiswa_data, format='json')
        login_response = self.client.post(reverse('login'), {
            'identifier': self.mahasiswa_data['nim'], 'password': self.mahasiswa_data['password'], 'role': 'mahasiswa'
        }, format='json')
        access_token = login_response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response_authed = self.client.get(url)
        self.assertEqual(response_authed.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_authed.data), 1)
        self.assertEqual(response_authed.data[0]['nik'], self.dosen_data['nik'])


class PasswordResetTests(BaseUserTestCase):
    """
    Tests for the password reset flow.
    Note: These views are template-based, so we test form submission.
    """
    def setUp(self):
        super().setUp()
        # Create a user to reset password for
        self.user = User.objects.create_user(
            username='resetuser',
            email='reset@example.com',
            password='oldpassword'
        )

    @patch('users.views.EmailMultiAlternatives.send')
    def test_password_reset_request_sends_email(self, mock_send):
        url = reverse('password_reset_request_form')
        response = self.client.post(url, {'email': self.user.email})

        # Should redirect after successful submission
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        # Check that one email was sent
        self.assertEqual(len(mail.outbox), 0) # This should be 0 because we mocked .send()
        mock_send.assert_called_once() # Verify the mocked send method was called

    def test_password_reset_request_invalid_email(self):
        url = reverse('password_reset_request_form')
        response = self.client.post(url, {'email': 'nonexistent@example.com'})
        # The view should still "succeed" to prevent user enumeration,
        # but no email should be sent.
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(len(mail.outbox), 0)