from django.shortcuts import render

def dokter_profile(request):
    return render(request, 'dashboard/dokter.html')

def frontdesk_profile(request):
    return render(request, 'dashboard/frontdesk.html')

def klien_profile(request):
    return render(request, 'dashboard/klien.html')

def perawat_profile(request):
    return render(request, 'dashboard/perawat.html')