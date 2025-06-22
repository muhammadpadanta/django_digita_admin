# core/views.py
from django.shortcuts import render, redirect
from django.views.generic import FormView, TemplateView, View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth import get_user_model
from .forms import AdminLoginForm
from itertools import chain

from users.models import Mahasiswa, Dosen, User
from tugas_akhir.models import Dokumen
from announcements.models import Pengumuman
from .models import ActivityLog


class HomeView(TemplateView):
    template_name = 'core/home.html'

class LoginView(FormView):
    template_name = 'core/login.html'
    form_class = AdminLoginForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        user = authenticate(self.request, username=username, password=password)

        if user is not None:
            if user.is_staff:
                login(self.request, user)
                return redirect('core:dashboard')
            else:
                messages.error(self.request, "Akun ini tidak memiliki hak akses admin.")
                return self.form_invalid(form)
        else:
            messages.error(self.request, "Username atau password salah. Mohon periksa kembali.")
            return self.form_invalid(form)

class LogoutView(View):
    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect('core:home')

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # --- Data for Stat Cards ---
        context['total_mahasiswa'] = Mahasiswa.objects.count()
        context['total_dosen'] = Dosen.objects.count()
        context['total_dokumen'] = Dokumen.objects.count()

        # --- Data for Recent Announcements Panel ---
        context['recent_announcements'] = Pengumuman.objects.all()[:3]

        # --- Data for Recent Activity Panel ---
        context['recent_activities'] = ActivityLog.objects.select_related('actor').all()[:5]

        return context