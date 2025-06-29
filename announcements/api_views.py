# announcements/api_views.py

from django.http import JsonResponse
from django.views import View

from .models import Pengumuman

class PengumumanAPIListView(View):
    """
    API view to get a list of all announcements for the mobile app.
    """
    def get(self, request, *args, **kwargs):
        # Using .order_by('-tanggal_mulai') to ensure the newest come first
        announcements = Pengumuman.objects.order_by('-tanggal_mulai').values(
            'id',
            'judul',
            'deskripsi',
            'tanggal_mulai',
            'tanggal_selesai',
            'lampiran'
        )
        data = list(announcements)

        for announcement_data in data:
            if announcement_data['lampiran']:
                # Retrieve the full object to get the correct URL
                pengumuman_obj = Pengumuman.objects.get(id=announcement_data['id'])
                announcement_data['lampiran_url'] = request.build_absolute_uri(pengumuman_obj.lampiran.url)
            else:
                announcement_data['lampiran_url'] = None

        return JsonResponse(data, safe=False)


class PengumumanAPIDetailView(View):
    """
    API view to get the details of a single announcement for the mobile app.
    """
    def get(self, request, pk, *args, **kwargs):
        try:
            announcement = Pengumuman.objects.get(pk=pk)
            data = {
                'id': announcement.id,
                'judul': announcement.judul,
                'deskripsi': announcement.deskripsi,
                'tanggal_mulai': announcement.tanggal_mulai,
                'tanggal_selesai': announcement.tanggal_selesai,
                'lampiran_url': request.build_absolute_uri(announcement.lampiran.url) if announcement.lampiran else None,
                'created_at': announcement.created_at,
                'updated_at': announcement.updated_at,
            }
            return JsonResponse(data)
        except Pengumuman.DoesNotExist:
            return JsonResponse({'error': 'Pengumuman not found'}, status=404)
