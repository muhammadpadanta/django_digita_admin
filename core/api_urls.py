# core/api_urls.py

from django.urls import path
from .api_views import RegisterFCMDeviceView

urlpatterns = [
    path('register-fcm-device/', RegisterFCMDeviceView.as_view(), name='core-api-register-fcm'),
]
