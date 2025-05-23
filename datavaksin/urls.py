from django.urls import path
from . import views

app_name = 'data_vaksin'

urlpatterns = [
    path('', views.vaccine_data_list_view, name='vaccine_data_list'),
    path('create/', views.vaccine_data_create_view, name='vaccine_data_create'),
    path('update/<str:kode_vaksin>/', views.vaccine_data_update_view, name='vaccine_data_update'),
    path('update-stock/<str:kode_vaksin>/', views.vaccine_stock_update_view, name='vaccine_stock_update'),
    path('delete/<str:kode_vaksin>/', views.vaccine_data_delete_view, name='vaccine_data_delete'),
    # Opsional: URL untuk AJAX
    path('details/<str:kode_vaksin>/json/', views.get_vaccine_details_json, name='get_vaccine_details_json'),
]