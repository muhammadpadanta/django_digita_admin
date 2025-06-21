# digita_admin/urls.py
from django.urls import path, include
from django.contrib import admin

# Define API v1 URLs in a separate list for clarity
api_v1_patterns = [
    path('users/', include('users.api_urls')),
    path('tugas-akhir/', include('tugas_akhir.urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- WEB PAGE URLS ---
    path('', include('core.urls')),
    path('users/', include('users.urls', namespace='users')),

    # --- API URLS ---
    path('api/v1/', include(api_v1_patterns)),
]