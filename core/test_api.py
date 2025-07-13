# core/test_api.py
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from .models import FCMDevice

pytestmark = pytest.mark.django_db


# --- Fixtures ---

@pytest.fixture
def api_client():
    """Fixture for a DRF API client."""
    return APIClient()

@pytest.fixture
def regular_user():
    """Fixture for a regular, authenticated user."""
    return User.objects.create_user(username='testuser', password='password123')


# --- API Test Classes ---

class TestFCMDeviceAPI:
    """
    Tests for the FCM Device Registration API endpoint.
    """

    def test_register_fcm_device_success_new(self, api_client, regular_user):
        """
        Test successfully registering a new FCM device token for a logged-in user.
        """
        api_client.force_authenticate(user=regular_user)
        url = reverse('core-api-register-fcm')
        data = {'fcm_token': 'new_device_token_string_1'}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'New device registered successfully.'
        assert FCMDevice.objects.filter(user=regular_user, fcm_token='new_device_token_string_1').exists()

    def test_register_fcm_device_success_existing_reassociate(self, api_client, regular_user):
        """
        Test that an existing token is correctly re-associated with the current user.
        """
        # Pre-create a device with a different user (or no user)
        old_user = User.objects.create_user(username='olduser', password='password')
        FCMDevice.objects.create(user=old_user, fcm_token='existing_token_string_2')

        api_client.force_authenticate(user=regular_user)
        url = reverse('core-api-register-fcm')
        data = {'fcm_token': 'existing_token_string_2'}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'Existing device re-associated with user.'
        
        # Verify the token is now associated with the new user
        device = FCMDevice.objects.get(fcm_token='existing_token_string_2')
        assert device.user == regular_user

    def test_register_fcm_device_fail_no_token(self, api_client, regular_user):
        """
        Test that the endpoint returns a 400 Bad Request if no token is provided.
        """
        api_client.force_authenticate(user=regular_user)
        url = reverse('core-api-register-fcm')
        data = {'fcm_token': ''} # Empty token
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_register_fcm_device_fail_unauthenticated(self, api_client):
        """
        Test that an unauthenticated user cannot access the endpoint.
        """
        url = reverse('core-api-register-fcm')
        data = {'fcm_token': 'some_token'}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
