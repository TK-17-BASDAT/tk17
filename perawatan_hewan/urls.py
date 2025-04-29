from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'perawatan_hewan'

urlpatterns = [
    path('', TemplateView.as_view(template_name='perawatan_hewan/list.html'), name='list'),
    path('create/', views.create_perawatan, name='create'),
    path('update/', views.update_perawatan, name='update'),
    path('delete/', views.delete_perawatan, name='delete'),
]