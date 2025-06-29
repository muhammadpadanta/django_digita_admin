from django.contrib import admin
from .models import Dokumen, TugasAkhir, RequestDosen, Ruangan, JadwalBimbingan

admin.site.register(Dokumen)
admin.site.register(TugasAkhir)
admin.site.register(RequestDosen)
admin.site.register(Ruangan)
admin.site.register(JadwalBimbingan)