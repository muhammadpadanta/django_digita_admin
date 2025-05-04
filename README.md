# DJANGO DIGITA ADMIN

Backend REST API untuk aplikasi manajemen tugas akhir (skripsi/tesis) antara mahasiswa dan dosen. Dibangun menggunakan Django dan Django REST Framework, dengan database PostgreSQL. Proyek ini dikonfigurasi untuk dijalankan menggunakan Docker dan Docker Compose untuk kemudahan setup environment pengembangan.

**Tech Stack:**
* Python 3.11+
* Django 5.x
* Django REST Framework
* djangorestframework-simplejwt (Untuk Autentikasi Token)
* PostgreSQL 16+
* Docker & Docker Compose

---

## Requirements

Pastikan software berikut sudah terinstall:

1.  **Git:** Untuk mengkloning repository. ([Download Git](https://git-scm.com/downloads))
2.  **Docker Desktop:** Termasuk Docker Engine dan Docker Compose. ([Download Docker Desktop](https://www.docker.com/products/docker-desktop/)) Pastikan Docker Desktop sedang berjalan.

---

## Setup Menggunakan Docker

Ikuti langkah-langkah ini untuk menjalankan project di environment laptopmu menggunakan Docker:

1.  **Clone Repository:**
    Buka terminal atau command prompt Anda dan clone repository ini:
    ```bash
    git clone https://github.com/muhammadpadanta/django_digita_admin
    cd django_digita_admin
    ```

2.  **Buat File Environment (`.env`):**
    * Proyek ini menggunakan file `.env` untuk menyimpan konfigurasi.
    * Download file .env di deskripsi Grup Whatsapp
    * Jalankan perintah berikut di terminal:
        ```bash
        cp .env.example .env
        ```
    * Copy Paste isi .env yg didownload ke .env yang ada di project.

3.  **Penting untuk Pengguna Windows (Line Endings):**
    * Pastikan file `entrypoint.sh` menggunakan format line ending **LF** (Unix/Linux) bukan CRLF (Windows).
    * Buka `entrypoint.sh` di VS Code, lihat di status bar kanan bawah, klik jika tertulis `CRLF` dan ubah menjadi `LF`, lalu simpan file. Lihat contoh gambar
    ![gambar_fix_windows](https://s4.gifyu.com/images/bL6HZ.png)

4.  **Build & Jalankan Containers:**
    * Buka terminal **di dalam direktori root proyek** (yang berisi `docker-compose.yml`).
    * Jalankan perintah berikut untuk membangun image Docker:
        ```bash
        docker-compose up --build
        ```
    * Proses nya mungkin bisa lama tergantung spek laptop :v
    * lihat log dari service `db` (PostgreSQL) dan `web` (Django). Tunggu hingga muncul pesan seperti:
        ```
        web-1  | Starting development server at [http://0.0.0.0:8000/](http://0.0.0.0:8000/)
        web-1  | Quit the server with CONTROL-C.
        ```

5.  **Akses Aplikasi:**
    * Backend API sudah jalan. bisa diakses di:
        * **API Endpoints:** Gunakan Postman untuk mengakses endpoint seperti `http://localhost:8000/api/users/login/`, `http://localhost:8000/api/users/dosen/`, dll.
        * **Django Admin:** Buka browser `http://localhost:8000/admin/`.
     
6. **Membuat Akun Admin untuk kelola data secara lokal**
   * Jalankan perintah berikut:
     ```bash
     docker-compose exec web python manage.py createsuperuser
     ```
   isi username dengan: `digitaadmin`, email dengan: `digitaadmin@polibatam.ac.id`, password dengan: `digitaadmin`
   * untuk kelola data pergi ke http://localhost:8000/admin/
   * Tambahkan dulu Jurusan baru tambahkan Program Studi, baru bisa register Mahasiswa/Dosen di flutternya.
---

## Jika ingin Menjalankan Aplikasi lagi nanti Setelah Setup Awal 

* **Memulai:** Jika container sudah pernah di-build dan tidak ada perubahan pada `Dockerfile` atau `requirements.txt`, jalankan:
    ```bash
    docker-compose up
    ```
* **Menghentikan:** Tekan `Ctrl+C` di terminal tempat `docker-compose up` berjalan. Lalu:
    ```bash
    docker-compose down
    ```
* **Menghentikan & Menghapus Volume Data:** Jika ingin mereset total database (misalnya memulai dari awal), gunakan flag `-v`:
    ```bash
    docker-compose down -v
    ```

---

## Jika ingin Menjalankan Perintah Django (`manage.py`)

Untuk menjalankan perintah `manage.py` (seperti `makemigrations`, `migrate`, `createsuperuser`, `shell`), buka **terminal baru**, navigasi ke root direktori proyek, dan gunakan `docker-compose exec`:

```bash
# Contoh membuat superuser (untuk login admin)
docker-compose exec web python manage.py createsuperuser

# Contoh membuka Django shell
docker-compose exec web python manage.py shell
