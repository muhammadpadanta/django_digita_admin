# announcements/admin.py

from django.contrib import admin
from .models import Pengumuman

@admin.register(Pengumuman)
class PengumumanAdmin(admin.ModelAdmin):
    """
    Customizes the display of the Pengumuman model in the Django admin.
    """
    list_display = ('judul', 'tanggal_mulai', 'tanggal_selesai', 'created_at')
    list_filter = ('tanggal_mulai', 'tanggal_selesai')
    search_fields = ('judul', 'deskripsi')
    ordering = ('-tanggal_mulai',)

    fieldsets = (
        (None, {
            'fields': ('judul', 'deskripsi')
        }),
        ('Periode Aktif', {
            'fields': ('tanggal_mulai', 'tanggal_selesai')
        }),
        ('Lampiran', {
            'fields': ('lampiran',)
        }),
    )