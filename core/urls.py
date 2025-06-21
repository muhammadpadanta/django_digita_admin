# core/urls.py
from django.urls import path, include
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('documents/', views.DocumentsView.as_view(), name='documents'),
    path('announcements/', views.AnnouncementsView.as_view(), name='announcements'),
]