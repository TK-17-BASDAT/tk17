from django.shortcuts import render

def create_rekam_medis(request):
    return render(request, 'rekam_medis/create.html')

def update_rekam_medis(request):
    return render(request, 'rekam_medis/update.html')

def missing_rekam_medis(request):
    return render(request, 'rekam_medis/missing.html')
