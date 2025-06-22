# announcements/views.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, View
from django.urls import reverse_lazy

from .models import Pengumuman
from .forms import PengumumanForm

class AnnouncementListView(LoginRequiredMixin, ListView):
    """
    Displays a list of all announcements with pagination.
    Also provides the form for the 'Add Announcement' modal.
    """
    model = Pengumuman
    template_name = 'core/announcements.html'
    context_object_name = 'announcements'
    paginate_by = 3

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PengumumanForm()
        return context


class AnnouncementCreateView(LoginRequiredMixin, View):
    """
    Handles the creation of a new announcement via an AJAX POST request.
    """
    def post(self, request, *args, **kwargs):
        form = PengumumanForm(request.POST, request.FILES)
        if form.is_valid():
            announcement = form.save()
            messages.success(request, f"Pengumuman '{announcement.judul}' berhasil dibuat.")
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)


class AnnouncementUpdateView(LoginRequiredMixin, View):
    """
    Handles fetching data for and updating an announcement via AJAX.
    """
    # ... The get method remains the same ...
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
        """Update the announcement."""
        announcement = get_object_or_404(Pengumuman, pk=pk)
        form = PengumumanForm(request.POST, request.FILES, instance=announcement)
        if form.is_valid():
            saved_announcement = form.save()
            messages.success(request, f"Pengumuman '{saved_announcement.judul}' berhasil diperbarui.")
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)


class AnnouncementDeleteView(LoginRequiredMixin, View):
    """
    Handles the deletion of an announcement.
    """
    def post(self, request, pk, *args, **kwargs):
        try:
            announcement = Pengumuman.objects.get(pk=pk)
            announcement.delete()
            messages.success(request, f"Pengumuman '{announcement.judul}' telah berhasil dihapus.")
        except Pengumuman.DoesNotExist:
            messages.error(request, "Pengumuman yang ingin Anda hapus tidak ditemukan.")
        return redirect('announcements:list')