from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import Jurusan, ProgramStudi, Mahasiswa, Dosen


# --- Serializer untuk List Dosen ---
class DosenListSerializer(serializers.ModelSerializer):
    """
    Serializer untuk menampilkan daftar Dosen beserta informasi
    tambahan (nama lengkap, email, jurusan, jumlah mahasiswa bimbingan).
    """

    nama_lengkap = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    # Field ini akan diisi oleh anotasi dari view
    jumlah_mahasiswa_aktif = serializers.IntegerField(read_only=True)

    class Meta:
        model = Dosen
        fields = [
            'user_id', # Primary key Dosen (sama dengan user_id)
            'nik',
            'nama_lengkap',
            'email',
            'jurusan', # Akan berisi Jurusan jika menggunakan JurusanSerializer
            'jumlah_mahasiswa_aktif'
        ]
        read_only_fields = fields # Semua field read-only untuk list view

# --- Serializer untuk data lookup (dropdown, dll) ---
class JurusanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Jurusan
        fields = ['id', 'nama_jurusan']

class ProgramStudiSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramStudi
        fields = ['id', 'nama_prodi', 'jurusan']

# --- Registration Serializers ---

class RegisterMahasiswaSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Konfirmasi Kata Sandi")
    email = serializers.EmailField(required=True, write_only=True)
    nama_lengkap = serializers.CharField(required=True, max_length=255, write_only=True)
    program_studi_id = serializers.PrimaryKeyRelatedField(
        queryset=ProgramStudi.objects.all(),
        source='program_studi',
        write_only=True
    )

    nim = serializers.CharField(
        max_length=50,
        required=True,
        validators=[
            UniqueValidator(
                queryset=Mahasiswa.objects.all(),
                message="Mahasiswa dengan NIM ini sudah ada."
            )
        ]
    )

    class Meta:
        model = Mahasiswa
        fields = ['nim', 'program_studi_id', 'email', 'password', 'password2', 'nama_lengkap']

    def validate(self, attrs):
        """Validasi data tambahan (password, keunikan User)."""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Konfirmasi kata sandi tidak cocok."})

        if User.objects.filter(username=attrs['nim']).exists():
            raise serializers.ValidationError({"nim": "NIM ini sudah terdaftar sebagai username pengguna lain."})

        # Cek keunikan email di tabel User
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Pengguna dengan email ini sudah terdaftar."})

        # Validasi tambahan
        if not attrs['email'].endswith('@polibatam.ac.id'):
            raise serializers.ValidationError({"email": "Harus menggunakan email universitas."})

        return attrs

    def create(self, validated_data):
        """Membuat instance User dan Mahasiswa."""
        user = User.objects.create(
            username=validated_data['nim'],
            email=validated_data['email'],
            first_name=validated_data['nama_lengkap']
        )
        user.set_password(validated_data['password'])
        user.save()

        mahasiswa = Mahasiswa.objects.create(
            user=user,
            nim=validated_data['nim'],
            program_studi=validated_data['program_studi']
        )
        return mahasiswa


class RegisterDosenSerializer(serializers.ModelSerializer):
    # Deklarasi eksplisit field yang dibutuhkan untuk input/validasi
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Konfirmasi Kata Sandi")
    email = serializers.EmailField(required=True, write_only=True)
    nama_lengkap = serializers.CharField(required=True, max_length=255, write_only=True)
    jurusan_id = serializers.PrimaryKeyRelatedField(
        queryset=Jurusan.objects.all(),
        source='jurusan',
        write_only=True
    )

    nik = serializers.CharField(
        max_length=50,
        required=True,
        validators=[
            UniqueValidator(
                queryset=Dosen.objects.all(),
                message="Dosen dengan NIK ini sudah ada."
            )
        ]
    )

    class Meta:
        model = Dosen
        fields = ['nik', 'jurusan_id', 'email', 'password', 'password2', 'nama_lengkap']

    def validate(self, attrs):
        """Validasi data tambahan (password, keunikan User)."""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Konfirmasi kata sandi tidak cocok."})

        # Cek keunikan username (NIK) di tabel User
        if User.objects.filter(username=attrs['nik']).exists():
             # Pesan untuk kasus username User bentrok
            raise serializers.ValidationError({"nik": "NIK ini sudah terdaftar sebagai username pengguna lain."})

        # Cek keunikan email di tabel User
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Pengguna dengan email ini sudah terdaftar."})

        # Validasi tambahan
        if not attrs['email'].endswith('@polibatam.ac.id'):
            raise serializers.ValidationError({"email": "Harus menggunakan email universitas."})

        return attrs

    def create(self, validated_data):
        """Membuat instance User dan Dosen."""
        user = User.objects.create(
            username=validated_data['nik'],
            email=validated_data['email'],
            first_name=validated_data['nama_lengkap']
        )
        user.set_password(validated_data['password'])
        user.save()

        dosen = Dosen.objects.create(
            user=user,
            nik=validated_data['nik'],
            jurusan=validated_data['jurusan']
        )
        return dosen


# --- Login Serializer ---
class LoginSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=['mahasiswa', 'dosen'])
    identifier = serializers.CharField(label="NIM / NIK")
    password = serializers.CharField(write_only=True)
