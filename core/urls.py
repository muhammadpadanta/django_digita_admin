# core/urls.py
from django.urls import path, include
from . import views
from .views import DashboardView

app_name = 'core'

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('', views.HomeView.as_view(), name='home'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
]

# Include other app URLs for a modular structure
urlpatterns += [
    path('users/', include('users.urls', namespace='users')),
    path('announcements/', include('announcements.urls', namespace='announcements')),
]