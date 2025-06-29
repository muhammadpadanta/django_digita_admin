# announcements/api_urls.py

from django.urls import path
from . import api_views

# These patterns are prefixed with 'api/' in the main urls.py
urlpatterns = [
    path('all/', api_views.PengumumanAPIListView.as_view(), name='api-list'),
    path('<int:pk>/', api_views.PengumumanAPIDetailView.as_view(), name='api-detail'),
]
