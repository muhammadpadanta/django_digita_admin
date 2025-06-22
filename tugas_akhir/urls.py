# tugas_akhir/urls.py
from django.urls import path
from . import views #
app_name = 'tugas_akhir'

# These are the URL patterns for your website's pages
urlpatterns = [
    # list of Tugas Akhir
    path('ta/', views.tugas_akhir_list_view, name='ta-list'),
    # URL for the detail view of a specific Tugas Akhir
    path('ta/<int:pk>/details/', views.tugas_akhir_detail_view, name='ta-detail'),
    # URL for deleting a specific Tugas Akhir
    path('ta/<int:pk>/delete/', views.delete_tugas_akhir_view, name='ta-delete'),
    # The URL for the page that lists all documents.
    path('documents/', views.document_list_view, name='document-list'),
    # URL for viewing or downloading a specific file
    path('documents/<int:pk>/file/', views.serve_document_file_view, name='document-file'),
    # URL for deleting a document
    path('documents/<int:pk>/delete/', views.delete_document_view, name='document-delete'),
    # URL for editing a document
    path('documents/<int:pk>/edit/', views.edit_document_view, name='document-edit'),
    path('documents/create/', views.create_document_view, name='document-create'),

]