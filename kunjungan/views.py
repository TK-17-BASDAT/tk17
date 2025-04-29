from django.shortcuts import render

def create_kunjungan(request):
    return render(request, 'kunjungan/create.html')

def update_kunjungan(request):
    return render(request, 'kunjungan/update.html')

def delete_kunjungan(request):
    return render(request, 'kunjungan/delete.html')