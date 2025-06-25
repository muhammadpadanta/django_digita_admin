from django import forms
from .models import Dokumen
from django.db import transaction
from core.models import ActivityLog
from django.contrib.auth.models import User
from core.utils import calculate_file_hash
from .models import Dokumen, TugasAkhir, Dosen
from crum import get_current_user


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

class TugasAkhirEditForm(forms.ModelForm):
    """
    Form for editing an existing TugasAkhir instance.
    """
    dosen_pembimbing = forms.ModelChoiceField(
        queryset=Dosen.objects.select_related('user').all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label="Dosen Pembimbing"
    )

    class Meta:
        model = TugasAkhir
        fields = ['judul', 'deskripsi', 'dosen_pembimbing']
        widgets = {
            'judul': forms.TextInput(attrs={'class': 'form-control'}),
            'deskripsi': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.dosen_pembimbing:
            self.fields['dosen_pembimbing'].initial = self.instance.dosen_pembimbing.pk

    @transaction.atomic
    def save(self, commit=True):
        """
        Overrides the default save method to:
        1. Log detailed changes to the ActivityLog.
        2. Update the `dosen_pembimbing` on the related Mahasiswa instance.
        """
        # Get the state of the object BEFORE changes
        old_instance = TugasAkhir.objects.get(pk=self.instance.pk)
        old_details = {
            'Judul': old_instance.judul,
            'Deskripsi': old_instance.deskripsi,
            'Dosen Pembimbing': old_instance.dosen_pembimbing.user.get_full_name() if old_instance.dosen_pembimbing else "Belum Ditentukan"
        }

        # Get the new instance from the form, but don't save to DB yet
        updated_ta = super().save(commit=False)

        # --- MODIFICATION START ---
        # Compare old and new values to build a change description
        changes = []
        new_dosen_name = updated_ta.dosen_pembimbing.user.get_full_name() if updated_ta.dosen_pembimbing else "Belum Ditentukan"

        if old_details['Judul'] != updated_ta.judul:
            changes.append(f"Judul: '{old_details['Judul']}' -> '{updated_ta.judul}'")

        if old_details['Deskripsi'] != updated_ta.deskripsi:
            changes.append("Deskripsi diperbarui.")

        if old_details['Dosen Pembimbing'] != new_dosen_name:
            changes.append(f"Dosen Pembimbing: '{old_details['Dosen Pembimbing']}' -> '{new_dosen_name}'")

        # If there were changes, create a log entry
        if changes:
            actor = get_current_user()
            # Add a fallback if the current user isn't found
            if not actor:
                actor = User.objects.filter(is_superuser=True, is_active=True).first()

            if actor: # This check will now be more reliable
                description = (
                    f"Memperbarui Tugas Akhir '{updated_ta.judul}' milik "
                    f"{updated_ta.mahasiswa.user.get_full_name()}: {'; '.join(changes)}"
                )
                ActivityLog.objects.create(
                    actor=actor,
                    verb="memperbarui tugas akhir",
                    target=updated_ta,
                    description=description
                )

        mahasiswa = updated_ta.mahasiswa
        new_advisor = updated_ta.dosen_pembimbing

        if mahasiswa.dosen_pembimbing != new_advisor:
            mahasiswa.dosen_pembimbing = new_advisor
            if commit:
                mahasiswa.save()

        # Commit all changes to the database
        if commit:
            updated_ta.save()
            self.save_m2m()

        return updated_ta