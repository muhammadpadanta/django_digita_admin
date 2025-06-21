# users/urls.py
from django.urls import path
from . import views
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views

app_name = 'users'

# These are the URLs for admin web interface
urlpatterns = [
    path('', views.UserManagementView.as_view(), name='user_management_list'),
    path('<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    path('<int:pk>/edit/', views.UserEditView.as_view(), name='user_edit'),
    path('create/', views.UserCreateView.as_view(), name='user_create'),

    # Template-based Password reset URLs from views
    path('auth/password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset_request_form'),
    path('auth/password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_sent.html'),
         name='password_reset_done'),
    path('auth/reset/<str:uidb64>/<str:token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm_page'),
    path('auth/reset/complete/',
         TemplateView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete_page'),
]

