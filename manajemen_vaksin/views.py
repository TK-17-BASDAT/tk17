from django.shortcuts import render

def manajemen_vaksin(request):
    return render(request, 'manajemen_vaksin/vaksin.html')
