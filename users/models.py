# users/models.py

from django.db import models
from django.contrib.auth.models import User

class Jurusan(models.Model):
    nama_jurusan = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.nama_jurusan

class ProgramStudi(models.Model):
    nama_prodi = models.CharField(max_length=255, unique=True)
    jurusan = models.ForeignKey(Jurusan, on_delete=models.PROTECT, related_name='program_studi')

    def __str__(self):
        return self.nama_prodi

class Dosen(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='dosen_profile')
    nik = models.CharField(max_length=50, unique=True)
    jurusan = models.ForeignKey(Jurusan, on_delete=models.PROTECT, related_name='dosen')

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.nik})"

class Mahasiswa(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='mahasiswa_profile')
    nim = models.CharField(max_length=50, unique=True)
    program_studi = models.ForeignKey(ProgramStudi, on_delete=models.PROTECT, related_name='mahasiswa')
    dosen_pembimbing = models.ForeignKey(Dosen, on_delete=models.SET_NULL, null=True, blank=True, related_name='mahasiswa_binaan')
    # foto_profil bisa ditambahkan di sini nanti

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.nim})"