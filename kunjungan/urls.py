# tk17/kunjungan/urls.py
from django.urls import path
from . import views

app_name = 'kunjungan' # Namespace untuk URL

urlpatterns = [
    # URL untuk menampilkan daftar semua kunjungan
    path('', views.list_kunjungan_view, name='list_all_kunjungan'), # Sesuai dengan `kunjungan.html`

    # URL untuk melihat/membuat/mengupdate rekam medis spesifik
    # Pastikan path ini unik dan semua argumen UUID/stringnya benar
    path('<uuid:id_kunjungan>/<str:nama_hewan>/<uuid:no_identitas_klien>/<uuid:no_front_desk>/<uuid:no_perawat_hewan>/<uuid:no_dokter_hewan>/rekam-medis/',
         views.rekam_medis_view, name='rekam_medis_detail'), # 'rekam_medis_detail' untuk view/form
]