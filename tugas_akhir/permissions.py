from rest_framework import permissions

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
        # Admins can always access
        if request.user and request.user.is_staff:
            return True

        return (
            hasattr(request.user, 'dosen_profile') and
            obj.dosen == request.user.dosen_profile
        )

# Add these two new classes to the end of the file

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
