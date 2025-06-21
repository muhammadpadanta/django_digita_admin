# users/api_views.py

from rest_framework import generics, viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView as DRFView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from django.contrib.auth import authenticate
from django.db.models import Count

from .models import Dosen, Jurusan, Mahasiswa, ProgramStudi, User
from .serializers import (
    DosenSerializer,
    JurusanSerializer,
    LoginSerializer,
    MahasiswaDetailSerializer,
    ProgramStudiSerializer,
    RegisterDosenSerializer,
    RegisterMahasiswaSerializer,
)

# --- Helper Functions ---

def get_tokens_for_user(user: User) -> dict:
    """
    Generates JWT refresh and access tokens for a given user.
    """
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

# --- API Views for Core Models ---

class JurusanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Jurusan to be viewed.
    - Provides `list` and `retrieve` actions.
    - Open to any user.
    """
    queryset = Jurusan.objects.all().order_by('nama_jurusan')
    serializer_class = JurusanSerializer
    permission_classes = [AllowAny]


class ProgramStudiViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Program Studi to be viewed.
    - Provides `list` and `retrieve` actions.
    - Can be filtered by `jurusan_id` query parameter.
    """
    serializer_class = ProgramStudiSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """
        Optionally filters the queryset by `jurusan_id` if provided
        in the query parameters.
        """
        queryset = ProgramStudi.objects.select_related('jurusan').order_by('nama_prodi')
        jurusan_id = self.request.query_params.get('jurusan_id')
        if jurusan_id:
            queryset = queryset.filter(jurusan_id=jurusan_id)
        return queryset

class DosenViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows lecturers (Dosen) to be viewed.
    - Provides `list` and `retrieve` actions automatically.
    - Optimized with `select_related` and annotates student count.
    - Requires authentication.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DosenSerializer

    def get_queryset(self):
        """
        Constructs the queryset by selecting related user and department data,
        annotating the student count, and ordering by name.
        """
        return Dosen.objects.select_related('user', 'jurusan').annotate(
            jumlah_mahasiswa_aktif=Count('mahasiswa_binaan')
        ).order_by('user__first_name', 'user__last_name')

class MahasiswaViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows students (Mahasiswa) to be viewed.
    - Provides `list` and `retrieve` actions.
    - Optimized with `select_related` to pre-fetch related user data.
    - Requires authentication.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MahasiswaDetailSerializer
    queryset = Mahasiswa.objects.select_related(
        'user',
        'program_studi',
        'dosen_pembimbing__user'
    ).all()


# --- API Views for Authentication ---

class RegisterMahasiswaView(generics.CreateAPIView):
    """
    API view for registering a new student (Mahasiswa).
    - Open to any user.
    - Returns a consistent success response structure.
    """
    serializer_class = RegisterMahasiswaSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"status": "success", "data": serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers
        )

class RegisterDosenView(generics.CreateAPIView):
    """
    API view for registering a new lecturer (Dosen).
    - Open to any user.
    - Returns a consistent success response structure.
    """
    serializer_class = RegisterDosenSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"status": "success", "data": serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers
        )

class LoginView(DRFView):
    """
    API view for user login.
    - Handles POST requests for authentication.
    - Returns user data and JWT tokens upon successful login.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer


    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data['identifier']
        password = serializer.validated_data['password']
        role = serializer.validated_data['role']

        user = authenticate(request, identifier=identifier, password=password, role=role)

        if user and user.is_active:
            tokens = get_tokens_for_user(user)
            user_data = {
                'id': user.id,
                'email': user.email,
                'nama_lengkap': user.get_full_name(),
                'role': role,
            }
            if role == 'mahasiswa' and hasattr(user, 'mahasiswa_profile'):
                user_data['nim'] = user.mahasiswa_profile.nim
            elif role == 'dosen' and hasattr(user, 'dosen_profile'):
                user_data['nik'] = user.dosen_profile.nik

            # Format respons sukses yang baru
            response_data = {
                "user": user_data,
                "tokens": tokens
            }
            return Response({
                "status": "success",
                "data": response_data
            }, status=status.HTTP_200_OK)

        if user and not user.is_active:
            # Format respons error yang baru
            return Response(
                {"status": "error", "message": "This account has been disabled."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Format respons error yang baru
        return Response(
            {"status": "error", "message": "The credentials provided could not be verified. Please check and try again."},
            status=status.HTTP_401_UNAUTHORIZED
        )

class LogoutView(DRFView):
    """
    API view for user logout.
    - Handles POST requests to blacklist the provided refresh token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"status": "error", "message": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"status": "success", "data": {"message": "Logout successful. Token has been blacklisted."}},
                status=status.HTTP_200_OK
            )
        except (TokenError, Exception):
            return Response(
                {"status": "error", "message": "Token is invalid or expired."},
                status=status.HTTP_400_BAD_REQUEST
            )