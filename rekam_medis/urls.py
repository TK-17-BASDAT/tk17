from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'rekam_medis'

urlpatterns = [
    path('create/', views.create_rekam_medis, name='create'),
    path('update/', views.update_rekam_medis, name='update'),
]