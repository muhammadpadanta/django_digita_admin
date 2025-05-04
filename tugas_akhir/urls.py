from django.urls import path
from . import views

urlpatterns = [
    path('request-dosen/', views.RequestDosenCreateView.as_view(), name='request-supervisor-create'),
    path('request-dosen/pribadi/', views.MySupervisorRequestListView.as_view(), name='request-supervisor-mine'),
    path('request-mahasiswa/incoming/', views.IncomingSupervisorRequestListView.as_view(), name='request-supervisor-incoming'),
    path('request-mahasiswa/<int:pk>/respond/', views.SupervisorRequestRespondView.as_view(), name='request-supervisor-respond'),

]
