from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('dokter/', views.DokterProfileView.as_view(), name='dokter'), 
    path('frontdesk/', views.FrontDeskProfileView.as_view(), name='frontdesk'),  
    path('klien/', views.KlienProfileView.as_view(), name='klien'),  
    path('perawat/', views.PerawatProfileView.as_view(), name='perawat'), 
    path('kliencompany/', views.KlienCompanyProfileView.as_view(), name='kliencompany'),
    path('change-password/', views.PasswordChangeCustomView.as_view(), name='change_password'),
]
