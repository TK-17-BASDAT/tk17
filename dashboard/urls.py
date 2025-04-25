from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('dashboard/dokter/', views.dokter_profile, name='dokter'), 
    path('dashboard/frontdesk/', views.frontdesk_profile, name='frontdesk'),  
    path('dashboard/klien/', views.klien_profile, name='klien'),  
    path('dashboard/perawat/', views.perawat_profile, name='perawat'), 
]
