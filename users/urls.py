from django.urls import path
from . import views
from rest_framework_simplejwt.views import ( # Import JWT views
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('jurusan/', views.JurusanListView.as_view(), name='jurusan-list'),
    path('program-studi/', views.ProgramStudiListView.as_view(), name='program-studi-list'),
    path('register/mahasiswa/', views.RegisterMahasiswaView.as_view(), name='register-mahasiswa'),
    path('register/dosen/', views.RegisterDosenView.as_view(), name='register-dosen'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='user-logout'),
    path('dosen/', views.DosenListView.as_view(), name='dosen-list'),

    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]
