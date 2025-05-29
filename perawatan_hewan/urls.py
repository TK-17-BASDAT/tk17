from django.urls import path
from . import views

app_name = 'perawatan_hewan'

urlpatterns = [
    path('', views.perawatan_view, name='perawatan_view'),
    path('create/', views.perawatan_create, name='perawatan_create'),
    path('update/<uuid:id_kunjungan>/', views.perawatan_update, name='perawatan_update'),
    path('delete/<uuid:id_kunjungan>/', views.perawatan_delete, name='perawatan_delete'),
    path('data/<uuid:id_kunjungan>/', views.perawatan_data, name='perawatan_data'),
    # path('jenis-perawatan/', views.get_jenis_perawatan, name='get_jenis_perawatan'),
]