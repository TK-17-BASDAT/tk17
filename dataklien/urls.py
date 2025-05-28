from django.urls import path
from . import views

app_name = 'dataklien'

urlpatterns = [
    path('dataklien/', views.client_list_view, name='client_list'), 
    path('details_json/<uuid:no_identitas_klien>/', views.get_client_details_json, name='get_client_details_json'),
]
