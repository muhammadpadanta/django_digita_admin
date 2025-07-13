# tugas_akhir/test_api.py
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from users.models import Jurusan, ProgramStudi, Dosen, Mahasiswa
from .models import TugasAkhir, RequestDosen, Dokumen, JadwalBimbingan, Ruangan
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch

pytestmark = pytest.mark.django_db

# --- Fixtures ---

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def jurusan():
    return Jurusan.objects.create(nama_jurusan='Teknik Informatika')

@pytest.fixture
def prodi(jurusan):
    return ProgramStudi.objects.create(nama_prodi='S1 Informatika', jurusan=jurusan)

@pytest.fixture
def dosen_user():
    return User.objects.create_user(username='dosen_test', password='password', first_name='Candra', last_name='Naya')

@pytest.fixture
def dosen(dosen_user, jurusan):
    dosen_profile, _ = Dosen.objects.get_or_create(user=dosen_user, nik='67890', jurusan=jurusan)
    return dosen_profile

@pytest.fixture
def mahasiswa_user():
    return User.objects.create_user(username='mahasiswa_test', password='password', first_name='Dian', last_name='Sastro')

@pytest.fixture
def mahasiswa(mahasiswa_user, prodi):
    mahasiswa_profile, _ = Mahasiswa.objects.get_or_create(user=mahasiswa_user, nim='09876', program_studi=prodi)
    return mahasiswa_profile

@pytest.fixture
def another_dosen_user():
    return User.objects.create_user(username='dosen_another', password='password', first_name='Eka', last_name='Kurniawan')

@pytest.fixture
def another_dosen(another_dosen_user, jurusan):
    return Dosen.objects.create(user=another_dosen_user, nik='11122', jurusan=jurusan)

@pytest.fixture
def tugas_akhir(mahasiswa, dosen):
    return TugasAkhir.objects.create(mahasiswa=mahasiswa, dosen_pembimbing=dosen, judul="Analisis Sentimen")

@pytest.fixture
def ruangan():
    return Ruangan.objects.create(nama_ruangan="Ruang Diskusi 3", gedung="Perpustakaan")

@pytest.fixture
def dummy_file():
    return SimpleUploadedFile("test_doc.pdf", b"file_content", content_type="application/pdf")


# --- API Test Classes ---

class TestSupervisionRequestAPI:
    def test_mahasiswa_create_supervision_request_success(self, api_client, mahasiswa, dosen):
        # This test assumes the mahasiswa does not have a TugasAkhir object yet
        # To ensure that, if a TA was created by another fixture, we remove it.
        TugasAkhir.objects.filter(mahasiswa=mahasiswa).delete()

        api_client.force_authenticate(user=mahasiswa.user)
        url = reverse('supervision-request-list-create')
        data = {
            'dosen_id': dosen.pk,
            'rencana_judul': 'Judul Baru',
            'rencana_deskripsi': 'Deskripsi Baru',
            'alasan_memilih_dosen': 'Karena ahli di bidangnya'
        }
        with patch('core.firebase_utils.send_notification_to_user'):
            response = api_client.post(url, data, format='json')
            assert response.status_code == status.HTTP_201_CREATED

    def test_dosen_list_pending_requests(self, api_client, dosen_user, mahasiswa, dosen, another_dosen):
        RequestDosen.objects.create(mahasiswa=mahasiswa, dosen=dosen, status='PENDING', rencana_judul="Test", rencana_deskripsi="Test")
        # Create a second request for the same student to a different dosen to ensure filtering works
        RequestDosen.objects.create(mahasiswa=mahasiswa, dosen=another_dosen, status='ACCEPTED', rencana_judul="Test 2", rencana_deskripsi="Test 2")
        
        api_client.force_authenticate(user=dosen_user)
        url = reverse('supervision-request-list-create')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['status'] == 'PENDING'

    def test_dosen_respond_to_request_accept(self, api_client, dosen_user, mahasiswa, dosen):
        request_obj = RequestDosen.objects.create(mahasiswa=mahasiswa, dosen=dosen, status='PENDING', rencana_judul="Test", rencana_deskripsi="Test")
        api_client.force_authenticate(user=dosen_user)
        url = reverse('supervision-request-detail-update', kwargs={'pk': request_obj.pk})
        data = {'status': 'ACCEPTED'}
        with patch('core.firebase_utils.send_notification_to_user'):
            response = api_client.patch(url, data, format='json')
            assert response.status_code == status.HTTP_200_OK
            assert response.data['status'] == 'ACCEPTED'
            assert TugasAkhir.objects.filter(mahasiswa=mahasiswa).exists()

