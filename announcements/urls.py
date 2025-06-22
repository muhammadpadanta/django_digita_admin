# announcements/urls.py

from django.urls import path
from . import views

app_name = 'announcements'

urlpatterns = [
    # The main page that lists all announcements
    path('', views.AnnouncementListView.as_view(), name='list'),

    # URL for the AJAX create functionality
    path('create/', views.AnnouncementCreateView.as_view(), name='create'),

    # URLs for the AJAX update functionality (GET to fetch, POST to save)
    path('<int:pk>/update/', views.AnnouncementUpdateView.as_view(), name='update'),

    # URL for deleting an announcement
    path('<int:pk>/delete/', views.AnnouncementDeleteView.as_view(), name='delete'),
]