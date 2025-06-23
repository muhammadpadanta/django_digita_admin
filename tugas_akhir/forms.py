from django import forms
from .models import Dokumen
from django.db import transaction
from core.models import ActivityLog
from django.contrib.auth.models import User
from .utils import calculate_file_hash


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

        if bab and pemilik:
            query = Dokumen.objects.filter(pemilik=pemilik, bab=bab)
            if self.instance and self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                self.add_error('bab', 'Mahasiswa ini sudah pernah mengunggah dokumen untuk BAB ini.')
        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        if not self.instance.pk:
            return super().save(commit)

        actor = User.objects.filter(is_superuser=True).first()
        old_dokumen = Dokumen.objects.select_related('pemilik__user').get(pk=self.instance.pk)
        updated_dokumen = super().save(commit=False)

        changes = []

        # File change logic using hashing
        old_hash = old_dokumen.file_hash
        new_hash = old_hash
        newly_uploaded_file = self.cleaned_data.get('file')
        file_was_cleared = self.cleaned_data.get('file-clear', False)

        if newly_uploaded_file:
            new_hash = calculate_file_hash(newly_uploaded_file)
        elif file_was_cleared:
            new_hash = ""

        if old_hash != new_hash:
            updated_dokumen.file_hash = new_hash
            old_filename = old_dokumen.file.name.split('/')[-1] if old_dokumen.file else "No File"
            new_filename = updated_dokumen.file.name.split('/')[-1] if updated_dokumen.file else "No File"
            changes.append(f"File: '{old_filename}' -> '{new_filename}'")

        # Logic for other fields
        old_details = {
            'Bab': old_dokumen.get_bab_display(),
            'Nama Dokumen': old_dokumen.nama_dokumen,
            'Status': old_dokumen.get_status_display(),
            'Pemilik': old_dokumen.pemilik.user.get_full_name(),
        }
        new_details = {
            'Bab': updated_dokumen.get_bab_display(),
            'Nama Dokumen': updated_dokumen.nama_dokumen,
            'Status': updated_dokumen.get_status_display(),
            'Pemilik': updated_dokumen.pemilik.user.get_full_name(),
        }

        for key, old_value in old_details.items():
            new_value = new_details.get(key)
            if str(old_value) != str(new_value):
                changes.append(f"{key}: '{old_value}' -> '{new_value}'")

        # Create log and commit
        if changes and actor:
            description = (f"Memperbarui dokumen {old_dokumen.get_bab_display()} "
                           f"milik {old_dokumen.pemilik.user.get_full_name()}: {'; '.join(changes)}")
            ActivityLog.objects.create(
                actor=actor, verb="memperbarui dokumen",
                target=updated_dokumen, description=description
            )

        if commit:
            updated_dokumen.save()
            self.save_m2m()

        return updated_dokumen


# --- Form for creating documents ---
# This form was already correct, with its save method properly indented.
class DokumenCreateForm(forms.ModelForm):
    class Meta:
        model = Dokumen
        fields = ['tugas_akhir', 'bab', 'nama_dokumen', 'file', 'pemilik']
        widgets = {
            'tugas_akhir': forms.Select(attrs={'class': 'form-select'}),
            'bab': forms.Select(attrs={'class': 'form-select'}),
            'nama_dokumen': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'pemilik': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        """
        Custom validation to check for duplicate BAB uploads for a new document.
        """
        cleaned_data = super().clean()
        bab = cleaned_data.get("bab")
        pemilik = cleaned_data.get("pemilik")

        if bab and pemilik:
            if Dokumen.objects.filter(pemilik=pemilik, bab=bab).exists():
                self.add_error('bab', 'Mahasiswa ini sudah pernah mengunggah dokumen untuk BAB ini.')

        return cleaned_data

    def save(self, commit=True):
        # Calculate hash on creation
        instance = super().save(commit=False)
        if instance.file:
            instance.file_hash = calculate_file_hash(instance.file)

        if commit:
            instance.save()
            self.save_m2m()

        return instance