from tokenize import TokenError

from django.contrib import messages
from django.contrib.auth import authenticate, logout as django_logout
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from rest_framework import generics, status, views as drf_views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Count
from rest_framework import permissions as drf_permissions
from django.views import View
from django.shortcuts import render, redirect
from django.urls import reverse

from .models import Dosen
from .serializers import DosenListSerializer

from .models import Jurusan, ProgramStudi
from .serializers import (
    JurusanSerializer, ProgramStudiSerializer,
    RegisterMahasiswaSerializer, RegisterDosenSerializer, LoginSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)


# --- View untuk List Dosen ---
class DosenListView(generics.ListAPIView):
    serializer_class = DosenListSerializer
    # Hanya mahasiswa yang terautentikasi yang bisa melihat daftar dosen
    permission_classes = [drf_permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Dosen.objects.select_related('user', 'jurusan').all()
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


class LoginView(drf_views.APIView):
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
            return Response({"error": "Data yang diinputkan tidak ditemukan, Mohon periksa ulang data!"},
                            status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(drf_views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"detail": "Refresh token is required in the request body."},
                                status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()

            if hasattr(request, 'session'):
                django_logout(request)

            return Response({"detail": "Successfully logged out. The refresh token has been blacklisted."},
                            status=status.HTTP_200_OK)
        except TokenError:
            return Response({"detail": "Token is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": "An error occurred during logout."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- Password Reset Views (Template-based) ---
class PasswordResetRequestView(View):
    form_template_name = 'registration/password_reset_request_form.html'

    success_url_name = 'password_reset_done'

    serializer_class = PasswordResetRequestSerializer

    def get(self, request, *args, **kwargs):

        return render(request, self.form_template_name, {'form': self.serializer_class()})

    def post(self, request, *args, **kwargs):

        serializer = self.serializer_class(data=request.POST)

        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)

            # --- Generate Token and Reset URL ---
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = request.build_absolute_uri(
                reverse('password_reset_confirm_page', kwargs={'uidb64': uid, 'token': token})
            )

            # --- Prepare Email Content (Text and HTML) ---
            subject = "Password Reset Request - Digita Admin"
            text_content = f"""
Hello {user.get_full_name() or user.username},

You've requested to reset your password for your Digita Admin account.

Please click the link below or copy and paste it into your browser to reset your password:
{reset_url}

This link will expire in 24 hours for security reasons.

If you didn't request this password reset, you can safely ignore this email.

Best regards,
Digita Admin Team
            """
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Password Reset Request</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">Password Reset Request</h2>
        <p>Hello <strong>{user.get_full_name() or user.username}</strong>,</p>
        <p>You've requested to reset your password for your Digita Admin account.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" style="background-color: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                Reset Password
            </a>
        </div>
        <p>Or copy and paste this link in your browser:</p>
        <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 3px;">{reset_url}</p>
        <p><small>This link will expire in 24 hours for security reasons.</small></p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p><small>If you didn't request this password reset, you can safely ignore this email.</small></p>
        <p>Best regards,<br><strong>Digita Admin Team</strong></p>
    </div>
</body>
</html>
            """

            # --- Send the Email ---
            email_message = EmailMultiAlternatives(
                subject=subject, body=text_content, from_email=settings.DEFAULT_FROM_EMAIL, to=[email]
            )
            email_message.attach_alternative(html_content, "text/html")

            try:
                email_message.send(fail_silently=False)
            except Exception:
                messages.error(request, "We had an issue sending the email. Please try again later.")
                return render(request, self.form_template_name, {'form': serializer})

            # --- Final Success Action: Message and Redirect ---
            messages.success(request, 'If an account with that email exists, a reset link has been sent.')
            return redirect(self.success_url_name)

        else:
            messages.error(request, "Please check the form for errors.")
            return render(request, self.form_template_name, {'form': serializer})



class PasswordResetConfirmView(View):

    serializer_class = PasswordResetConfirmSerializer
    form_template_name = 'registration/password_reset_confirm_form.html'
    success_template_name = 'registration/password_reset_complete.html'
    invalid_token_template_name = 'registration/password_reset_invalid_token.html'

    success_url_name = 'password_reset_complete_page'

    def get(self, request, uidb64=None, token=None, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            context = {'uidb64': uidb64, 'token': token}
            return render(request, self.form_template_name, context)
        else:
            return render(request, self.invalid_token_template_name)

    def post(self, request, uidb64=None, token=None, *args, **kwargs):
        data = request.POST.copy()
        data['uid'] = uidb64
        data['token'] = token

        serializer = self.serializer_class(data=data)

        if serializer.is_valid():
            user = serializer.validated_data['user']
            new_password = serializer.validated_data['new_password']

            user.set_password(new_password)
            user.save()

            return redirect(self.success_url_name)
        else:

            is_token_error = any(
                key in serializer.errors for key in ['uid', 'token']
            ) or any(
                ("Invalid user ID" in msg or "Invalid or expired token" in msg)
                for field_errors in serializer.errors.values() for msg in field_errors
            )

            if is_token_error:
                return render(request, self.invalid_token_template_name, {'errors_dict': serializer.errors})

            context = {
                'uidb64': uidb64,
                'token': token,
                'errors_dict': serializer.errors
            }
            return render(request, self.form_template_name, context)