from django.urls import path
from django.views.generic import TemplateView

app_name = 'authentication'

urlpatterns = [
    path('login/', TemplateView.as_view(template_name='authentication/login.html'), name='login'),
    path('register/', TemplateView.as_view(template_name='authentication/register.html'), name='register'),
    path('logout/', TemplateView.as_view(template_name='authentication/logout.html'), name='logout'),
]
