from django.urls import path
from django.views.generic import TemplateView

app_name = 'jenis_hewan'

urlpatterns = [
    path(
        '',
        TemplateView.as_view(template_name='jenis_hewan/list.html'),
        name='list'
    ),

    path(
        'create/',
        TemplateView.as_view(template_name='jenis_hewan/create.html'),
        name='create'
    ),

    path(
        'update/<int:pk>/',
        TemplateView.as_view(template_name='jenis_hewan/update.html'),
        name='update'
    ),

    path(
        'delete/<int:pk>/',
        TemplateView.as_view(template_name='jenis_hewan/delete.html'),
        name='delete'
    ),
]
