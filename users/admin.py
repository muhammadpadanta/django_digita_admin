# users/admin.py
from django.contrib import admin
from .models import Jurusan, ProgramStudi, Mahasiswa, Dosen

admin.site.register(Jurusan)
admin.site.register(ProgramStudi)
admin.site.register(Mahasiswa)
admin.site.register(Dosen)
