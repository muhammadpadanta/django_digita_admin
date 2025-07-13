import os
from locust import HttpUser, task, between

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digita_admin.settings')
import django
django.setup()

from django.contrib.auth.models import User

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)  # Time between each task execution

    @task
    def index_page(self):
        self.client.get("/")

    @task(3)
    def about_page(self):
        self.client.get("/about/")

    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        # Example of a user logging in
        # Note: You'll need to handle CSRF tokens for POST requests
        res = self.client.get("/admin/login/")
        csrftoken = res.cookies['csrftoken']
        self.client.post("/admin/login/", {
            "username": "testuser",
            "password": "password",
            "csrfmiddlewaretoken": csrftoken
        }, headers={'X-CSRFToken': csrftoken})