from django.urls import path
from . import views

app_name = 'manajemen_vaksin'

urlpatterns = [
    path('vaksin/', views.vaccination_list_view, name='vaccination_list'),
    path('create/', views.vaccination_create_view, name='vaccination_create'),
    path('update/<uuid:kunjungan_id>/', views.vaccination_update_view, name='vaccination_update_view'),
    path('delete/<uuid:kunjungan_id>/', views.vaccination_delete_view, name='vaccination_delete'),
    path('riwayat-klien/', views.ClientPetVaccinationHistoryView.as_view(), name='client_vaccination_history'),
]
