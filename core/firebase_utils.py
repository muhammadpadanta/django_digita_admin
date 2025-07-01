# core/firebase_utils.py

import os
import json
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from .models import FCMDevice

# --- Firebase Admin SDK Initialization ---
try:
    SERVICE_ACCOUNT_KEY_PATH = os.path.join(settings.BASE_DIR, 'firebase-service-account-key.json')

    with open(SERVICE_ACCOUNT_KEY_PATH, 'r') as f:
        service_account_info = json.load(f)
        project_id = service_account_info.get('project_id')

    if not firebase_admin._apps:
        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
        firebase_admin.initialize_app(cred, {'projectId': project_id})

    print(f"Firebase Admin SDK initialized successfully for project: {project_id}")

except FileNotFoundError:
    print("CRITICAL: firebase-service-account-key.json not found. Push notifications are disabled.")
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")


def send_notification_to_all_users(title, body, data=None):
    """
    Sends a push notification to all devices by iterating through them.
    This is a debugging alternative to send_multicast.
    """
    if not firebase_admin._apps:
        print("Firebase app not initialized. Cannot send notification.")
        return

    fcm_tokens = list(FCMDevice.objects.values_list('fcm_token', flat=True).distinct())

    if not fcm_tokens:
        print("No FCM tokens found in the database.")
        return

    success_count = 0
    failure_count = 0

    # --- MODIFIED LOGIC: Send notifications one-by-one ---
    for token in fcm_tokens:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data if data else {},
            token=token,
        )

        try:
            # Use the send() method for a single device
            response = messaging.send(message)
            print(f"Successfully sent message to token {token[:10]}... response: {response}")
            success_count += 1
        except Exception as e:
            print(f"Failed to send to token {token[:10]}... Error: {e}")
            failure_count += 1

    print(f"--- Sending Complete ---")
    print(f"Success count: {success_count}")
    print(f"Failure count: {failure_count}")

