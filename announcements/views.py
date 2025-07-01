# announcements/views.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, View
from .models import Pengumuman
from .forms import PengumumanForm
from core.firebase_utils import send_notification_to_all_users


class AnnouncementListView(LoginRequiredMixin, ListView):
    model = Pengumuman
    template_name = 'core/announcements.html'
    context_object_name = 'announcements'
    paginate_by = 3

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PengumumanForm()
        return context


class AnnouncementCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = PengumumanForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            announcement = form.save()

            # --- TRIGGER NOTIFICATION ---
            try:
                title = announcement.judul
                body = announcement.deskripsi
                data = {
                    'announcement_id': str(announcement.id),
                    'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                    'screen': 'announcement_detail', # Custom key to tell Flutter where to navigate
                }
                send_notification_to_all_users(title=title, body=body, data=data)
            except Exception as e:
                # Log the error, but don't let it crash the main request
                print(f"Failed to send notification for new announcement: {e}")

            messages.success(request, f"Pengumuman '{announcement.judul}' berhasil dibuat.")
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)


class AnnouncementUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        announcement = get_object_or_404(Pengumuman, pk=pk)
        data = {
            'judul': announcement.judul,
            'deskripsi': announcement.deskripsi,
            'tanggal_mulai': announcement.tanggal_mulai,
            'tanggal_selesai': announcement.tanggal_selesai,
            'lampiran_url': announcement.lampiran.url if announcement.lampiran else ''
        }
        return JsonResponse(data)

    def post(self, request, pk):
        announcement = get_object_or_404(Pengumuman, pk=pk)
        form = PengumumanForm(request.POST, request.FILES, instance=announcement, user=request.user)

        if form.is_valid():
            saved_announcement = form.save()
            messages.success(request, f"Pengumuman '{saved_announcement.judul}' berhasil diperbarui.")
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)


class AnnouncementDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            announcement = Pengumuman.objects.get(pk=pk)
            announcement.delete()
            messages.success(request, f"Pengumuman '{announcement.judul}' telah berhasil dihapus.")
        except Pengumuman.DoesNotExist:
            messages.error(request, "Pengumuman yang ingin Anda hapus tidak ditemukan.")
        return redirect('announcements:list')
