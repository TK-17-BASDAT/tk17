from django.shortcuts import render, redirect

def index(request):
    
    if not request.user.is_authenticated:
        return redirect('home')
    
    
    user_role = request.session.get('user_role')
    
    
    if user_role == 'klien_individu':
        return klien_profile(request)
    elif user_role == 'klien_perusahaan':
        return kliencompany_profile(request)
    elif user_role == 'front_desk':
        return frontdesk_profile(request)
    elif user_role == 'dokter_hewan':
        return dokter_profile(request)
    elif user_role == 'perawat_hewan':
        return perawat_profile(request)
    else:
        return redirect('home')

def dokter_profile(request):
    return render(request, 'dashboard/dokter.html')

def frontdesk_profile(request):
    return render(request, 'dashboard/frontdesk.html')

def klien_profile(request):
    return render(request, 'dashboard/klien.html')

def perawat_profile(request):
    return render(request, 'dashboard/perawat.html')

def kliencompany_profile(request):
    return render(request, 'dashboard/kliencompany.html')