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
