# tugas_akhir/api_views.py

from django.db import transaction
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import Dokumen, RequestDosen, TugasAkhir
from .permissions import (
    IsDokumenOwner, IsDosen, IsMahasiswa, IsMahasiswaOrDosen,
    IsOwnerOrRecipient, IsOwnerOrSupervisingDosen,
    IsRequestRecipientOrAdmin, IsSupervisingDosen
)
from .serializers import (
    DokumenSerializer, RequestDosenCreateSerializer,
    RequestDosenListSerializer, RequestDosenRespondSerializer
)


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
            return RequestDosen.objects.filter(mahasiswa=user.mahasiswa_profile).select_related('mahasiswa__user', 'dosen__user')
        if hasattr(user, 'dosen_profile'):
            return RequestDosen.objects.filter(dosen=user.dosen_profile, status='PENDING').select_related('mahasiswa__user', 'dosen__user')
        return RequestDosen.objects.none()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RequestDosenCreateSerializer
        return RequestDosenListSerializer

    def perform_create(self, serializer):
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
    - PATCH: Updates a request (for a Dosen to respond).
    """
    queryset = RequestDosen.objects.all().select_related('mahasiswa__user', 'dosen__user')
    http_method_names = ['get', 'patch']

    def get_permissions(self):
        if self.request.method == 'PATCH':
            self.permission_classes = [permissions.IsAuthenticated, IsDosen, IsRequestRecipientOrAdmin]
        else:
            self.permission_classes = [permissions.IsAuthenticated, IsOwnerOrRecipient]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return RequestDosenRespondSerializer
        return RequestDosenListSerializer

    @transaction.atomic
    def perform_update(self, serializer):
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


class DokumenViewSet(viewsets.ModelViewSet):
    """
    Manages documents for a thesis (Tugas Akhir).
    """
    serializer_class = DokumenSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'mahasiswa_profile'):
            return Dokumen.objects.filter(pemilik=user.mahasiswa_profile).select_related('pemilik__user', 'tugas_akhir')
        elif hasattr(user, 'dosen_profile'):
            return Dokumen.objects.filter(tugas_akhir__dosen_pembimbing=user.dosen_profile).select_related('pemilik__user', 'tugas_akhir')
        return Dokumen.objects.none()

    def get_permissions(self):
        if self.action == 'status_checklist':
            self.permission_classes = [permissions.IsAuthenticated, IsMahasiswa]
        elif self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated, IsMahasiswa]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated, IsDokumenOwner]
        elif self.action == 'retrieve':
            self.permission_classes = [permissions.IsAuthenticated, IsOwnerOrSupervisingDosen]
        elif self.action == 'update_status':
            self.permission_classes = [permissions.IsAuthenticated, IsSupervisingDosen]
        else:
            self.permission_classes = [permissions.IsAuthenticated, IsMahasiswaOrDosen]
        return super().get_permissions()

    @action(detail=False, methods=['get'], url_path='status-checklist')
    def status_checklist(self, request):
        """
        Provides a complete checklist of all required thesis chapters (BAB)
        and the status of each for the currently logged-in student.
        """
        mahasiswa = request.user.mahasiswa_profile
        uploaded_docs = {doc.bab: doc for doc in Dokumen.objects.filter(pemilik=mahasiswa)}
        all_babs = Dokumen.BAB_CHOICES
        checklist_data = []
        for bab_code, bab_display_name in all_babs:
            if bab_code in uploaded_docs:
                document = uploaded_docs[bab_code]
                serializer = self.get_serializer(document)
                checklist_data.append({
                    'bab': bab_code,
                    'is_uploaded': True,
                    'document_details': serializer.data
                })
            else:
                checklist_data.append({
                    'bab': bab_code,
                    'is_uploaded': False,
                    'document_details': None
                })
        return Response(checklist_data)

    def perform_create(self, serializer):
        """Passes the request context to the serializer to set the owner."""
        serializer.save(context={'request': self.request})

    @action(detail=True, methods=['patch'], url_path='update-status')
    def update_status(self, request, pk=None):
        """Custom action for a Dosen to update a document's status."""
        dokumen = self.get_object()
        new_status = request.data.get('status')
        if new_status not in [choice[0] for choice in Dokumen.STATUS_CHOICES]:
            return Response({'error': 'Status yang diberikan tidak valid.'}, status=status.HTTP_400_BAD_REQUEST)
        dokumen.status = new_status
        dokumen.save(update_fields=['status'])
        serializer = self.get_serializer(dokumen)
        return Response(serializer.data)