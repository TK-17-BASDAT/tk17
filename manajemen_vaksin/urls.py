from django.urls import path
from . import views

app_name = 'manajemen_vaksin'

urlpatterns = [
    path('vaksin/', views.vaccination_list_view, name='vaccination_list'),
    # path('vaccinations/create/', views.vaccination_create_view, name='vaccination_create'),
    # path('vaccinations/update/<int:pk>/', views.vaccination_update_view, name='vaccination_update'), # Example using pk
    # path('vaccinations/delete/<int:pk>/', views.vaccination_delete_view, name='vaccination_delete'), # Example using pk
]
