# tk17/pet_clinic_tk17/views.py
from django.shortcuts import render

def klien_dashboard(request):
    return render(request, 'dashboard/klien.html')

def frontdesk_dashboard(request):
    return render(request, 'dashboard/frontdesk.html')

def dokter_dashboard(request):
    return render(request, 'dashboard/dokter.html')

def perawat_dashboard(request):
    return render(request, 'dashboard/perawat.html')

# Add other view functions as needed