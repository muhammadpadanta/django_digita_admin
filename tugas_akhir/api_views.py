# tugas_akhir/api_views.py
import boto3
from botocore.exceptions import ClientError
from django.db import transaction
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework import serializers
from django.conf import settings
from core.firebase_utils import send_notification_to_user
from .models import Dokumen, RequestDosen, TugasAkhir, Mahasiswa, JadwalBimbingan, Ruangan
from .permissions import (
    IsDokumenOwner, IsDosen, IsMahasiswa, IsMahasiswaOrDosen,
    IsOwnerOrRecipient, IsOwnerOrSupervisingDosen,
    IsRequestRecipientOrAdmin, IsSupervisingDosen,
    IsJadwalOwner, IsJadwalDosen, IsJadwalOwnerOrDosen
)
from .serializers import (
    DokumenSerializer, DokumenStatusUpdateSerializer, RequestDosenCreateSerializer,
    RequestDosenListSerializer, RequestDosenRespondSerializer, SupervisedMahasiswaSerializer,
    JadwalBimbinganCreateSerializer, JadwalBimbinganListSerializer, JadwalBimbinganDosenResponseSerializer,
    JadwalBimbinganDosenCompleteSerializer, RuanganSerializer, JadwalBimbinganRescheduleSerializer
)

# --- View to list supervised students ---
class SupervisedStudentsListView(generics.ListAPIView):
    """
    API endpoint for a logged-in Dosen to view a list of all
    Mahasiswa they are supervising.
    """
    serializer_class = SupervisedMahasiswaSerializer
    permission_classes = [permissions.IsAuthenticated, IsDosen]

    def get_queryset(self):
        """
        Returns a queryset of Mahasiswa who are being supervised by the
        currently authenticated Dosen.
        """
        user = self.request.user
        return Mahasiswa.objects.filter(
            tugas_akhir__dosen_pembimbing=user.dosen_profile
        ).select_related('user', 'program_studi', 'tugas_akhir').order_by('user__first_name')

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
        dosen_profile = request_instance.dosen

        if new_status == 'ACCEPTED':
            mahasiswa_profile = request_instance.mahasiswa
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

        # --- 🚀 LOGIKA NOTIFIKASI UNTUK MAHASISWA ---
        try:
            recipient_user = request_instance.mahasiswa.user
            dosen_name = dosen_profile.user.get_full_name()
            status_display = "Disetujui" if new_status == 'ACCEPTED' else "Ditolak"

            title = "Update Permintaan Dosen Pembimbing"
            body = f"Permintaanmu kepada {dosen_name} sebagai pembimbing telah {status_display}."

            data = {
                'request_id': str(request_instance.id),
                'screen': 'supervision_request_detail'
            }

            send_notification_to_user(
                user=recipient_user,
                title=title,
                body=body,
                data=data
            )
        except Exception as e:
            print(f"Gagal mengirim notifikasi untuk respons permintaan dosen: {e}")
        # --- AKHIR LOGIKA NOTIFIKASI ---

