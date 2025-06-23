# announcements/forms.py

from django import forms
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import Pengumuman
from core.models import ActivityLog
from core.utils import calculate_file_hash

User = get_user_model()

class PengumumanForm(forms.ModelForm):
    """
    Form for creating and updating Pengumuman instances, with built-in
    detailed activity logging.
    """
    def __init__(self, *args, **kwargs):
        # Pop the user from kwargs to store it. We'll need it for the actor.
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Pengumuman #
        fields = ['judul', 'deskripsi', 'tanggal_mulai', 'tanggal_selesai', 'lampiran'] #
        widgets = {
            'judul': forms.TextInput(attrs={'class': 'form-control', 'id': 'ann-title'}), #
            'deskripsi': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'id': 'ann-desc'}), #
            'tanggal_mulai': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'ann-start-date'}), #
            'tanggal_selesai': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'ann-end-date'}), #
            'lampiran': forms.FileInput(attrs={'class': 'file-input', 'id': 'ann-attachment'}), #
        }

    @transaction.atomic
    def save(self, commit=True):
        # Determine the actor. Fallback to a superuser if not provided.
        actor = self.user
        if not actor:
            actor = User.objects.filter(is_superuser=True).first()

        is_new = not self.instance.pk

        # For updates, get the state of the object before any changes.
        if not is_new:
            old_instance = Pengumuman.objects.get(pk=self.instance.pk)

        # Handle file hashing before saving the instance
        attachment = self.cleaned_data.get('lampiran')
        # Check if the file was cleared by the user
        if attachment is False: # False when a user checks the 'clear' checkbox
            self.instance.lampiran_hash = ""
        # If a new file was uploaded, calculate its hash
        elif attachment:
            self.instance.lampiran_hash = calculate_file_hash(attachment)

        # Proceed with saving the Pengumuman instance
        instance = super().save(commit)

        # --- Activity Logging ---
        if is_new:
            verb = "menambahkan pengumuman baru"
            description = f"Menambahkan pengumuman: {instance.judul}"
            ActivityLog.objects.create(actor=actor, verb=verb, target=instance, description=description)
        else:
            changed_fields = []
            if old_instance.judul != instance.judul:
                changed_fields.append(f"Judul: '{old_instance.judul}' -> '{instance.judul}'")
            if old_instance.deskripsi != instance.deskripsi:
                # Truncate the text to keep the log readable
                MAX_LEN = 75
                old_desc = (old_instance.deskripsi[:MAX_LEN] + '...') if len(old_instance.deskripsi) > MAX_LEN else old_instance.deskripsi
                new_desc = (instance.deskripsi[:MAX_LEN] + '...') if len(instance.deskripsi) > MAX_LEN else instance.deskripsi
                changed_fields.append(f"Deskripsi: '{old_desc}' -> '{new_desc}'")
            if old_instance.tanggal_mulai != instance.tanggal_mulai:
                changed_fields.append(f"Tanggal Mulai: '{old_instance.tanggal_mulai}' -> '{instance.tanggal_mulai}'")
            if old_instance.tanggal_selesai != instance.tanggal_selesai:
                changed_fields.append(f"Tanggal Selesai: '{old_instance.tanggal_selesai}' -> '{instance.tanggal_selesai}'")

            if old_instance.lampiran_hash != instance.lampiran_hash:
                old_file = old_instance.lampiran.name.split('/')[-1] if old_instance.lampiran else "Tidak ada"
                new_file = instance.lampiran.name.split('/')[-1] if instance.lampiran else "Tidak ada"
                if old_file != new_file or old_instance.lampiran_hash != instance.lampiran_hash:
                    changed_fields.append(f"Lampiran: '{old_file}' -> '{new_file}'")

            if changed_fields:
                verb = "memperbarui pengumuman"
                details = "; ".join(changed_fields)
                description = f"Memperbarui pengumuman '{instance.judul}': {details}"
                ActivityLog.objects.create(actor=actor, verb=verb, target=instance, description=description)

        return instance