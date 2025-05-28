from django.urls import path
from . import views

app_name = 'hewan_peliharaan'

urlpatterns = [
    path('', views.list_hewan_peliharaan, name='list'),
    path('create/', views.create_hewan_peliharaan, name='create'),
    path('update/<str:id>/', views.update_hewan_peliharaan, name='update'),
    path('delete/<str:id>/', views.delete_hewan_peliharaan, name='delete'),
]