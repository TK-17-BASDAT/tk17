from django.urls import path
from . import views

app_name = 'jenis_hewan'

urlpatterns = [
    path(
        '',
        views.list_jenis_hewan,
        name='list'
    ),

    path(
        'create/',
        views.create_jenis_hewan,
        name='create'
    ),

    path(
        'update/<uuid:id>/',  
        views.update_jenis_hewan,
        name='update'
    ),

    path(
        'delete/<uuid:id>/',  
        views.delete_jenis_hewan,
        name='delete'
    ),
]