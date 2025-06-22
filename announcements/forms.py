# announcements/forms.py

from django import forms
from .models import Pengumuman

class PengumumanForm(forms.ModelForm):
    """
    Form for creating and updating Pengumuman instances.
    """
    class Meta:
        model = Pengumuman
        fields = ['judul', 'deskripsi', 'tanggal_mulai', 'tanggal_selesai', 'lampiran']
        widgets = {
            'judul': forms.TextInput(attrs={'class': 'form-control', 'id': 'ann-title'}),
            'deskripsi': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'id': 'ann-desc'}),
            'tanggal_mulai': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'ann-start-date'}),
            'tanggal_selesai': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'ann-end-date'}),
            'lampiran': forms.FileInput(attrs={'class': 'file-input', 'id': 'ann-attachment'}),
        }
