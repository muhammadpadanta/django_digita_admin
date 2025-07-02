# core/api_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import FCMDevice

class RegisterFCMDeviceView(APIView):
    """
    API view for a logged-in user to register their FCM device token.
    This logic correctly handles multiple devices per user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        fcm_token = request.data.get('fcm_token')

        if not fcm_token:
            return Response(
                {'error': 'An FCM token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        device, created = FCMDevice.objects.update_or_create(
            fcm_token=fcm_token,
            defaults={'user': request.user}
        )

        if created:
            return Response(
                {'status': 'New device registered successfully.'},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'status': 'Existing device re-associated with user.'},
                status=status.HTTP_200_OK
            )