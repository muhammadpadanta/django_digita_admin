# users/serializers.py

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import Jurusan, ProgramStudi, Mahasiswa, Dosen


# --- Serializer untuk List Dosen ---
class DosenSerializer(serializers.ModelSerializer):

    nama_lengkap = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    jumlah_mahasiswa_aktif = serializers.IntegerField(read_only=True)

    class Meta:
        model = Dosen
        fields = [
            'user_id',
            'nik',
            'nama_lengkap',
            'email',
            'jurusan',
            'jumlah_mahasiswa_aktif'
        ]
        read_only_fields = fields

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
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Konfirmasi kata sandi tidak cocok."})

        if User.objects.filter(username=attrs['nim']).exists():
            raise serializers.ValidationError({"nim": "NIM ini sudah terdaftar sebagai username pengguna lain."})

        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Pengguna dengan email ini sudah terdaftar."})

        # Validasi tambahan
        # if not attrs['email'].endswith('@polibatam.ac.id'):
        #     raise serializers.ValidationError({"email": "Harus menggunakan email universitas."})

        return attrs

    def create(self, validated_data):
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
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Konfirmasi kata sandi tidak cocok."})

        if User.objects.filter(username=attrs['nik']).exists():
            raise serializers.ValidationError({"nik": "NIK ini sudah terdaftar sebagai username pengguna lain."})

        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Pengguna dengan email ini sudah terdaftar."})

        # Validasi tambahan
        # if not attrs['email'].endswith('@polibatam.ac.id'):
        #     raise serializers.ValidationError({"email": "Harus menggunakan email universitas."})

        return attrs

    def create(self, validated_data):
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


# --- Password Reset Serializers ---
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user is registered with this email address.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        try:
            uid = force_str(urlsafe_base64_decode(attrs['uid']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"uid": "Invalid user ID."})

        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError({"token": "Invalid or expired token."})

        attrs['user'] = user
        return attrs

class MahasiswaDetailSerializer(serializers.ModelSerializer):
    """
    Serializer to represent detailed Mahasiswa data for the API.
    """
    # Get fields from the related User model
    nama_lengkap = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    # Represent related models with their string representation
    program_studi = serializers.StringRelatedField(read_only=True)
    dosen_pembimbing = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Mahasiswa
        fields = [
            'user_id',
            'nim',
            'nama_lengkap',
            'email',
            'program_studi',
            'dosen_pembimbing',
            'dosen_pembimbing_id',
        ]
        read_only_fields = fields

# --- Profile Update Serializers ---

class MahasiswaProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving and updating the logged-in student's profile.
    """
    nama_lengkap = serializers.CharField(source='user.first_name', max_length=255)
    email = serializers.EmailField(source='user.email')
    nim = serializers.CharField(read_only=True)
    program_studi_id = serializers.PrimaryKeyRelatedField(
        queryset=ProgramStudi.objects.all(),
        source='program_studi',
        write_only=True,
        label="ID Program Studi"
    )
    # Provides a readable representation for GET requests
    program_studi = ProgramStudiSerializer(read_only=True)
    jurusan = serializers.StringRelatedField(source='program_studi.jurusan', read_only=True)


    class Meta:
        model = Mahasiswa
        fields = [
            'nim',
            'nama_lengkap',
            'email',
            'program_studi',
            'jurusan',
            'program_studi_id' # For writing/updating
        ]

    def update(self, instance, validated_data):
        # Handle nested User model update
        user_data = validated_data.pop('user', {})
        user = instance.user
        user.first_name = user_data.get('first_name', user.first_name)
        user.email = user_data.get('email', user.email)
        # Check if email is being changed to one that already exists
        if 'email' in user_data and User.objects.exclude(pk=user.pk).filter(email=user_data['email']).exists():
            raise serializers.ValidationError({"email": "This email is already in use by another account."})
        user.save()

        # Handle Mahasiswa model update
        return super().update(instance, validated_data)

class DosenProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving and updating the logged-in lecturer's profile.
    """
    nama_lengkap = serializers.CharField(source='user.first_name', max_length=255)
    email = serializers.EmailField(source='user.email')
    nik = serializers.CharField(read_only=True)
    jurusan_id = serializers.PrimaryKeyRelatedField(
        queryset=Jurusan.objects.all(),
        source='jurusan',
        write_only=True,
        label="ID Jurusan"
    )
    # Provides a readable representation for GET requests
    jurusan = JurusanSerializer(read_only=True)

    class Meta:
        model = Dosen
        fields = ['nik', 'nama_lengkap', 'email', 'jurusan', 'jurusan_id']

    def update(self, instance, validated_data):
        # Handle nested User model update
        user_data = validated_data.pop('user', {})
        user = instance.user
        user.first_name = user_data.get('first_name', user.first_name)
        user.email = user_data.get('email', user.email)
        # Check if email is being changed to one that already exists
        if 'email' in user_data and User.objects.exclude(pk=user.pk).filter(email=user_data['email']).exists():
            raise serializers.ValidationError({"email": "This email is already in use by another account."})
        user.save()

        # Handle Dosen model update
        return super().update(instance, validated_data)