class TestDokumenAPI:
    def test_mahasiswa_upload_document_success(self, api_client, mahasiswa, tugas_akhir, dummy_file):
        api_client.force_authenticate(user=mahasiswa.user)
        url = reverse('dokumen-api-list')
        data = {
            'bab': 'BAB I',
            'nama_dokumen': 'My First Chapter',
            'file': dummy_file
        }
        with patch('core.firebase_utils.send_notification_to_user'):
            response = api_client.post(url, data, format='multipart')
            assert response.status_code == status.HTTP_201_CREATED
            assert Dokumen.objects.filter(pemilik=mahasiswa).count() == 1

    def test_dosen_list_supervised_student_documents(self, api_client, dosen_user, tugas_akhir, mahasiswa):
        Dokumen.objects.create(tugas_akhir=tugas_akhir, pemilik=mahasiswa, bab='BAB I', nama_dokumen='Doc 1')
        api_client.force_authenticate(user=dosen_user)
        url = reverse('dokumen-api-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_dosen_update_document_status(self, api_client, dosen_user, tugas_akhir, mahasiswa):
        doc = Dokumen.objects.create(tugas_akhir=tugas_akhir, pemilik=mahasiswa, bab='BAB I', nama_dokumen='Doc 1')
        api_client.force_authenticate(user=dosen_user)
        url = reverse('dokumen-api-update-status', kwargs={'pk': doc.pk})
        data = {'status': 'Disetujui'}
        with patch('core.firebase_utils.send_notification_to_user'):
            response = api_client.patch(url, data, format='json')
            assert response.status_code == status.HTTP_200_OK
            assert response.data['status'] == 'Disetujui'

    def test_dosen_update_document_status_revisi_requires_catatan(self, api_client, dosen_user, tugas_akhir, mahasiswa):
        doc = Dokumen.objects.create(tugas_akhir=tugas_akhir, pemilik=mahasiswa, bab='BAB I', nama_dokumen='Doc 1')
        api_client.force_authenticate(user=dosen_user)
        url = reverse('dokumen-api-update-status', kwargs={'pk': doc.pk})
        data = {'status': 'Revisi', 'catatan_revisi': ''} # Missing catatan
        response = api_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

class TestJadwalBimbinganAPI:
    def test_mahasiswa_create_jadwal_success(self, api_client, mahasiswa, tugas_akhir, ruangan):
        api_client.force_authenticate(user=mahasiswa.user)
        url = reverse('jadwal-bimbingan-api-list')
        data = {
            'judul_bimbingan': 'Pembahasan Progres',
            'tanggal': (timezone.now() + timezone.timedelta(days=3)).strftime('%Y-%m-%d'),
            'waktu': '10:00:00',
            'lokasi_ruangan_id': ruangan.pk
        }
        with patch('core.firebase_utils.send_notification_to_user'):
            response = api_client.post(url, data, format='json')
            assert response.status_code == status.HTTP_201_CREATED
            assert JadwalBimbingan.objects.count() == 1

    def test_dosen_respond_to_jadwal_accept(self, api_client, dosen_user, mahasiswa, dosen, ruangan):
        jadwal = JadwalBimbingan.objects.create(
            mahasiswa=mahasiswa, dosen_pembimbing=dosen, judul_bimbingan="Test",
            tanggal=timezone.now().date(), waktu='10:00', lokasi_ruangan=ruangan, lokasi_text="-"
        )
        api_client.force_authenticate(user=dosen_user)
        url = reverse('jadwal-bimbingan-api-respond', kwargs={'pk': jadwal.pk})
        data = {'status': 'ACCEPTED'}
        with patch('core.firebase_utils.send_notification_to_user'):
            response = api_client.patch(url, data, format='json')
            assert response.status_code == status.HTTP_200_OK
            assert response.data['status'] == 'ACCEPTED'

    def test_dosen_complete_jadwal_success(self, api_client, dosen_user, mahasiswa, dosen, ruangan):
        jadwal = JadwalBimbingan.objects.create(
            mahasiswa=mahasiswa, dosen_pembimbing=dosen, judul_bimbingan="Test",
            tanggal=timezone.now().date(), waktu='10:00', lokasi_ruangan=ruangan, lokasi_text="-", status='ACCEPTED'
        )
        api_client.force_authenticate(user=dosen_user)
        url = reverse('jadwal-bimbingan-api-complete', kwargs={'pk': jadwal.pk})
        data = {'catatan_bimbingan': 'Sudah bagus, lanjutkan.'}
        with patch('core.firebase_utils.send_notification_to_user'):
            response = api_client.patch(url, data, format='json')
            assert response.status_code == status.HTTP_200_OK
            assert response.data['status'] == 'DONE'
            assert response.data['catatan_bimbingan'] == 'Sudah bagus, lanjutkan.'
