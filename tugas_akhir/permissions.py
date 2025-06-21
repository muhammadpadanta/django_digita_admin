from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS

class IsMahasiswa(permissions.BasePermission):
    """Allows access only to authenticated users with a Mahasiswa profile."""
    message = "Akses hanya untuk Mahasiswa."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'mahasiswa_profile')

class IsDosen(permissions.BasePermission):
    """Allows access only to authenticated users with a Dosen profile."""
    message = "Akses hanya untuk Dosen."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'dosen_profile')

class IsRequestRecipientOrAdmin(permissions.BasePermission):
    """
    Allows access only to the Dosen the request was sent to, or admin users.
    Assumes the object being checked is a RequestDosen instance.
    """
    message = "Anda tidak memiliki izin untuk merespon permintaan ini."

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        return (
                hasattr(request.user, 'dosen_profile') and
                obj.dosen == request.user.dosen_profile
        )

class IsMahasiswaOrDosen(permissions.BasePermission):
    """
    Allows access only to users who are either a Mahasiswa or a Dosen.
    """
    message = "Akses hanya untuk Mahasiswa atau Dosen."

    def has_permission(self, request, view):
        is_authenticated = request.user and request.user.is_authenticated
        is_mahasiswa = hasattr(request.user, 'mahasiswa_profile')
        is_dosen = hasattr(request.user, 'dosen_profile')
        return is_authenticated and (is_mahasiswa or is_dosen)

class IsOwnerOrRecipient(permissions.BasePermission):
    """
    Allows read access to the Mahasiswa who sent the request or the Dosen who received it.
    """
    message = "Anda tidak memiliki izin untuk melihat permintaan ini."

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        is_owner = (
                hasattr(request.user, 'mahasiswa_profile') and
                obj.mahasiswa == request.user.mahasiswa_profile
        )
        is_recipient = (
                hasattr(request.user, 'dosen_profile') and
                obj.dosen == request.user.dosen_profile
        )
        return is_owner or is_recipient

# --- NEW PERMISSIONS FOR DOKUMEN ---

class IsDokumenOwner(permissions.BasePermission):
    """
    Custom permission to only allow the owner (Mahasiswa) of a document to edit or delete it.
    Assumes the model instance has a `pemilik` attribute.
    """
    message = "Anda bukan pemilik dokumen ini."

    def has_object_permission(self, request, view, obj):
        if not hasattr(request.user, 'mahasiswa_profile'):
            return False
        return obj.pemilik == request.user.mahasiswa_profile

class IsSupervisingDosen(permissions.BasePermission):
    """
    Custom permission to only allow the supervising Dosen to perform an action.
    This is used for actions like updating a document's status.
    """
    message = "Anda bukan dosen pembimbing untuk mahasiswa pemilik dokumen ini."

    def has_object_permission(self, request, view, obj):
        if not hasattr(request.user, 'dosen_profile'):
            return False
        # The document is linked to TugasAkhir, which has the dosen_pembimbing.
        return obj.tugas_akhir.dosen_pembimbing == request.user.dosen_profile

class IsOwnerOrSupervisingDosen(permissions.BasePermission):
    """
    Allows access if the user is the owner (Mahasiswa) or the supervising Dosen.
    This is mainly used for read-only access to a document's details.
    """
    message = "Anda tidak memiliki izin untuk melihat dokumen ini."

    def has_object_permission(self, request, view, obj):
        is_owner = False
        if hasattr(request.user, 'mahasiswa_profile'):
            is_owner = (obj.pemilik == request.user.mahasiswa_profile)

        is_supervisor = False
        if hasattr(request.user, 'dosen_profile'):
            is_supervisor = (obj.tugas_akhir.dosen_pembimbing == request.user.dosen_profile)

        return is_owner or is_supervisor
