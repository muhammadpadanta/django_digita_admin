# locustfile_dokumen_upload.py
import os
import django
import random
import io
from locust import HttpUser, task, between, events

# --- Setup Django Environment ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digita_admin.settings')
django.setup()

from django.contrib.auth.models import User
from users.models import Mahasiswa, Dosen, ProgramStudi, Jurusan
from tugas_akhir.models import TugasAkhir, Dokumen

# --- Locust User Class ---
class DokumenUploadUser(HttpUser):
    """
    Locust user for simulating document uploads.
    """
    wait_time = between(1, 5)

    def on_start(self):
        """
        Sets up the necessary data for a student to upload a document.
        - Creates a Dosen and a Mahasiswa.
        - Creates a TugasAkhir instance linking them.
        - Logs in as the Mahasiswa.
        """
        unique_id = random.randint(1000, 9999)
        self.username = f"testuser_doc_{unique_id}"
        self.password = "testpassword"
        self.dosen_username = f"testdosen_doc_{unique_id}"
        self.dosen_password = "testpassword"

        # --- Create Prerequisite Data ---
        self.jurusan, _ = Jurusan.objects.get_or_create(nama_jurusan="Teknik Elektro")
        self.program_studi, _ = ProgramStudi.objects.get_or_create(nama_prodi="Teknik Informatika", jurusan=self.jurusan)
        
        self.user_dosen = User.objects.create_user(username=self.dosen_username, password=self.dosen_password)
        self.dosen = Dosen.objects.create(user=self.user_dosen, nik=f"dosen_nik_doc_{unique_id}", jurusan=self.jurusan)

        self.user_mahasiswa = User.objects.create_user(username=self.username, password=self.password)
        self.mahasiswa = Mahasiswa.objects.create(user=self.user_mahasiswa, nim=f"mhs_nim_doc_{unique_id}", program_studi=self.program_studi)

        self.tugas_akhir = TugasAkhir.objects.create(
            mahasiswa=self.mahasiswa,
            dosen_pembimbing=self.dosen,
            judul="Thesis on Performance Testing",
            deskripsi="A deep dive into load testing methodologies."
        )
        
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
    def upload_document(self):
        """
        Task to upload a new document for a random chapter.
        """
        if not self.token:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Choose a random chapter to upload
        bab_choice = random.choice(Dokumen.BAB_CHOICES)[0]
        
        # Create a dummy file in memory
        dummy_file = io.BytesIO(b"This is the content of the test document.")
        dummy_file.name = f"test_document_{bab_choice}.pdf"
        
        payload = {
            "bab": bab_choice,
            "nama_dokumen": f"Dokumen untuk {bab_choice}",
        }
        
        files = {
            "file": (dummy_file.name, dummy_file, "application/pdf")
        }

        # Since a user can only upload one document per chapter, we'll check first
        # This is a simplified check; in a real scenario, we might track uploaded chapters in the user session
        if not Dokumen.objects.filter(pemilik=self.mahasiswa, bab=bab_choice).exists():
            self.client.post(
                "/api/v1/tugas-akhir/dokumen/",
                data=payload,
                files=files,
                headers=headers,
                name="/api/v1/tugas-akhir/dokumen/ [CREATE]"
            )

    def on_stop(self):
        """
        Cleans up all created test data for this user.
        """
        if hasattr(self, 'user_mahasiswa'):
            self.user_mahasiswa.delete()
        if hasattr(self, 'user_dosen'):
            self.user_dosen.delete()

# --- Global Cleanup Hooks ---
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("--- Global Start: Cleaning up leftover document test data ---")
    User.objects.filter(username__startswith='testuser_doc_').delete()
    User.objects.filter(username__startswith='testdosen_doc_').delete()
    print("--- Global cleanup complete. Starting test. ---")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("--- Global Stop: Cleaning up all document test data ---")
    User.objects.filter(username__startswith='testuser_doc_').delete()
    User.objects.filter(username__startswith='testdosen_doc_').delete()
    print("--- Final global cleanup complete. ---")
