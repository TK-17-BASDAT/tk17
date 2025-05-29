# tk17/kunjungan/urls.py
from django.urls import path
from . import views

app_name = 'kunjungan'

urlpatterns = [
    path('', views.list_kunjungan_view, name='list_all_kunjungan'),
    path('tambah/', views.tambah_kunjungan_view, name='tambah_kunjungan'),
    path('rekam-medis/<str:id_kunjungan>/<str:nama_hewan>/<str:no_identitas_klien>/<str:no_front_desk>/<str:no_perawat_hewan>/<str:no_dokter_hewan>/', 
         views.rekam_medis_view, name='rekam_medis_detail'),
]