FROM python:3.11-slim

# Set environment variables
## agar Python membuat file .pyc
ENV PYTHONDONTWRITEBYTECODE=1
## agar output Python langsung tampil di console
ENV PYTHONUNBUFFERED=1

# Set workdir di dalam container
WORKDIR /app

# Jika ada error saat build psycopg2, uncomment baris berikut:
## RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install dependensi Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Port yang akan diekspos oleh container (port yang digunakan runserver)
EXPOSE 8000

# Menggunakan 0.0.0.0 agar bisa diakses dari luar container
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


