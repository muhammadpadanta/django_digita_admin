from rest_framework import serializers
from users.serializers import JurusanSerializer
from users.models import Mahasiswa, Dosen, ProgramStudi
from .models import RequestDosen, TugasAkhir, Dokumen # Import Dokumen

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
class DokumenSerializer(serializers.ModelSerializer):
    """
    Serializer for the Dokumen model, using existing simple serializers
    for related user information.
    """
    pemilik_info = MahasiswaSimpleSerializer(source='pemilik', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    bab_display = serializers.CharField(source='get_bab_display', read_only=True)
    file_url = serializers.FileField(source='file', read_only=True)

    # Use write_only for the file upload field.
    file = serializers.FileField(write_only=True)

    class Meta:
        model = Dokumen
        fields = [
            'id',
            'bab',
            'bab_display',
            'nama_dokumen',
            'file', # write-only
            'file_url', # read-only
            'status',
            'status_display',
            'pemilik_info',
            'uploaded_at'
        ]
        read_only_fields = ['status']

    def create(self, validated_data):
        mahasiswa = self.context['request'].user.mahasiswa_profile
        try:
            tugas_akhir = TugasAkhir.objects.get(mahasiswa=mahasiswa)
        except TugasAkhir.DoesNotExist:
            raise serializers.ValidationError("Anda tidak memiliki data Tugas Akhir yang aktif untuk mengunggah dokumen.")

        validated_data['pemilik'] = mahasiswa
        validated_data['tugas_akhir'] = tugas_akhir
        validated_data['status'] = 'Pending'
        return super().create(validated_data)
