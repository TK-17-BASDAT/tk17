from django.shortcuts import render

def data_vaksin(request):
    return render(request, 'datavaksin/datavaksin.html')
