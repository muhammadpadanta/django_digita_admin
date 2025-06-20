# core/views.py
from django.shortcuts import render, redirect
from django.views.generic import FormView, TemplateView, View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .forms import AdminLoginForm
from django.contrib.auth.models import User

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
        user = self.request.user
        context['nama_lengkap'] = user.get_full_name() or user.username

        if user.is_superuser:
            context['role'] = 'Superuser'
        elif user.is_staff:
            context['role'] = 'Staff'

        return context


class UserManagementView(LoginRequiredMixin, TemplateView):
    template_name = 'core/user_management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get the active tab from the URL query parameter (e.g., /users?tab=mahasiswa)
        active_tab = self.request.GET.get('tab', 'semua') # Default to 'semua'


        if active_tab == 'mahasiswa':
            # This assumes you have a related profile with a 'role' field.
            # Adapt this query to your models.
            users_list = User.objects.filter(userprofile__role='mahasiswa').select_related('userprofile')
        elif active_tab == 'dosen':
            users_list = User.objects.filter(userprofile__role='dosen').select_related('userprofile')
        else:
            # 'Semua User' tab shows all non-superuser accounts
            users_list = User.objects.filter(is_superuser=False)

        context['users'] = users_list
        context['active_tab'] = active_tab
        return context


class DocumentsView(LoginRequiredMixin, TemplateView):
    template_name = 'core/documents.html'

class AnnouncementsView(LoginRequiredMixin, TemplateView):
    template_name = 'core/announcements.html'