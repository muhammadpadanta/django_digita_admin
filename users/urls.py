from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

urlpatterns = [
    path('jurusan/', views.JurusanListView.as_view(), name='jurusan-list'),
    path('program-studi/', views.ProgramStudiListView.as_view(), name='program-studi-list'),
    path('register/mahasiswa/', views.RegisterMahasiswaView.as_view(), name='register-mahasiswa'),
    path('register/dosen/', views.RegisterDosenView.as_view(), name='register-dosen'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='user-logout'),
    path('dosen/', views.DosenListView.as_view(), name='dosen-list'),


    # Template-based Password reset URLs
    path('auth/password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset_request_form'),
    path('auth/reset/<str:uidb64>/<str:token>/', views.PasswordResetConfirmView.as_view(),
         name='password_reset_confirm_page'),
    path('auth/password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_sent.html'
         ),
         name='password_reset_done'),
    path('auth/reset/complete/',
         TemplateView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete_page'),

    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]
