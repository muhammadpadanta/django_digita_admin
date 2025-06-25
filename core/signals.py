# core/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import ActivityLog
from tugas_akhir.models import Dokumen, TugasAkhir
from announcements.models import Pengumuman
from crum import get_current_user

User = get_user_model()

# --- USER CREATION & DELETION ---
@receiver(post_save, sender=User)
def log_user_creation_activity(sender, instance, created, **kwargs):
    """
    Logs an activity ONLY when a User is CREATED.
    """
    if created:
        # Get the user who performed the action.
        actor = get_current_user()

        # Fallback for actions outside a request (e.g., scripts) or self-signup
        if not actor:
            actor = instance # A user creating their own account is the actor.

        verb = "menambahkan pengguna baru"
        description = f"Menambahkan pengguna baru: {instance.get_full_name()} ({instance.username})"
        ActivityLog.objects.create(
            actor=actor,
            verb=verb,
            target=instance,
            description=description
        )

@receiver(post_delete, sender=User)
def log_user_deletion(sender, instance, **kwargs):
    # Get the user who performed the action (e.g., an admin deleting another user).
    actor = get_current_user()

    # Fallback to a superuser only if no request user can be found.
    if not actor:
        actor = User.objects.filter(is_superuser=True, is_active=True).first()
        if not actor: return # Exit if no actor can be determined.
    description = f"Menghapus pengguna: {instance.get_full_name()} ({instance.username})"
    ActivityLog.objects.create(
        actor=actor,
        verb="menghapus pengguna",
        description=description
    )


# --- OTHER SIGNALS ---

@receiver(post_save, sender=Dokumen)
def log_dokumen_activity(sender, instance, created, **kwargs):
    """
    This signal now ONLY logs the creation of a new document.
    Updates are handled by DokumenEditForm.
    """
    if created:
        actor = instance.pemilik.user
        verb = "mengupload dokumen baru"
        description = f"Mengupload dokumen: {instance.nama_dokumen} ({instance.get_bab_display()})"
        ActivityLog.objects.create(actor=actor, verb=verb, target=instance, description=description)



@receiver(post_delete, sender=Dokumen)
def log_dokumen_deletion(sender, instance, **kwargs):
    actor = instance.pemilik.user
    description = f"Menghapus dokumen: {instance.nama_dokumen} ({instance.get_bab_display()})"
    ActivityLog.objects.create(actor=actor, verb="menghapus dokumen", description=description)


@receiver(post_delete, sender=Pengumuman)
def log_pengumuman_deletion(sender, instance, **kwargs):
    # The file deletion logic for orphaned files
    if instance.lampiran:
        instance.lampiran.delete(save=False)

    # Get the admin/user who deleted the announcement.
    actor = get_current_user()
    if not actor:
        actor = User.objects.filter(is_superuser=True, is_active=True).first()
        if not actor: return

    description = f"Menghapus pengumuman: {instance.judul}"
    ActivityLog.objects.create(actor=actor, verb="menghapus pengumuman", description=description)

@receiver(post_save, sender=TugasAkhir)
def log_tugas_akhir_creation_activity(sender, instance, created, **kwargs):
    """
    Logs an activity ONLY when a TugasAkhir is CREATED.
    Updates should be handled in the form for more detail.
    """
    if created:
        actor = get_current_user()
        if not actor:
            # Fallback to a superuser if the actor isn't in the request context
            actor = User.objects.filter(is_superuser=True, is_active=True).first()
            if not actor: return

        verb = "membuat tugas akhir"
        mahasiswa_name = instance.mahasiswa.user.get_full_name() if instance.mahasiswa else "N/A"
        description = f"Membuat Tugas Akhir baru '{instance.judul}' untuk mahasiswa {mahasiswa_name}"

        ActivityLog.objects.create(
            actor=actor,
            verb=verb,
            target=instance,
            description=description
        )

@receiver(post_delete, sender=TugasAkhir)
def log_tugas_akhir_deletion_activity(sender, instance, **kwargs):
    """
    Logs an activity when a TugasAkhir is DELETED.
    """
    actor = get_current_user()
    if not actor:
        actor = User.objects.filter(is_superuser=True, is_active=True).first()
        if not actor: return

    verb = "menghapus tugas akhir"
    mahasiswa_name = instance.mahasiswa.user.get_full_name() if instance.mahasiswa else "N/A"
    description = f"Menghapus Tugas Akhir '{instance.judul}' milik {mahasiswa_name}"

    ActivityLog.objects.create(
        actor=actor,
        verb=verb,
        # The target object is now gone, so we only save the description
        description=description
    )
