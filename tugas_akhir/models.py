from django.db import models
from django.db.models import Q
from users.models import Mahasiswa, Dosen

# --- Model TugasAkhir ---
class TugasAkhir(models.Model):
    mahasiswa = models.OneToOneField(Mahasiswa, on_delete=models.CASCADE, related_name='tugas_akhir')
    dosen_pembimbing = models.ForeignKey(
        Dosen,
        on_delete=models.SET_NULL, # Atau PROTECT
        null=True,
        blank=True,
        related_name='mahasiswa_bimbingan'
    )
    judul = models.CharField(max_length=255, null=True, blank=True)
    deskripsi = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"TA {self.mahasiswa.nim} - {self.judul or 'Belum ada judul'}"

# ---  Model RequestDosen ---
class RequestDosen(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]

    mahasiswa = models.ForeignKey(Mahasiswa, on_delete=models.CASCADE, related_name='request_dosen_sent')
    dosen = models.ForeignKey(Dosen, on_delete=models.CASCADE, related_name='request_dosen_received')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # Field baru untuk menyimpan proposal awal mahasiswa
    rencana_judul = models.CharField(max_length=255, null=True, blank=False)
    rencana_deskripsi = models.TextField(null=True, blank=False)

    alasan_memilih_dosen = models.TextField(null=True, blank=True)

    dosen_response = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['mahasiswa'], condition=Q(status='PENDING'), name='unique_pending_request_per_mahasiswa')
            # Tambahkan constraint lain kalo perlu, misal mahasiswa hanya bisa punya 1 TA aktif
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Request from {self.mahasiswa.nim} to {self.dosen.nik} ({self.status})"
