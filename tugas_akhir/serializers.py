from rest_framework import serializers
from users.serializers import JurusanSerializer
from users.models import Mahasiswa, Dosen
from .models import RequestDosen, TugasAkhir

# --- Nested Serializers untuk Read-Only Info ---
class MahasiswaSimpleSerializer(serializers.ModelSerializer):
    nama_lengkap = serializers.CharField(source='user.get_full_name', read_only=True)
    class Meta:
        model = Mahasiswa
        fields = ['user_id', 'nim', 'nama_lengkap'] # user_id adalah PK

class DosenSimpleSerializer(serializers.ModelSerializer):
    nama_lengkap = serializers.CharField(source='user.get_full_name', read_only=True)
    class Meta:
        model = Dosen
        fields = ['user_id', 'nik', 'nama_lengkap', 'jurusan'] # user_id adalah PK

# --- Serializers for RequestDosen ---

class RequestDosenCreateSerializer(serializers.ModelSerializer):
    """Serializer for Student creating a request."""
    dosen_id = serializers.PrimaryKeyRelatedField(
        queryset=Dosen.objects.all(), source='dosen', write_only=True, label="Dosen Pembimbing"
    )
    # Sesuaikan nama field dan requirement
    rencana_judul = serializers.CharField(max_length=255, required=True)
    rencana_deskripsi = serializers.CharField(required=True, style={'base_template': 'textarea.html'})
    alasan_memilih_dosen = serializers.CharField(required=True, style={'base_template': 'textarea.html'})

    class Meta:
        model = RequestDosen
        fields = ['dosen_id', 'rencana_judul', 'rencana_deskripsi', 'alasan_memilih_dosen']


class RequestDosenListSerializer(serializers.ModelSerializer):
    """Serializer for listing requests (for both student and dosen)."""
    mahasiswa = MahasiswaSimpleSerializer(read_only=True)
    dosen = DosenSimpleSerializer(read_only=True)

    class Meta:
        model = RequestDosen
        # Tambahkan field baru ke list
        fields = [
            'id', 'mahasiswa', 'dosen', 'status',
            'rencana_judul', 'rencana_deskripsi',
            'alasan_memilih_dosen', 'dosen_response',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields


class RequestDosenRespondSerializer(serializers.ModelSerializer):
    """Serializer for Dosen responding to a request."""
    status = serializers.ChoiceField(choices=[('ACCEPTED', 'Accepted'), ('REJECTED', 'Rejected')])
    dosen_response = serializers.CharField(required=False, allow_blank=True, style={'base_template': 'textarea.html'})

    class Meta:
        model = RequestDosen
        fields = ['status', 'dosen_response']

    def validate(self, attrs):
        if self.instance and self.instance.status != 'PENDING':
            raise serializers.ValidationError("Hanya request dengan status PENDING yang dapat direspon.")
        return attrs
