# locustfile_supervision_requests.py
import os
import django
import random
from locust import HttpUser, task, between, events

# --- Setup Django Environment ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digita_admin.settings')
django.setup()

from django.contrib.auth.models import User
from users.models import Mahasiswa, Dosen, ProgramStudi, User, Jurusan
from tugas_akhir.models import RequestDosen

# --- Locust User Class ---
class SupervisionRequestUser(HttpUser):
    """
    Locust user class for simulating supervision request submissions.
    """
    wait_time = between(1, 5)  # Time between consecutive tasks

    def on_start(self):
        """
        Called when a Locust user starts.
        This method creates a new Mahasiswa and a new Dosen for each user.
        """
        # Create unique credentials for each user
        unique_id = random.randint(1000, 9999)
        self.username = f"testuser_{unique_id}"
        self.password = "testpassword"
        self.dosen_username = f"testdosen_{unique_id}"
        self.dosen_password = "testpassword"

        # Create Mahasiswa user
        self.user_mahasiswa = User.objects.create_user(username=self.username, password=self.password, first_name="Test", last_name="User")
        self.jurusan, _ = Jurusan.objects.get_or_create(nama_jurusan="Teknik Elektro")
        self.program_studi, _ = ProgramStudi.objects.get_or_create(nama_prodi="Teknik Informatika", jurusan=self.jurusan)
        self.mahasiswa = Mahasiswa.objects.create(user=self.user_mahasiswa, nim=f"12345{unique_id}", program_studi=self.program_studi)

        # Create Dosen user
        self.user_dosen = User.objects.create_user(username=self.dosen_username, password=self.dosen_password, first_name="Test", last_name="Dosen")
        self.dosen = Dosen.objects.create(user=self.user_dosen, nik=f"54321{unique_id}", jurusan=self.jurusan)

        # Login to get auth token
        login_payload = {
            "identifier": self.mahasiswa.nim,
            "password": self.password,
            "role": "mahasiswa"
        }
        response = self.client.post(
            "/api/v1/users/login/", 
            json=login_payload, 
            name="/api/v1/users/login/"
        )
        
        # Check if login was successful and token exists
        if response.status_code == 200 and response.json().get("data", {}).get("tokens"):
            self.token = response.json()["data"]["tokens"].get("access")
        else:
            self.token = None
            print(f"Login failed for user {self.username} with status {response.status_code}: {response.text}")
            return # Stop if login fails

        # After successful login, immediately create one supervision request
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "dosen_id": self.dosen.user_id,
            "rencana_judul": "Studi Kasus: Pengembangan Sistem A",
            "rencana_deskripsi": "Deskripsi mendalam tentang pengembangan sistem A.",
            "alasan_memilih_dosen": "Keahlian dosen dalam bidang terkait sangat relevan."
        }
        self.client.post(
            "/api/v1/tugas-akhir/supervision-requests/",
            json=payload,
            headers=headers,
            name="/api/v1/tugas-akhir/supervision-requests/"
        )

    @task
    def do_nothing(self):
        """
        This task does nothing, just keeps the user active.
        The actual work is done in on_start.
        """
        pass

    def on_stop(self):
        """
        Called when a Locust user stops.
        This method cleans up the created users and requests.
        """
        # Clean up the created users
        if hasattr(self, 'user_mahasiswa'):
            self.user_mahasiswa.delete()
        if hasattr(self, 'user_dosen'):
            self.user_dosen.delete()

# --- Event Hooks for Global Cleanup ---
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Fixture to run at the beginning of the whole test run.
    """
    print("--- Starting test: Cleaning up any leftover test data ---")
    # Clean up any users that might be left from a previous crashed run
    User.objects.filter(username__startswith='testuser_').delete()
    User.objects.filter(username__startswith='testdosen_').delete()
    print("--- Cleanup complete. Starting locust. ---")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Fixture to run at the end of the whole test run.
    """
    print("--- Test finished: Cleaning up all test data ---")
    # Final cleanup of all test users and related data
    User.objects.filter(username__startswith='testuser_').delete()
    User.objects.filter(username__startswith='testdosen_').delete()
    print("--- Final cleanup complete. ---")
