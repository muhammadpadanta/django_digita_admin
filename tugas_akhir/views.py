from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import RequestDosen, TugasAkhir, Mahasiswa, Dosen
from .serializers import (
    RequestDosenCreateSerializer, RequestDosenListSerializer,
    RequestDosenRespondSerializer
)
from .permissions import IsMahasiswa, IsDosen, IsRequestRecipientOrAdmin

# --- Views for Supervisor Request Flow ---

class RequestDosenCreateView(generics.CreateAPIView):

    serializer_class = RequestDosenCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsMahasiswa]

    def perform_create(self, serializer):
        mahasiswa_profile = self.request.user.mahasiswa_profile

        # --- HAPUS/UBAH CEK TugasAkhir DI SINI ---
        # Cek apakah mahasiswa sudah punya TA (mungkin dari request sebelumnya)
        if TugasAkhir.objects.filter(mahasiswa=mahasiswa_profile).exists():
             # Atau jika boleh punya TA tanpa pembimbing, cek apakah pembimbing sudah ada
             # if TugasAkhir.objects.filter(mahasiswa=mahasiswa_profile, dosen_pembimbing__isnull=False).exists():
             raise ValidationError("Anda sudah terdaftar dalam proses Tugas Akhir.")
        # --------------------------------------------

        # Cek apakah sudah ada request PENDING
        if RequestDosen.objects.filter(mahasiswa=mahasiswa_profile, status='PENDING').exists():
             raise ValidationError("Anda sudah memiliki permintaan pembimbing yang PENDING.")

        # Cek self-request
        requested_dosen = serializer.validated_data['dosen']
        if hasattr(requested_dosen.user, 'mahasiswa_profile') and requested_dosen.user.mahasiswa_profile == mahasiswa_profile:
             raise ValidationError("Tidak bisa mengajukan diri sendiri sebagai pembimbing.")

        # Simpan request dengan data dari serializer
        serializer.save(mahasiswa=mahasiswa_profile, status='PENDING')
        # todo: Add notification logic here later



class MySupervisorRequestListView(generics.ListAPIView):

    serializer_class = RequestDosenListSerializer
    permission_classes = [permissions.IsAuthenticated, IsMahasiswa]

    def get_queryset(self):
        return RequestDosen.objects.filter(mahasiswa=self.request.user.mahasiswa_profile).select_related('mahasiswa__user', 'dosen__user')


class IncomingSupervisorRequestListView(generics.ListAPIView):

    serializer_class = RequestDosenListSerializer
    permission_classes = [permissions.IsAuthenticated, IsDosen]

    def get_queryset(self):
        return RequestDosen.objects.filter(
            dosen=self.request.user.dosen_profile,
            status='PENDING'
        ).select_related('mahasiswa__user', 'dosen__user')


class SupervisorRequestRespondView(generics.UpdateAPIView):

    serializer_class = RequestDosenRespondSerializer
    permission_classes = [permissions.IsAuthenticated, IsDosen, IsRequestRecipientOrAdmin]
    queryset = RequestDosen.objects.filter(status='PENDING')
    http_method_names = ['patch']

    # transaksi database
    @transaction.atomic
    def perform_update(self, serializer):
        request_instance = serializer.instance
        new_status = serializer.validated_data.get('status')

        if new_status == 'ACCEPTED':
            mahasiswa_profile = request_instance.mahasiswa
            dosen_profile = request_instance.dosen

            # 1. Pastikan mahasiswa belum punya TugasAkhir (penting!)
            if TugasAkhir.objects.filter(mahasiswa=mahasiswa_profile).exists():
                 # Seharusnya tidak terjadi jika validasi di create view benar
                 raise ValidationError("Mahasiswa ini sudah memiliki data Tugas Akhir.")

            # 2. Buat record TugasAkhir baru
            try:
                TugasAkhir.objects.create(
                    mahasiswa=mahasiswa_profile,
                    dosen_pembimbing=dosen_profile,
                    judul=request_instance.rencana_judul,
                    deskripsi=request_instance.rencana_deskripsi
                )
            except Exception as e:
                # Tangani kemungkinan error saat membuat TA
                raise ValidationError(f"Gagal membuat data Tugas Akhir: {e}")

            # Opsional: Tolak otomatis request lain yang PENDING dari mahasiswa yang sama
            # RequestDosen.objects.filter(
            #      mahasiswa=mahasiswa_profile,
            #      status='PENDING'
            # ).exclude(pk=request_instance.pk).update(status='REJECTED', dosen_response="Ditolak otomatis karena permintaan lain diterima.")


        serializer.save()
        # notification logic disini nanti
