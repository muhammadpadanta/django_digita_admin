from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import RequestDosen, TugasAkhir, Mahasiswa, Dosen
from .serializers import (
    RequestDosenCreateSerializer, RequestDosenListSerializer,
    RequestDosenRespondSerializer
)
from .permissions import IsMahasiswa, IsDosen, IsRequestRecipientOrAdmin, IsMahasiswaOrDosen, IsOwnerOrRecipient

class SupervisionRequestListCreateView(generics.ListCreateAPIView):
    """
    - GET: Lists requests.
      - For Mahasiswa: lists their own sent requests.
      - For Dosen: lists their incoming PENDING requests.
    - POST: Creates a new supervision request (for Mahasiswa only).
    """
    permission_classes = [permissions.IsAuthenticated, IsMahasiswaOrDosen]

    def get_queryset(self):
        """Dynamically filters the queryset based on the user's role."""
        user = self.request.user
        if hasattr(user, 'mahasiswa_profile'):
            # Mahasiswa sees all their requests, ordered by most recent
            return RequestDosen.objects.filter(mahasiswa=user.mahasiswa_profile).select_related('mahasiswa__user', 'dosen__user')
        if hasattr(user, 'dosen_profile'):
            # Dosen only sees PENDING requests addressed to them
            return RequestDosen.objects.filter(dosen=user.dosen_profile, status='PENDING').select_related('mahasiswa__user', 'dosen__user')
        return RequestDosen.objects.none()

    def get_serializer_class(self):
        """Returns the appropriate serializer for the action."""
        if self.request.method == 'POST':
            return RequestDosenCreateSerializer
        return RequestDosenListSerializer

    def perform_create(self, serializer):
        """Handles the logic for creating a new request."""
        mahasiswa_profile = self.request.user.mahasiswa_profile
        if TugasAkhir.objects.filter(mahasiswa=mahasiswa_profile).exists():
            raise ValidationError("Anda sudah terdaftar dalam proses Tugas Akhir.")
        if RequestDosen.objects.filter(mahasiswa=mahasiswa_profile, status='PENDING').exists():
            raise ValidationError("Anda sudah memiliki permintaan pembimbing yang PENDING.")
        requested_dosen = serializer.validated_data['dosen']
        if hasattr(requested_dosen.user, 'mahasiswa_profile') and requested_dosen.user.mahasiswa_profile == mahasiswa_profile:
            raise ValidationError("Tidak bisa mengajukan diri sendiri sebagai pembimbing.")
        serializer.save(mahasiswa=mahasiswa_profile, status='PENDING')


class SupervisionRequestDetailUpdateView(generics.RetrieveUpdateAPIView):
    """
    - GET: Retrieves the details of a specific request.
      - Accessible by the Mahasiswa who sent it or the Dosen who received it.
    - PATCH: Updates a request.
      - Primarily for a Dosen to respond (accept/reject).
    """
    queryset = RequestDosen.objects.all().select_related('mahasiswa__user', 'dosen__user')
    http_method_names = ['get', 'patch'] # Only allow GET and PATCH

    def get_permissions(self):
        """
        - For PATCH (responding), only the recipient Dosen is allowed.
        - For GET (viewing), the owner Mahasiswa or recipient Dosen is allowed.
        """
        if self.request.method == 'PATCH':
            return [permissions.IsAuthenticated(), IsDosen(), IsRequestRecipientOrAdmin()]
        return [permissions.IsAuthenticated(), IsOwnerOrRecipient()]

    def get_serializer_class(self):
        """Returns the appropriate serializer for the action."""
        if self.request.method == 'PATCH':
            return RequestDosenRespondSerializer
        return RequestDosenListSerializer

    @transaction.atomic
    def perform_update(self, serializer):
        """Handles the logic for responding to a request (from the old view)."""
        request_instance = self.get_object()
        new_status = serializer.validated_data.get('status')

        if new_status == 'ACCEPTED':
            mahasiswa_profile = request_instance.mahasiswa
            dosen_profile = request_instance.dosen
            if TugasAkhir.objects.filter(mahasiswa=mahasiswa_profile).exists():
                raise ValidationError("Mahasiswa ini sudah memiliki data Tugas Akhir.")

            TugasAkhir.objects.create(
                mahasiswa=mahasiswa_profile,
                dosen_pembimbing=dosen_profile,
                judul=request_instance.rencana_judul,
                deskripsi=request_instance.rencana_deskripsi
            )
            mahasiswa_profile.dosen_pembimbing = dosen_profile
            mahasiswa_profile.save(update_fields=['dosen_pembimbing'])

        serializer.save()