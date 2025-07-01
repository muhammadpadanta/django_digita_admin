# core/models.py
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class ActivityLog(models.Model):
    """
    A log of user actions across the application.
    """
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="The user who performed the action."
    )
    verb = models.CharField(
        max_length=255,
        help_text="The action performed, e.g., 'created', 'uploaded', 'updated'."
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL, # Use SET_NULL
        null=True,                 # Allow null in the database
        blank=True                 # Allow blank in forms/admin
    )
    object_id = models.PositiveIntegerField(
        null=True,                 # Allow null in the database
        blank=True                 # Allow blank in forms/admin
    )
    target = GenericForeignKey('content_type', 'object_id')

    description = models.TextField(
        blank=True, null=True,
        help_text="A human-readable description of the action."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"

    def __str__(self):
        if self.target:
            return f"{self.actor.username} {self.verb} {self.target}"
        return f"{self.actor.username} {self.verb}"

class FCMDevice(models.Model):
    """
    Represents a device registered for Firebase Cloud Messaging.
    Links a user to a specific device token.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fcm_devices',
        help_text="The user associated with this device."
    )
    fcm_token = models.CharField(
        max_length=255,
        unique=True,
        help_text="Firebase Cloud Messaging device token."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "FCM Device"
        verbose_name_plural = "FCM Devices"
        ordering = ['-created_at']

    def __str__(self):
        return f"Device for {self.user.username}"
