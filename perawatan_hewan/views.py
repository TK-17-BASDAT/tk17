from django.shortcuts import render

def create_perawatan(request):
    return render(request, 'perawatan_hewan/create.html')

def update_perawatan(request):
    return render(request, 'perawatan_hewan/update.html')

def delete_perawatan(request):
    return render(request, 'perawatan_hewan/delete.html')