from django.urls import path
from . import views

app_name = 'manajemen_vaksin'

urlpatterns = [
    path('vaksin/', views.manajemen_vaksin, name='manajemen_vaksin'), 
]
