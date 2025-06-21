from django import forms
from .models import Dokumen

class DokumenEditForm(forms.ModelForm):
    class Meta:
        model = Dokumen
        fields = ['tugas_akhir', 'bab', 'nama_dokumen', 'file', 'status', 'pemilik']
        widgets = {
            'tugas_akhir': forms.Select(attrs={'class': 'form-control'}),
            'bab': forms.Select(attrs={'class': 'form-control'}),
            'nama_dokumen': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'pemilik': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        """
        Custom validation to check for duplicate BAB uploads for the same student.
        """
        cleaned_data = super().clean()
        bab = cleaned_data.get("bab")
        pemilik = cleaned_data.get("pemilik")

        # self.instance is the original document object we are editing.
        # We only want to check for duplicates on *other* documents.
        if bab and pemilik:
            query = Dokumen.objects.filter(pemilik=pemilik, bab=bab)

            # If we are editing an existing document, exclude it from the check
            if self.instance and self.instance.pk:
                query = query.exclude(pk=self.instance.pk)

            if query.exists():
                # If a document with the same BAB and owner already exists, raise an error.
                self.add_error('bab', 'Mahasiswa ini sudah pernah mengunggah dokumen untuk BAB ini.')

        return cleaned_data