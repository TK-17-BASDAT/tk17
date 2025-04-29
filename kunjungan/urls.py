from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'kunjungan'

urlpatterns = [
    path('', TemplateView.as_view(template_name='kunjungan/list.html'), name='list'),
    path('create/', views.create_kunjungan, name='create'),
    path('update/', views.update_kunjungan, name='update'),
    path('delete/', views.delete_kunjungan, name='delete'),
]