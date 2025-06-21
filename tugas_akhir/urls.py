from django.urls import path
from . import views

urlpatterns = [
    # Handles listing all relevant requests (GET) and creating a new one (POST)
    path('supervision-requests/', views.SupervisionRequestListCreateView.as_view(), name='supervision-request-list-create'),

    # Handles retrieving details (GET) and responding/updating (PATCH)
    path('supervision-requests/<int:pk>/', views.SupervisionRequestDetailUpdateView.as_view(), name='supervision-request-detail-update'),
]