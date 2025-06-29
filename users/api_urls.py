# users/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()

router.register(r'mahasiswa', api_views.MahasiswaViewSet, basename='mahasiswa')
router.register(r'dosen', api_views.DosenViewSet, basename='dosen')
router.register(r'jurusan', api_views.JurusanViewSet, basename='jurusan')
router.register(r'program-studi', api_views.ProgramStudiViewSet, basename='program-studi')

urlpatterns = [
    # API endpoints from api_views
    path('profil/mahasiswa/', api_views.MahasiswaProfileView.as_view(), name='profil-mahasiswa'),
    path('profil/dosen/', api_views.DosenProfileView.as_view(), name='profil-dosen'),
    path('mahasiswa/register/', api_views.RegisterMahasiswaView.as_view(), name='register-mahasiswa'),
    path('dosen/register/', api_views.RegisterDosenView.as_view(), name='register-dosen'),
    path('login/', api_views.LoginView.as_view(), name='login'),
    path('logout/', api_views.LogoutView.as_view(), name='user-logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]

urlpatterns += router.urls