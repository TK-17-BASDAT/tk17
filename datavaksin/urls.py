from django.urls import path
from . import views

app_name = 'data_vaksin'

urlpatterns = [
    path('datavaksin/', views.data_vaksin, name='data_vaksin'), 
]
