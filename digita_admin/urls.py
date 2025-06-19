from django.contrib import admin
from django.urls import path, include

# This list defines the URL patterns for the entire project.
urlpatterns = [
    # Maps the '/admin/' URL to the Django admin interface.
    path('admin/', admin.site.urls),

    # Includes all URL patterns from the 'users' application under the 'api/users/' prefix.
    path('api/users/', include('users.urls')),

    # Includes all URL patterns from the 'tugas_akhir' application under the 'api/ta/' prefix.
    path('api/ta/', include('tugas_akhir.urls')),

    path('', include('core.urls')),
]