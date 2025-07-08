# core/firebase_utils.py

import os
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from .models import FCMDevice

# --- Firebase Admin SDK Initialization ---
try:
    SERVICE_ACCOUNT_KEY_PATH = os.path.join(settings.BASE_DIR, 'firebase-service-account-key.json')

    if not firebase_admin._apps:
        # cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
        # firebase_admin.initialize_app(cred)
        cred = credentials.Certificate(
            os.path.join(settings.BASE_DIR, os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
        )
        default_app = firebase_admin.initialize_app(cred)

    project_id = firebase_admin.get_app().project_id
    print(f"Firebase Admin SDK initialized successfully for project: {project_id}")

except FileNotFoundError:
    print("CRITICAL: firebase-service-account-key.json not found. Push notifications are disabled.")
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")


def send_notification_to_all_users(title, body, data=None):
    """
    Sends a data-only push notification to all devices, one by one.
    """
    if not firebase_admin._apps:
        print("Firebase app not initialized. Cannot send notification.")
        return

    fcm_tokens = list(FCMDevice.objects.values_list('fcm_token', flat=True).distinct())

    if not fcm_tokens:
        print("No FCM tokens found in the database.")
        return

    message_data = {'title': title, 'body': body}
    if data:
        message_data.update(data)

    success_count = 0
    failure_count = 0
    tokens_to_delete = []

    for token in fcm_tokens:
        message = messaging.Message(data=message_data, token=token)
        try:
            messaging.send(message)
            success_count += 1
        except messaging.UnregisteredError:
            tokens_to_delete.append(token)
            failure_count += 1
        except Exception as e:
            print(f"Failed to send to token {token[:15]}... Error: {e}")
            failure_count += 1

    if tokens_to_delete:
        FCMDevice.objects.filter(fcm_token__in=tokens_to_delete).delete()

    print(f"--- Sending Complete (All Users) --- Success: {success_count}, Failure: {failure_count}")


def send_notification_to_user(user, title, body, data=None):
    """
    Sends a data-only push notification to all devices for a specific user, one by one.
    """
    if not firebase_admin._apps:
        print("Firebase app not initialized. Cannot send notification.")
        return

    fcm_tokens = list(user.fcm_devices.values_list('fcm_token', flat=True))

    if not fcm_tokens:
        print(f"User {user.username} has no registered FCM tokens.")
        return

    message_data = {'title': title, 'body': body}
    if data:
        message_data.update(data)

    success_count = 0
    failure_count = 0
    tokens_to_delete = []

    for token in fcm_tokens:
        message = messaging.Message(data=message_data, token=token)
        try:
            messaging.send(message)
            success_count += 1
        except messaging.UnregisteredError:
            tokens_to_delete.append(token)
            failure_count += 1
        except Exception as e:
            print(f"Failed to send to user {user.username} with token {token[:15]}... Error: {e}")
            failure_count += 1

    if tokens_to_delete:
        FCMDevice.objects.filter(fcm_token__in=tokens_to_delete).delete()

    print(f"--- Sending Complete (User: {user.username}) --- Success: {success_count}, Failure: {failure_count}")