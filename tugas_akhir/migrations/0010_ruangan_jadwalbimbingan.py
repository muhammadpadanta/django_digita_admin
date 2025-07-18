# Generated by Django 5.2 on 2025-06-27 22:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tugas_akhir", "0009_alter_dokumen_status_alter_requestdosen_status"),
        ("users", "0004_remove_historicalmahasiswa_dosen_pembimbing_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Ruangan",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nama_ruangan", models.CharField(max_length=100, unique=True)),
                ("gedung", models.CharField(blank=True, max_length=100, null=True)),
                (
                    "keterangan",
                    models.TextField(
                        blank=True,
                        help_text="Informasi tambahan seperti kapasitas atau fasilitas.",
                        null=True,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Ruangan",
                "ordering": ["nama_ruangan"],
            },
        ),
        migrations.CreateModel(
            name="JadwalBimbingan",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "judul_bimbingan",
                    models.CharField(
                        help_text="Topik atau judul yang akan dibahas.", max_length=255
                    ),
                ),
                ("tanggal", models.DateField()),
                ("waktu", models.TimeField()),
                (
                    "lokasi_text",
                    models.CharField(
                        help_text="e.g., 'Online via Google Meet' atau nama ruangan jika tidak ada di daftar.",
                        max_length=255,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Menunggu Persetujuan"),
                            ("ACCEPTED", "Disetujui"),
                            ("REJECTED", "Ditolak"),
                            ("DONE", "Selesai"),
                        ],
                        db_index=True,
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                (
                    "alasan_penolakan",
                    models.TextField(
                        blank=True,
                        help_text="Diisi oleh dosen jika permintaan ditolak.",
                        null=True,
                    ),
                ),
                (
                    "catatan_bimbingan",
                    models.TextField(
                        blank=True,
                        help_text="Diisi oleh dosen setelah bimbingan selesai.",
                        null=True,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "dosen_pembimbing",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="jadwal_bimbingan_dosen",
                        to="users.dosen",
                    ),
                ),
                (
                    "mahasiswa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="jadwal_bimbingan",
                        to="users.mahasiswa",
                    ),
                ),
                (
                    "lokasi_ruangan",
                    models.ForeignKey(
                        blank=True,
                        help_text="Pilih ruangan jika bimbingan tatap muka.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="tugas_akhir.ruangan",
                    ),
                ),
            ],
            options={
                "verbose_name": "Jadwal Bimbingan",
                "verbose_name_plural": "Jadwal Bimbingan",
                "ordering": ["-tanggal", "-waktu"],
            },
        ),
    ]
