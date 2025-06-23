# users/forms.py

from django import forms
from django.contrib.auth.models import User
from django.db import transaction

from core.models import ActivityLog
from .models import Mahasiswa, Dosen, ProgramStudi, Jurusan

class UserCreationAdminForm(forms.Form):
    """
    Form for creating a new user (Mahasiswa or Dosen) by an admin.
    Handles creation of both the User and their associated profile.
    """
    ROLE_CHOICES = (
        ('mahasiswa', 'Mahasiswa'),
        ('dosen', 'Dosen'),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True, widget=forms.Select(attrs={'class': 'form-select'}))
    nama_lengkap = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput, required=True)

    # Mahasiswa fields
    nim = forms.CharField(max_length=50, required=False)
    program_studi_id = forms.ModelChoiceField(
        queryset=ProgramStudi.objects.all(),
        required=False,
        label="Program Studi",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # Dosen fields
    nik = forms.CharField(max_length=50, required=False)
    jurusan_id = forms.ModelChoiceField(
        queryset=Jurusan.objects.all(),
        required=False,
        label="Jurusan",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean_password2(self):
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password2

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        email = cleaned_data.get('email')

        if email and User.objects.filter(email=email).exists():
            self.add_error('email', 'A user with this email address already exists.')

        if role == 'mahasiswa':
            nim = cleaned_data.get('nim')
            if not nim: self.add_error('nim', 'NIM is required for Mahasiswa.')
            elif User.objects.filter(username=nim).exists(): self.add_error('nim', 'A user with this NIM already exists.')
            if not cleaned_data.get('program_studi_id'): self.add_error('program_studi_id', 'Program Studi is required for Mahasiswa.')

        elif role == 'dosen':
            nik = cleaned_data.get('nik')
            if not nik: self.add_error('nik', 'NIK is required for Dosen.')
            elif User.objects.filter(username=nik).exists(): self.add_error('nik', 'A user with this NIK already exists.')
            if not cleaned_data.get('jurusan_id'): self.add_error('jurusan_id', 'Jurusan is required for Dosen.')

        return cleaned_data

    @transaction.atomic
    def save(self):
        data = self.cleaned_data
        role = data['role']
        username = data['nim'] if role == 'mahasiswa' else data['nik']
        full_name = data['nama_lengkap']
        first_name, last_name = (full_name.split(' ', 1) + [''])[:2] # Safely split name

        user = User.objects.create_user(
            username=username, email=data['email'], password=data['password'],
            first_name=first_name, last_name=last_name
        )

        if role == 'mahasiswa':
            Mahasiswa.objects.create(user=user, nim=data['nim'], program_studi=data['program_studi_id'])
        elif role == 'dosen':
            Dosen.objects.create(user=user, nik=data['nik'], jurusan=data['jurusan_id'])
        return user


class UserEditForm(forms.ModelForm):
    """
    Form for editing an existing user and their profile.
    This form now contains the consolidated logic for detailed activity logging.
    """
    nama_lengkap = forms.CharField(max_length=150, required=True)
    nim = forms.CharField(max_length=50, required=False)
    program_studi = forms.ModelChoiceField(queryset=ProgramStudi.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    nik = forms.CharField(max_length=50, required=False)
    jurusan = forms.ModelChoiceField(queryset=Jurusan.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    dosen_pembimbing = forms.ModelChoiceField(queryset=Dosen.objects.select_related('user'), required=False, empty_label="---------", widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = User
        fields = ['nama_lengkap', 'email', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk: # Ensure instance exists
            self.user = self.instance
            self.is_mahasiswa = hasattr(self.user, 'mahasiswa_profile')
            self.is_dosen = hasattr(self.user, 'dosen_profile')

            self.fields['nama_lengkap'].initial = self.user.get_full_name()

            if self.is_mahasiswa:
                profile = self.user.mahasiswa_profile
                self.fields['nim'].initial = profile.nim
                self.fields['program_studi'].initial = profile.program_studi
                self.fields['dosen_pembimbing'].initial = profile.dosen_pembimbing
                self.fields['nik'].widget = forms.HiddenInput()
                self.fields['jurusan'].widget = forms.HiddenInput()
            elif self.is_dosen:
                profile = self.user.dosen_profile
                self.fields['nik'].initial = profile.nik
                self.fields['jurusan'].initial = profile.jurusan
                self.fields['nim'].widget = forms.HiddenInput()
                self.fields['program_studi'].widget = forms.HiddenInput()
                self.fields['dosen_pembimbing'].widget = forms.HiddenInput()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def clean_nim(self):
        nim = self.cleaned_data.get('nim')
        if hasattr(self.instance, 'mahasiswa_profile') and nim and User.objects.filter(username=nim).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('A user with this NIM already exists.')
        return nim

    def clean_nik(self):
        nik = self.cleaned_data.get('nik')
        if hasattr(self.instance, 'dosen_profile') and nik and User.objects.filter(username=nik).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('A user with this NIK already exists.')
        return nik

    @transaction.atomic
    def save(self, commit=True):
        actor = User.objects.filter(is_superuser=True).first()
        if not self.instance.pk: return super().save(commit)

        old_user = User.objects.select_related('mahasiswa_profile', 'dosen_profile').get(pk=self.instance.pk)

        changes = []
        old_details = {
            'Nama Lengkap': old_user.get_full_name(),
            'Email': old_user.email,
            'Status Aktif': old_user.is_active,
        }
        if hasattr(old_user, 'mahasiswa_profile'):
            old_details['NIM'] = old_user.mahasiswa_profile.nim
            old_details['Program Studi'] = str(old_user.mahasiswa_profile.program_studi)
            old_details['Dosen Pembimbing'] = str(old_user.mahasiswa_profile.dosen_pembimbing) if old_user.mahasiswa_profile.dosen_pembimbing else None
        elif hasattr(old_user, 'dosen_profile'):
            old_details['NIK'] = old_user.dosen_profile.nik
            old_details['Jurusan'] = str(old_user.dosen_profile.jurusan)

        user = super().save(commit=False)
        full_name = self.cleaned_data['nama_lengkap']
        user.first_name, user.last_name = (full_name.split(' ', 1) + [''])[:2]
        user.is_active = self.cleaned_data['is_active']

        if hasattr(user, 'mahasiswa_profile'):
            user.username = self.cleaned_data['nim']
            profile = user.mahasiswa_profile
            profile.nim = self.cleaned_data['nim']
            profile.program_studi = self.cleaned_data['program_studi']
            profile.dosen_pembimbing = self.cleaned_data.get('dosen_pembimbing')
            if commit: profile.save()
        elif hasattr(user, 'dosen_profile'):
            user.username = self.cleaned_data['nik']
            profile = user.dosen_profile
            profile.nik = self.cleaned_data['nik']
            profile.jurusan = self.cleaned_data['jurusan']
            if commit: profile.save()

        if commit: user.save()

        new_details = {
            'Nama Lengkap': self.cleaned_data['nama_lengkap'],
            'Email': self.cleaned_data['email'],
            'Status Aktif': self.cleaned_data['is_active'],
        }
        if hasattr(user, 'mahasiswa_profile'):
            new_details['NIM'] = self.cleaned_data['nim']
            new_details['Program Studi'] = str(self.cleaned_data['program_studi'])
            new_details['Dosen Pembimbing'] = str(self.cleaned_data.get('dosen_pembimbing')) if self.cleaned_data.get('dosen_pembimbing') else None
        elif hasattr(user, 'dosen_profile'):
            new_details['NIK'] = self.cleaned_data['nik']
            new_details['Jurusan'] = str(self.cleaned_data['jurusan'])

        for key, old_value in old_details.items():
            new_value = new_details.get(key)
            if str(old_value) != str(new_value):
                changes.append(f"{key}: '{old_value}' -> '{new_value}'")

        if changes and actor:
            description = f"Memperbarui data untuk {user.get_full_name()}: {'; '.join(changes)}"
            ActivityLog.objects.create(actor=actor, verb="memperbarui profil pengguna", target=user, description=description)

        return user
