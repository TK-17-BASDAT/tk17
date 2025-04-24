"""
URL configuration for pet_clinic_tk17 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django import views
from django.contrib import admin
from django.urls import path
from . import views



urlpatterns = [
    path('admin/', admin.site.urls),
        # Klien URLs
    path('klien/dashboard/', views.klien_dashboard, name='klien_dashboard'),
    # path('klien/hewan/', views.kelola_hewan, name='kelola_hewan'),
    
    # Front Desk URLs
    path('frontdesk/dashboard/', views.frontdesk_dashboard, name='frontdesk_dashboard'),
    # path('frontdesk/jenis-hewan/', views.kelola_jenis_hewan, name='kelola_jenis_hewan'),
    # path('frontdesk/hewan/', views.frontdesk_kelola_hewan, name='frontdesk_kelola_hewan'),
    # path('frontdesk/kunjungan/', views.kelola_kunjungan, name='kelola_kunjungan'),
    # path('frontdesk/klien/', views.daftar_klien, name='daftar_klien'),
    
    # Dokter URLs
    path('dokter/dashboard/', views.dokter_dashboard, name='dokter_dashboard'),
    # path('dokter/jenis-hewan/', views.dokter_jenis_hewan, name='dokter_jenis_hewan'),
    # path('dokter/rekam-medis/', views.kelola_rekam_medis, name='kelola_rekam_medis'),
    # path('dokter/manajemen-obat/', views.manajemen_obat, name='manajemen_obat'),
    # path('dokter/jenis-perawatan/', views.manajemen_jenis_perawatan, name='manajemen_jenis_perawatan'),
    # path('dokter/pemberian-obat/', views.manajemen_pemberian_obat, name='manajemen_pemberian_obat'),
    # path('dokter/vaksinasi/', views.manajemen_vaksinasi, name='manajemen_vaksinasi'),
    
    # Perawat URLs
    path('perawat/dashboard/', views.perawat_dashboard, name='perawat_dashboard'),
    # path('perawat/manajemen-obat/', views.perawat_manajemen_obat, name='perawat_manajemen_obat'),
    # path('perawat/jenis-perawatan/', views.perawat_jenis_perawatan, name='perawat_jenis_perawatan'),
    # path('perawat/manajemen-vaksin/', views.perawat_manajemen_vaksin, name='perawat_manajemen_vaksin'),
    
    # Common URLs
    # path('logout/', views.logoput_view, name='logout'),
]
