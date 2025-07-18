# digita_admin/urls.py
from django.conf import settings
from django.urls import path, include
from django.contrib import admin
from django.conf.urls.static import static

api_v1_patterns = [
    path('users/', include('users.api_urls')),
    path('tugas-akhir/', include('tugas_akhir.api_urls')),
    path('announcements/', include('announcements.api_urls')),
    path('core/', include('core.api_urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- WEB PAGE URLS ---
    # These are your standard, browser-accessible pages
    path('', include('core.urls')),
    path('users/', include('users.urls', namespace='users')),
    path('tugas-akhir/', include('tugas_akhir.urls', namespace='tugas_akhir')),
    path('announcements/', include('announcements.urls', namespace='announcements')),

    # --- API URLS ---
    # All API endpoints are now cleanly nested under /api/v1/
    path('api/v1/', include(api_v1_patterns)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)