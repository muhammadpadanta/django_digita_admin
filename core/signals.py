# core/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import ActivityLog
from tugas_akhir.models import Dokumen
from announcements.models import Pengumuman

User = get_user_model()

# --- USER CREATION & DELETION ---
@receiver(post_save, sender=User)
def log_user_creation_activity(sender, instance, created, **kwargs):
    """
    Logs an activity ONLY when a User is CREATED.
    """
    if created:
        # Use the superuser as the actor, or whoever is logged in.
        actor = User.objects.filter(is_superuser=True).first()
        if not actor:
            return

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
    actor = User.objects.filter(is_superuser=True).first()
    if not actor: return
    description = f"Menghapus pengguna: {instance.get_full_name()} ({instance.username})"
    ActivityLog.objects.create(
        actor=actor,
        verb="menghapus pengguna",
        description=description
    )


# --- OTHER SIGNALS ---

@receiver(post_save, sender=Dokumen)
def log_dokumen_activity(sender, instance, created, update_fields, **kwargs):
    actor = instance.pemilik.user
    if created:
        verb = "mengupload dokumen baru"
        description = f"Mengupload dokumen: {instance.get_bab_display()}"
    else:
        verb = "memperbarui dokumen"
        description = f"Memperbarui dokumen: {instance.get_bab_display()}" # Simplified for consistency
    ActivityLog.objects.create(actor=actor, verb=verb, target=instance, description=description)


@receiver(post_save, sender=Pengumuman)
def log_pengumuman_activity(sender, instance, created, **kwargs):
    actor = User.objects.filter(is_superuser=True).first()
    if not actor: return
    if created:
        verb = "menambahkan pengumuman baru"
        description = f"Menambahkan pengumuman: {instance.judul}"
    else:
        verb = "memperbarui pengumuman"
        description = f"Memperbarui pengumuman: {instance.judul}"
    ActivityLog.objects.create(actor=actor, verb=verb, target=instance, description=description)


@receiver(post_delete, sender=Dokumen)
def log_dokumen_deletion(sender, instance, **kwargs):
    actor = instance.pemilik.user
    description = f"Menghapus dokumen: {instance.nama_dokumen} ({instance.get_bab_display()})"
    ActivityLog.objects.create(actor=actor, verb="menghapus dokumen", description=description)


@receiver(post_delete, sender=Pengumuman)
def log_pengumuman_deletion(sender, instance, **kwargs):
    actor = User.objects.filter(is_superuser=True).first()
    description = f"Menghapus pengumuman: {instance.judul}"
    if actor:
        ActivityLog.objects.create(actor=actor, verb="menghapus pengumuman", description=description)