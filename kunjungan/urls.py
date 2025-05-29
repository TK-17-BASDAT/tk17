from django.urls import path
from . import views

app_name = 'kunjungan'

urlpatterns = [
    path('', views.kunjungan_view, name='kunjungan_view'),
    path('create/', views.kunjungan_create, name='kunjungan_create'),
    path('update/<uuid:id_kunjungan>/', views.kunjungan_update, name='kunjungan_update'),
    path('delete/<uuid:id_kunjungan>/', views.kunjungan_delete, name='kunjungan_delete'),
    path('data/<uuid:id_kunjungan>/', views.kunjungan_data, name='kunjungan_data'),
    path('get-hewan/', views.get_hewan_by_klien, name='get_hewan_by_klien'),
    path('rekam-medis/check/<uuid:id_kunjungan>/', views.rekam_medis_check, name='rekam_medis_check'),
    path('rekam-medis/create/<uuid:id_kunjungan>/', views.rekam_medis_create, name='rekam_medis_create'),
    path('rekam-medis/update/<uuid:id_kunjungan>/', views.rekam_medis_update, name='rekam_medis_update'),
]