# tugas_akhir/urls.py
from django.urls import path
from . import views #
app_name = 'tugas_akhir'

# These are the URL patterns for your website's pages
urlpatterns = [
    # The URL for the page that lists all documents.
    path('documents/', views.document_list_view, name='document-list'),
    # URL for viewing or downloading a specific file
    path('documents/<int:pk>/file/', views.serve_document_file_view, name='document-file'),
    # URL for deleting a document
    path('documents/<int:pk>/delete/', views.delete_document_view, name='document-delete'),
    # URL for editing a document
    path('documents/<int:pk>/edit/', views.edit_document_view, name='document-edit'),
]