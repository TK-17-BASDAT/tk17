from django.urls import path
from . import views

app_name = 'dataklien'

urlpatterns = [
    path('dataklien/', views.data_klien, name='manajemen_vaksin'), 
]