class DokumenViewSet(viewsets.ModelViewSet):
    """
    Manages documents for a thesis (Tugas Akhir).
    """
    serializer_class = DokumenSerializer

    def get_queryset(self):
        """
        Dynamically filters the queryset based on the user's role.
        - Mahasiswa can see their own documents.
        - Dosen can see documents of the students they supervise.
        """
        user = self.request.user
        queryset = Dokumen.objects.none() # Start with an empty queryset

        if hasattr(user, 'mahasiswa_profile'):
            # Mahasiswa can only see their own documents
            queryset = Dokumen.objects.filter(pemilik=user.mahasiswa_profile)

        elif hasattr(user, 'dosen_profile'):
            # Dosen can see documents of students they supervise.
            # Check for the filter first.
            mahasiswa_id = self.request.query_params.get('mahasiswa_id')
            if mahasiswa_id:
                # If filtered, only show documents for that specific student,
                # but ensure the Dosen is actually their supervisor.
                queryset = Dokumen.objects.filter(
                    pemilik_id=mahasiswa_id,
                    tugas_akhir__dosen_pembimbing=user.dosen_profile
                )
            else:
                # If not filtered, show all documents from all supervised students.
                queryset = Dokumen.objects.filter(
                    tugas_akhir__dosen_pembimbing=user.dosen_profile
                )

        return queryset.select_related('pemilik__user', 'tugas_akhir').order_by('bab')

    def get_permissions(self):
        """Assigns permissions based on the requested action."""
        if self.action == 'update_status':
            self.permission_classes = [permissions.IsAuthenticated, IsSupervisingDosen]
        elif self.action == 'access_file':
            self.permission_classes = [permissions.IsAuthenticated, IsOwnerOrSupervisingDosen]
        elif self.action == 'status_checklist':
            self.permission_classes = [permissions.IsAuthenticated, IsMahasiswa]
        elif self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated, IsMahasiswa]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated, IsDokumenOwner]
        elif self.action == 'retrieve':
            self.permission_classes = [permissions.IsAuthenticated, IsOwnerOrSupervisingDosen]
        else: # Covers the 'list' action
            self.permission_classes = [permissions.IsAuthenticated, IsMahasiswaOrDosen]
        return super().get_permissions()

    def perform_create(self, serializer):
        """
        Saves the new document instance and notifies the supervising Dosen.
        """
        # The serializer.save() returns the created object instance
        new_document = serializer.save()

        # --- 🚀 NOTIFICATION LOGIC FOR DOSEN ---
        try:
            # Ensure the thesis and supervisor exist
            if new_document.tugas_akhir and new_document.tugas_akhir.dosen_pembimbing:
                recipient_user = new_document.tugas_akhir.dosen_pembimbing.user
                student_name = new_document.pemilik.user.get_full_name()

                title = "Mahasiswa Mengunggah Dokumen Baru"
                body = f"{student_name} telah mengunggah dokumen baru: '{new_document.nama_dokumen}'."

                # Data payload for client-side navigation
                data = {
                    'mahasiswa_id': str(new_document.pemilik.user_id),
                    'screen': 'document_list_for_student'
                }

                send_notification_to_user(
                    user=recipient_user,
                    title=title,
                    body=body,
                    data=data
                )
        except Exception as e:
            # Log the error but do not let it crash the main request
            print(f"Failed to send notification for new document upload: {e}")
        # --- END NOTIFICATION LOGIC ---

    def destroy(self, request, *args, **kwargs):
        """Overrides the default destroy method to return a success message."""
        instance = self.get_object()
        document_name = instance.nama_dokumen
        self.perform_destroy(instance)
        return Response(
            {"message": f"Dokumen '{document_name}' telah berhasil dihapus."},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['patch'], url_path='update-status')
    def update_status(self, request, pk=None):
        """
        Custom action for a Dosen to update a document's status.
        Requires 'catatan_revisi' if the status is set to 'Revisi'.
        """
        dokumen = self.get_object()
        serializer = DokumenStatusUpdateSerializer(dokumen, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()

            # --- 🚀 NOTIFICATION LOGIC FOR MAHASISWA ---
            try:
                recipient_user = dokumen.pemilik.user
                new_status = dokumen.get_status_display() # Gets "Disetujui" or "Revisi"

                title = f"Update Status Dokumen kamu nih!"
                body = f"Dokumen '{dokumen.nama_dokumen}' telah diupdate menjadi {new_status}."

                # Data payload for client-side navigation
                data = {
                    'document_id': str(dokumen.id),
                    'screen': 'document_detail'
                }

                send_notification_to_user(
                    user=recipient_user,
                    title=title,
                    body=body,
                    data=data
                )
            except Exception as e:
                # Log the error but do not let it crash the main request
                print(f"Failed to send notification for document status update: {e}")
            # --- END NOTIFICATION LOGIC ---

            return Response(DokumenSerializer(dokumen, context={'request': request}).data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='access-file')
    def access_file(self, request, pk=None):
        """
        Generates a temporary, secure pre-signed URL for an S3 file.
        The client can then use this URL to view or download the file directly from S3.
        Accepts a '?action=download' query parameter to force download.
        """
        document = self.get_object()

        if not document.file:
            return Response({"error": "File tidak ditemukan untuk dokumen ini."}, status=status.HTTP_404_NOT_FOUND)

        s3_client = boto3.client('s3', region_name=settings.AWS_S3_REGION_NAME)
        params = {
            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'Key': document.file.name,
        }

        if request.query_params.get('action') == 'download':
            file_name = document.file.name.split('/')[-1]
            params['ResponseContentDisposition'] = f'attachment; filename="{file_name}"'

        try:
            url = s3_client.generate_presigned_url('get_object', Params=params, ExpiresIn=900)
            return Response({'url': url})
        except ClientError as e:
            print(f"Error generating pre-signed URL: {e}")
            return Response({"error": "Tidak dapat membuat link aman untuk file tersebut."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='status-checklist')
    def status_checklist(self, request):
        """
        Provides a checklist of all required chapters and their upload status for the
        requesting Mahasiswa.
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

class JadwalBimbinganViewSet(viewsets.ModelViewSet):
    """
    Manages guidance schedule (Jadwal Bimbingan) for students and lecturers.
    """
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        """
        - Mahasiswa sees their own schedule requests.
        - Dosen sees incoming schedule requests from their students.
        """
        user = self.request.user
        if hasattr(user, 'mahasiswa_profile'):
            return JadwalBimbingan.objects.filter(mahasiswa=user.mahasiswa_profile).select_related('mahasiswa__user', 'dosen_pembimbing__user', 'lokasi_ruangan')
        if hasattr(user, 'dosen_profile'):
            return JadwalBimbingan.objects.filter(dosen_pembimbing=user.dosen_profile).select_related('mahasiswa__user', 'dosen_pembimbing__user', 'lokasi_ruangan')
        return JadwalBimbingan.objects.none()

    def get_serializer_class(self):
        """Return appropriate serializer based on action and user role."""
        if self.action == 'create':
            return JadwalBimbinganCreateSerializer
        if self.action == 'respond':
            return JadwalBimbinganDosenResponseSerializer
        if self.action == 'complete':
            return JadwalBimbinganDosenCompleteSerializer
        if self.action == 'reschedule':
            return JadwalBimbinganRescheduleSerializer
        return JadwalBimbinganListSerializer # For list and retrieve

    def get_permissions(self):
        """Assign permissions based on the action."""
        if self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated, IsMahasiswa]
        elif self.action == 'respond' or self.action == 'complete':
            self.permission_classes = [permissions.IsAuthenticated, IsJadwalDosen]
        elif self.action == 'reschedule':
            self.permission_classes = [permissions.IsAuthenticated, IsJadwalOwner]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            self.permission_classes = [permissions.IsAuthenticated, IsJadwalOwnerOrDosen]
        else: # list
            self.permission_classes = [permissions.IsAuthenticated, IsMahasiswaOrDosen]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['patch'], url_path='respond')
    def respond(self, request, pk=None):
        """
        Custom action for a Dosen to accept or reject a guidance request.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        # --- 🚀 LOGIKA NOTIFIKASI UNTUK MAHASISWA ---
        try:
            recipient_user = updated_instance.mahasiswa.user
            new_status_display = updated_instance.get_status_display().upper()

            title = f"Update Jadwal Bimbingan Kamu"
            body = f"Permintaan bimbinganmu untuk tanggal {updated_instance.tanggal.strftime('%d %B %Y')} telah {new_status_display} oleh dosen."

            data = {
                'schedule_id': str(updated_instance.id),
                'screen': 'guidance_schedule_detail'
            }

            send_notification_to_user(
                user=recipient_user,
                title=title,
                body=body,
                data=data
            )
        except Exception as e:
            print(f"Gagal mengirim notifikasi untuk respons bimbingan: {e}")
        # --- AKHIR LOGIKA NOTIFIKASI ---

        return Response(JadwalBimbinganListSerializer(updated_instance).data)

    @action(detail=True, methods=['patch'], url_path='complete')
    def complete(self, request, pk=None):
        """
        Custom action for a Dosen to mark a session as 'DONE' and add notes.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        # --- 🚀 LOGIKA NOTIFIKASI UNTUK MAHASISWA ---
        try:
            recipient_user = updated_instance.mahasiswa.user

            title = "Sesi Bimbingan Telah Selesai"
            body = f"Bimbinganmu pada tanggal {updated_instance.tanggal.strftime('%d %B %Y')} telah selesai. Jangan lupa cek catatan dari dosen ya!"

            data = {
                'schedule_id': str(updated_instance.id),
                'screen': 'guidance_schedule_detail'
            }

            send_notification_to_user(
                user=recipient_user,
                title=title,
                body=body,
                data=data
            )
        except Exception as e:
            # Log error jika terjadi, tapi jangan sampai menghentikan request utama
            print(f"Gagal mengirim notifikasi untuk bimbingan selesai: {e}")
        # --- AKHIR LOGIKA NOTIFIKASI ---

        return Response(JadwalBimbinganListSerializer(updated_instance).data)


    @action(detail=True, methods=['patch'], url_path='reschedule')
    def reschedule(self, request, pk=None):
        """
        Custom action for a Mahasiswa to reschedule a REJECTED guidance request.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        # --- 🚀 LOGIKA NOTIFIKASI UNTUK DOSEN (SAAT RESCHEDULE) ---
        try:
            recipient_user = updated_instance.dosen_pembimbing.user
            student_name = updated_instance.mahasiswa.user.get_full_name()

            title = "Pengajuan Jadwal Bimbingan Ulang"
            body = f"{student_name} telah mengajukan ulang jadwal bimbingan untuk tanggal {updated_instance.tanggal.strftime('%d %B %Y')}. Mohon ditinjau kembali."

            data = {
                'schedule_id': str(updated_instance.id),
                'mahasiswa_id': str(updated_instance.mahasiswa.user_id),
                'screen': 'guidance_schedule_detail'
            }

            send_notification_to_user(
                user=recipient_user,
                title=title,
                body=body,
                data=data
            )
        except Exception as e:
            print(f"Gagal mengirim notifikasi untuk reschedule bimbingan: {e}")
        # --- AKHIR LOGIKA NOTIFIKASI ---

        return Response(JadwalBimbinganListSerializer(updated_instance).data)