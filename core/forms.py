# core/forms.py
from django import forms

class AdminLoginForm(forms.Form):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={'placeholder': 'Masukkan username admin Anda'})
    )
    password = forms.CharField(
        label="Kata Sandi",
        widget=forms.PasswordInput(attrs={'placeholder': 'Masukkan password Anda'})
    )