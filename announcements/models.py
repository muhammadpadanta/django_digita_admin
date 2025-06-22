# announcements/models.py

from django.db import models
from django.conf import settings

class Pengumuman(models.Model):
    """
    Represents an announcement in the system.
    """
    judul = models.CharField(max_length=255, help_text="Judul pengumuman")
    deskripsi = models.TextField(help_text="Isi lengkap dari pengumuman")
    tanggal_mulai = models.DateField(help_text="Tanggal pengumuman mulai ditampilkan")
    tanggal_selesai = models.DateField(help_text="Tanggal pengumuman berakhir")
    lampiran = models.FileField(upload_to='attachments/announcements/', blank=True, null=True, help_text="File lampiran opsional")

    # Optional: Track who created the announcement if you have an admin/staff role
    # author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pengumuman"
        verbose_name_plural = "Pengumuman"
        ordering = ['-tanggal_mulai'] # Show the newest announcements first

    def __str__(self):
        return self.judul