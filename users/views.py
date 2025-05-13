from tokenize import TokenError
from django.contrib.auth import authenticate, logout as django_logout
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Count, Q
from rest_framework import permissions
from .models import Dosen
from .serializers import DosenListSerializer

from .models import Jurusan, ProgramStudi
from .serializers import (
    JurusanSerializer, ProgramStudiSerializer,
    RegisterMahasiswaSerializer, RegisterDosenSerializer, LoginSerializer
)

# --- View untuk List Dosen ---
class DosenListView(generics.ListAPIView):
    """
    Endpoint untuk menampilkan daftar semua Dosen
    beserta jumlah mahasiswa aktif yang dibimbing.
    GET /api/users/dosen/
    """
    serializer_class = DosenListSerializer
    # Hanya mahasiswa yang terautentikasi yang bisa melihat daftar dosen
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Mengambil data Dosen dan menambahkan anotasi jumlah mahasiswa.
        """
        queryset = Dosen.objects.select_related('user', 'jurusan').all()

        # Menambahkan anotasi (hitung) jumlah mahasiswa bimbingan
        # 'mahasiswa_bimbingan' adalah related_name dari ForeignKey
        # di model TugasAkhir yang menunjuk ke Dosen.
        # Kita hanya menghitung TugasAkhir di mana dosen_pembimbing tidak NULL
        # (yang mana otomatis terjadi saat menghitung reverse relation ini).
        queryset = queryset.annotate(
            jumlah_mahasiswa_aktif=Count('mahasiswa_bimbingan')
        )

        # Urutkan berdasarkan nama lengkap user
        queryset = queryset.order_by('user__first_name', 'user__last_name')

        return queryset

# --- Views untuk Dropdowns ---
class JurusanListView(generics.ListAPIView):
    queryset = Jurusan.objects.all()
    serializer_class = JurusanSerializer
    permission_classes = [AllowAny]

class ProgramStudiListView(generics.ListAPIView):
    serializer_class = ProgramStudiSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """ Optionally filter by jurusan_id query parameter """
        queryset = ProgramStudi.objects.all()
        jurusan_id = self.request.query_params.get('jurusan_id')
        if jurusan_id is not None:
            queryset = queryset.filter(jurusan_id=jurusan_id)
        return queryset

# --- Registration Views ---
class RegisterMahasiswaView(generics.CreateAPIView):
    serializer_class = RegisterMahasiswaSerializer
    permission_classes = [AllowAny]

class RegisterDosenView(generics.CreateAPIView):
    serializer_class = RegisterDosenSerializer
    permission_classes = [AllowAny]

# --- Login View ---
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class LoginView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data.get('identifier')
        password = serializer.validated_data.get('password')
        role = serializer.validated_data.get('role')

        # custom backend
        user = authenticate(request, identifier=identifier, password=password, role=role)

        if user is not None:
            if user.is_active:
                tokens = get_tokens_for_user(user)
                # bisa tambahkan data lain yang diperlukan
                user_data = {
                    'id': user.id,
                    'email': user.email,
                    'nama_lengkap': user.get_full_name(),
                    'role': role,

                }
                if role == 'mahasiswa':
                     user_data['nim'] = user.mahasiswa_profile.nim
                elif role == 'dosen':
                     user_data['nik'] = user.dosen_profile.nik

                return Response({
                    "message": "Login Successful",
                    "data": user_data,
                    "tokens": tokens
                 }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Account disabled."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "Data yang diinputkan tidak ditemukan, Mohon periksa ulang data!"}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"detail": "Refresh token is required in the request body."}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()

            if hasattr(request, 'session'):
                django_logout(request)

            return Response({"detail": "Successfully logged out. The refresh token has been blacklisted."}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({"detail": "Token is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": "An error occurred during logout."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
