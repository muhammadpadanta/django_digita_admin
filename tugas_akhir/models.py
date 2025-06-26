from django.db import models
from django.db.models import Q
from users.models import Mahasiswa, Dosen

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db.models import UniqueConstraint
from storages.backends.s3boto3 import S3Boto3Storage

def validate_file_size(value):
    """
    Validates that the file size does not exceed 2MB.
    """
    filesize = value.size
    if filesize > 2 * 1024 * 1024:  # 2MB
        raise ValidationError("Ukuran file maksimal adalah 2MB.")
    return value

# --- Model TugasAkhir ---
class TugasAkhir(models.Model):
    mahasiswa = models.OneToOneField(Mahasiswa, on_delete=models.CASCADE, related_name='tugas_akhir')
    dosen_pembimbing = models.ForeignKey(
        Dosen,
        on_delete=models.SET_NULL,
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
    rencana_judul = models.CharField(max_length=255, null=True, blank=False)
    rencana_deskripsi = models.TextField(null=True, blank=False)
    alasan_memilih_dosen = models.TextField(null=True, blank=True)
    dosen_response = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['mahasiswa'], condition=Q(status='PENDING'), name='unique_pending_request_per_mahasiswa')
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Request from {self.mahasiswa.nim} to {self.dosen.nik} ({self.status})"

# --- Model Dokumen ---
class Dokumen(models.Model):
    """
    Represents a document submitted by a student for their thesis.
    """
    BAB_CHOICES = [
        ('BAB I', 'BAB I - Pendahuluan'),
        ('BAB II', 'BAB II - Tinjauan Pustaka'),
        ('BAB III', 'BAB III - Metodologi Penelitian'),
        ('BAB IV', 'BAB IV - Hasil dan Pembahasan'),
        ('BAB V', 'BAB V - Kesimpulan dan Saran'),
        ('LAMPIRAN', 'Lampiran'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Revisi', 'Revisi'),
        ('Disetujui', 'Disetujui'),
    ]

    tugas_akhir = models.ForeignKey(TugasAkhir, on_delete=models.CASCADE, related_name='dokumen')
    bab = models.CharField(
        max_length=50,
        choices=BAB_CHOICES,
        help_text="Chapter of the document"
    )
    nama_dokumen = models.CharField(max_length=255, help_text="Name of the document file")

    # MODIFIED: Added validators for file type and size
    file = models.FileField(
        upload_to='dokumen_ta/',
        storage=S3Boto3Storage(),
        help_text="The uploaded document file",
        validators=[
            validate_file_size,
            FileExtensionValidator(
                allowed_extensions=['pdf'],
                message="File harus dalam format PDF."
            )
        ]
    )
    file_hash = models.CharField(max_length=64, blank=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', help_text="Approval status of the document")
    # NEW: Field for revision notes from the Dosen.
    catatan_revisi = models.TextField(
        blank=True, null=True,
        help_text="Catatan dari dosen jika statusnya adalah Revisi"
    )
    pemilik = models.ForeignKey(Mahasiswa, on_delete=models.CASCADE, related_name='dokumen_mahasiswa', help_text="The student who owns this document")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nama_dokumen} ({self.get_bab_display()}) - {self.pemilik.user.get_full_name()}"

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name_plural = "Dokumen"

        # NEW: Add a constraint to prevent duplicate BAB uploads per student
        constraints = [
            UniqueConstraint(
                fields=['pemilik', 'bab'],
                name='unique_bab_per_mahasiswa'
            )
        ]