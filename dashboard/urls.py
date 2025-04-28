from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('dokter/', views.dokter_profile, name='dokter'), 
    path('frontdesk/', views.frontdesk_profile, name='frontdesk'),  
    path('klien/', views.klien_profile, name='klien'),  
    path('perawat/', views.perawat_profile, name='perawat'), 
]
