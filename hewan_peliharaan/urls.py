from django.urls import path
from django.views.generic import TemplateView

app_name = 'hewan_peliharaan'

urlpatterns = [
    path(
        '',
        TemplateView.as_view(template_name='hewan_peliharaan/list.html'),
        name='list'
    ),
    path(
        'create/',
        TemplateView.as_view(template_name='hewan_peliharaan/create.html'),
        name='create'
    ),
    path(
        'create/error/',
        TemplateView.as_view(template_name='hewan_peliharaan/error.html'),
        name='error'
    ),
    path(
        'update/<int:pk>/',
        TemplateView.as_view(template_name='hewan_peliharaan/update.html'),
        name='update'
    ),
    path(
        'delete/<int:pk>/',
        TemplateView.as_view(template_name='hewan_peliharaan/delete.html'),
        name='delete'
    ),
]
