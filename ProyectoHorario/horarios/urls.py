from django.urls import path
from .views import upload_file, ver_horarios

urlpatterns = [
    path('upload/', upload_file, name='upload_file'),
    path('ver_horarios/', ver_horarios, name='ver_horarios'),
]
