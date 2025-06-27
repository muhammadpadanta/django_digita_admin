from rest_framework import serializers
from users.serializers import JurusanSerializer
from users.models import Mahasiswa, Dosen, ProgramStudi
from .models import RequestDosen, TugasAkhir, Dokumen, JadwalBimbingan, Ruangan
from django.urls import reverse
import datetime


class ProgramStudiSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramStudi
        fields = ['id', 'nama_prodi']

# --- Nested Serializers untuk Read-Only Info ---
class MahasiswaSimpleSerializer(serializers.ModelSerializer):
    nama_lengkap = serializers.CharField(source='user.get_full_name', read_only=True)
    program_studi = ProgramStudiSerializer(read_only=True)
    class Meta:
        model = Mahasiswa
        fields = ['user_id', 'nim', 'nama_lengkap', 'program_studi']

class DosenSimpleSerializer(serializers.ModelSerializer):
    nama_lengkap = serializers.CharField(source='user.get_full_name', read_only=True)
    class Meta:
        model = Dosen
        fields = ['user_id', 'nik', 'nama_lengkap', 'jurusan']

# --- Serializer for Supervised Students List ---
class SupervisedMahasiswaSerializer(serializers.ModelSerializer):
    """
    Serializer to represent a supervised student, including their thesis title.
    """
    nama_lengkap = serializers.CharField(source='user.get_full_name', read_only=True)
    program_studi = ProgramStudiSerializer(read_only=True)
    judul_skripsi = serializers.CharField(source='tugas_akhir.judul', read_only=True, default='Belum ada judul')

    class Meta:
        model = Mahasiswa
        fields = [
            'user_id',
            'nim',
            'nama_lengkap',
            'program_studi',
            'judul_skripsi'
        ]

# --- Serializers for RequestDosen ---
class RequestDosenCreateSerializer(serializers.ModelSerializer):
    dosen_id = serializers.PrimaryKeyRelatedField(
        queryset=Dosen.objects.all(), source='dosen', write_only=True, label="Dosen Pembimbing"
    )
    rencana_judul = serializers.CharField(max_length=255, required=True)
    rencana_deskripsi = serializers.CharField(required=True, style={'base_template': 'textarea.html'})
    alasan_memilih_dosen = serializers.CharField(required=True, style={'base_template': 'textarea.html'})

    class Meta:
        model = RequestDosen
        fields = ['dosen_id', 'rencana_judul', 'rencana_deskripsi', 'alasan_memilih_dosen']

class RequestDosenListSerializer(serializers.ModelSerializer):
    mahasiswa = MahasiswaSimpleSerializer(read_only=True)
    dosen = DosenSimpleSerializer(read_only=True)

    class Meta:
        model = RequestDosen
        fields = [
            'id', 'mahasiswa', 'dosen', 'status',
            'rencana_judul', 'rencana_deskripsi',
            'alasan_memilih_dosen', 'dosen_response',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields

class RequestDosenRespondSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=[('ACCEPTED', 'Accepted'), ('REJECTED', 'Rejected')])
    dosen_response = serializers.CharField(required=False, allow_blank=True, style={'base_template': 'textarea.html'})

    class Meta:
        model = RequestDosen
        fields = ['status', 'dosen_response']

    def validate(self, attrs):
        if self.instance and self.instance.status != 'PENDING':
            raise serializers.ValidationError("Hanya request dengan status PENDING yang dapat direspon.")
        return attrs

# --- Serializer for Dokumen ---

class DokumenStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a document's status.
    Requires `catatan_revisi` if status is 'Revisi'.
    """
    status = serializers.ChoiceField(choices=[('Revisi', 'Revisi'), ('Disetujui', 'Disetujui')])
    catatan_revisi = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        style={'base_template': 'textarea.html'}
    )

    class Meta:
        model = Dokumen
        fields = ['status', 'catatan_revisi']

    def validate(self, data):
        """
        Checks that catatan_revisi is provided if status is 'Revisi'.
        """
        status = data.get('status')
        catatan = data.get('catatan_revisi')

        if status == 'Revisi' and not catatan:
            raise serializers.ValidationError({"catatan_revisi": "Catatan revisi wajib diisi jika status adalah 'Revisi'."})

        # When approved, clear any previous revision notes.
        if status == 'Disetujui':
            data['catatan_revisi'] = None

        return data
class DokumenSerializer(serializers.ModelSerializer):
    """
    Serializer for the Dokumen model, using existing simple serializers
    for related user information.
    """
    pemilik_info = MahasiswaSimpleSerializer(source='pemilik', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    bab_display = serializers.CharField(source='get_bab_display', read_only=True)

    # NEW: This field provides a secure API endpoint to get the file URL.
    file_url = serializers.SerializerMethodField()

    # Use write_only for the file upload field. The client won't receive this field on GET.
    file = serializers.FileField(write_only=True)

    class Meta:
        model = Dokumen
        fields = [
            'id',
            'bab',
            'bab_display',
            'nama_dokumen',
            'file',
            'file_url',
            'status',
            'status_display',
            'catatan_revisi', # Displays the revision notes
            'pemilik_info',
            'uploaded_at'
        ]
        read_only_fields = [
            'status', 'catatan_revisi', 'pemilik_info', 'uploaded_at',
            'status_display', 'bab_display', 'file_url'
        ]

    def get_file_url(self, obj):
        """
        Return the full URL to the 'access-file' endpoint for the document.
        This endpoint will in turn generate and return a pre-signed S3 URL.
        """
        request = self.context.get('request')
        if request and obj.file:
            # The name 'dokumen-api-access-file' is automatically generated by the router
            # from the basename 'dokumen-api' and the action name 'access_file'.
            return request.build_absolute_uri(
                reverse('dokumen-api-access-file', kwargs={'pk': obj.pk})
            )
        return None

    def create(self, validated_data):
        mahasiswa = self.context['request'].user.mahasiswa_profile
        try:
            tugas_akhir = TugasAkhir.objects.get(mahasiswa=mahasiswa)
        except TugasAkhir.DoesNotExist:
            raise serializers.ValidationError("Anda tidak memiliki data Tugas Akhir yang aktif untuk mengunggah dokumen.")

        # Add validation to prevent duplicate BAB uploads
        bab = validated_data.get('bab')
        if Dokumen.objects.filter(pemilik=mahasiswa, bab=bab).exists():
            raise serializers.ValidationError({'bab': f'Anda sudah pernah mengunggah dokumen untuk {bab}.'})

        validated_data['pemilik'] = mahasiswa
        validated_data['tugas_akhir'] = tugas_akhir
        validated_data['status'] = 'Pending'
        return super().create(validated_data)

# --- NEW: Serializers for Jadwal Bimbingan ---
class RuanganSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ruangan
        fields = ['id', 'nama_ruangan', 'gedung', 'keterangan']

class JadwalBimbinganCreateSerializer(serializers.ModelSerializer):
    """Serializer for a student to create a new guidance schedule request."""
    lokasi_ruangan_id = serializers.PrimaryKeyRelatedField(
        queryset=Ruangan.objects.all(),
        source='lokasi_ruangan',
        write_only=True,
        label="Lokasi Bimbingan"
    )

    class Meta:
        model = JadwalBimbingan
        fields = [
            'judul_bimbingan', 'tanggal', 'waktu',
            'lokasi_ruangan_id'
        ]

    def validate_tanggal(self, value):
        """Check that the date is not in the past."""
        if value < datetime.date.today():
            raise serializers.ValidationError("Tanggal bimbingan tidak boleh di masa lalu.")
        return value

    def create(self, validated_data):
        mahasiswa = self.context['request'].user.mahasiswa_profile
        try:
            tugas_akhir = TugasAkhir.objects.get(mahasiswa=mahasiswa)
        except TugasAkhir.DoesNotExist:
            raise serializers.ValidationError("Anda harus memiliki data Tugas Akhir untuk mengajukan bimbingan.")

        if not tugas_akhir.dosen_pembimbing:
            raise serializers.ValidationError("Dosen pembimbing Anda belum ditentukan.")

        validated_data['mahasiswa'] = mahasiswa
        validated_data['dosen_pembimbing'] = tugas_akhir.dosen_pembimbing
        validated_data['status'] = 'PENDING'

        return super().create(validated_data)


class JadwalBimbinganListSerializer(serializers.ModelSerializer):
    """Serializer for listing guidance schedules with nested details."""
    mahasiswa = MahasiswaSimpleSerializer(read_only=True)
    dosen_pembimbing = DosenSimpleSerializer(read_only=True)
    lokasi_ruangan = RuanganSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = JadwalBimbingan
        fields = [
            'id', 'mahasiswa', 'dosen_pembimbing', 'judul_bimbingan',
            'tanggal', 'waktu', 'lokasi_ruangan',
            'status', 'status_display', 'alasan_penolakan', 'catatan_bimbingan',
            'created_at', 'updated_at'
        ]

class JadwalBimbinganDosenResponseSerializer(serializers.ModelSerializer):
    """Serializer for Dosen to respond to a PENDING request."""
    status = serializers.ChoiceField(choices=[('ACCEPTED', 'ACCEPTED'), ('REJECTED', 'REJECTED')])
    alasan_penolakan = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = JadwalBimbingan
        fields = ['status', 'alasan_penolakan']

    def validate(self, data):
        if self.instance and self.instance.status != 'PENDING':
            raise serializers.ValidationError("Hanya permintaan dengan status PENDING yang bisa direspon.")

        status = data.get('status')
        alasan = data.get('alasan_penolakan')

        if status == 'REJECTED' and not alasan:
            raise serializers.ValidationError({"alasan_penolakan": "Alasan penolakan wajib diisi jika permintaan ditolak."})

        if status == 'ACCEPTED':
            # Clear any previous rejection reason when accepting.
            data['alasan_penolakan'] = None

        return data

class JadwalBimbinganDosenCompleteSerializer(serializers.ModelSerializer):
    """Serializer for Dosen to mark an ACCEPTED session as DONE."""
    catatan_bimbingan = serializers.CharField(required=True)

    class Meta:
        model = JadwalBimbingan
        fields = ['catatan_bimbingan']

    def validate(self, data):
        if self.instance and self.instance.status != 'ACCEPTED':
            raise serializers.ValidationError("Hanya bimbingan yang sudah disetujui yang bisa diselesaikan.")
        return data

    def update(self, instance, validated_data):
        instance.status = 'DONE'
        instance.catatan_bimbingan = validated_data.get('catatan_bimbingan', instance.catatan_bimbingan)
        instance.save()
        return instance
