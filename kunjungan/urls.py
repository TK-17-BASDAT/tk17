# tk17/kunjungan/urls.py
from django.urls import path
from . import views

app_name = 'kunjungan'

urlpatterns = [
    path('', views.list_kunjungan_view, name='list_all_kunjungan'),
    path('tambah/', views.tambah_kunjungan_view, name='tambah_kunjungan'),
    path('rekam-medis/<uuid:id_kunjungan>/<str:nama_hewan>/<uuid:no_identitas_klien>/<uuid:no_front_desk>/<uuid:no_perawat_hewan>/<uuid:no_dokter_hewan>/', 
         views.rekam_medis_view, name='rekam_medis_detail'),
    path('delete/<uuid:id_kunjungan>/', views.delete_kunjungan_view, name='delete_kunjungan'),
    path('update/<uuid:id_kunjungan>/', views.update_kunjungan_view, name='update_kunjungan'),
    path('get-details/<uuid:id_kunjungan>/', views.get_kunjungan_details, name='get_kunjungan_details'),
]