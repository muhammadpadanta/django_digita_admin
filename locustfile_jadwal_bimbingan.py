# locustfile_jadwal_bimbingan.py
import os
import django
import random
import datetime
from locust import HttpUser, task, between, events

# --- Setup Django Environment ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digita_admin.settings')
django.setup()

from django.contrib.auth.models import User
from users.models import Mahasiswa, Dosen, ProgramStudi, Jurusan
from tugas_akhir.models import TugasAkhir, Ruangan, JadwalBimbingan

# --- Locust User Class ---
class JadwalBimbinganUser(HttpUser):
    """
    Locust user for simulating guidance schedule requests.
    """
    wait_time = between(1, 5)

    def on_start(self):
        """
        Sets up the necessary data for a student to request a guidance schedule.
        - Creates a Dosen.
        - Creates a Mahasiswa.
        - Creates a TugasAkhir instance linking them.
        - Creates a Ruangan (room).
        - Logs in as the Mahasiswa.
        """
        unique_id = random.randint(1000, 9999)
        self.username = f"testuser_jb_{unique_id}"
        self.password = "testpassword"
        self.dosen_username = f"testdosen_jb_{unique_id}"
        self.dosen_password = "testpassword"

        # --- Create Prerequisite Data ---
        self.jurusan, _ = Jurusan.objects.get_or_create(nama_jurusan="Teknik Elektro")
        self.program_studi, _ = ProgramStudi.objects.get_or_create(nama_prodi="Teknik Informatika", jurusan=self.jurusan)
        
        # Create Dosen
        self.user_dosen = User.objects.create_user(username=self.dosen_username, password=self.dosen_password)
        self.dosen = Dosen.objects.create(user=self.user_dosen, nik=f"dosen_nik_{unique_id}", jurusan=self.jurusan)

        # Create Mahasiswa
        self.user_mahasiswa = User.objects.create_user(username=self.username, password=self.password)
        self.mahasiswa = Mahasiswa.objects.create(user=self.user_mahasiswa, nim=f"mhs_nim_{unique_id}", program_studi=self.program_studi)

        # Create TugasAkhir linking Mahasiswa and Dosen
        self.tugas_akhir = TugasAkhir.objects.create(
            mahasiswa=self.mahasiswa,
            dosen_pembimbing=self.dosen,
            judul="Initial Thesis Title",
            deskripsi="Initial thesis description."
        )
        
        # Create a Ruangan
        self.ruangan, _ = Ruangan.objects.get_or_create(nama_ruangan="Ruang Diskusi 1", gedung="Gedung A")

        # --- Login ---
        login_payload = {
            "identifier": self.mahasiswa.nim,
            "password": self.password,
            "role": "mahasiswa"
        }
        response = self.client.post("/api/v1/users/login/", json=login_payload, name="/api/v1/users/login/")
        
        if response.status_code == 200 and response.json().get("data", {}).get("tokens"):
            self.token = response.json()["data"]["tokens"].get("access")
        else:
            self.token = None
            print(f"Login failed for user {self.username}: {response.text}")

    @task
    def create_jadwal_bimbingan(self):
        """
        Task to create a new guidance schedule request.
        """
        if not self.token:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Generate a future date for the request
        future_date = datetime.date.today() + datetime.timedelta(days=random.randint(1, 30))
        
        payload = {
            "judul_bimbingan": "Diskusi Bab 1",
            "tanggal": future_date.strftime("%Y-%m-%d"),
            "waktu": "10:00:00",
            "lokasi_ruangan_id": self.ruangan.id
        }
        
        self.client.post(
            "/api/v1/tugas-akhir/jadwal-bimbingan/",
            json=payload,
            headers=headers,
            name="/api/v1/tugas-akhir/jadwal-bimbingan/"
        )

    def on_stop(self):
        """
        Cleans up all created test data for this user.
        """
        if hasattr(self, 'user_mahasiswa'):
            self.user_mahasiswa.delete()
        if hasattr(self, 'user_dosen'):
            self.user_dosen.delete()
        # Ruangan and other shared objects are not deleted to avoid race conditions,
        # they can be cleaned up globally.

# --- Global Cleanup Hooks ---
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Clean up any leftover data from previous runs before starting.
    """
    print("--- Global Start: Cleaning up leftover test data ---")
    User.objects.filter(username__startswith='testuser_jb_').delete()
    User.objects.filter(username__startswith='testdosen_jb_').delete()
    print("--- Global cleanup complete. Starting test. ---")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Clean up all data at the very end of the test run.
    """
    print("--- Global Stop: Cleaning up all test data ---")
    User.objects.filter(username__startswith='testuser_jb_').delete()
    User.objects.filter(username__startswith='testdosen_jb_').delete()
    Ruangan.objects.filter(nama_ruangan__startswith='Ruang Diskusi').delete()
    print("--- Final global cleanup complete. ---")
