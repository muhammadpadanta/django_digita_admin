from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from .models import Mahasiswa, Dosen

class NimNikAuthBackend(BaseBackend):
    """
    Authenticate using NIM (for Mahasiswa) or NIK (for Dosen).
    """
    def authenticate(self, request, identifier=None, password=None, role=None, **kwargs):
        if role == 'mahasiswa':
            try:
                mahasiswa = Mahasiswa.objects.get(nim=identifier)
                user = mahasiswa.user
            except Mahasiswa.DoesNotExist:
                return None
        elif role == 'dosen':
            try:
                dosen = Dosen.objects.get(nik=identifier)
                user = dosen.user
            except Dosen.DoesNotExist:
                return None
        else:
            return None # Invalid role

        if user.check_password(password):
            return user # Authentication successful
        return None # Wrong password

    def get_user(self, user_id):
        """
        Required method for Django's auth system.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
