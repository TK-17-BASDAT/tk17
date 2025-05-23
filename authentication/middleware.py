from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class RoleMiddleware:
    """
    Middleware to enforce role-based access to views
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        
        if request.path.startswith('/auth/'):
            
            return self.get_response(request)
        
        
        if not request.user.is_authenticated:
            if request.path != reverse('authentication:login'):
                messages.warning(request, "Please log in to access this page")
                return redirect('authentication:login')
        else:
            
            user_role = request.session.get('user_role', None)
            
            
            role_required_prefixes = {
                'klien_individu': ['/dashboard/klien-individu/'],
                'klien_perusahaan': ['/dashboard/klien-perusahaan/'],
                'front_desk': ['/dashboard/front-desk/'],
                'dokter_hewan': ['/dashboard/dokter-hewan/'],
                'perawat_hewan': ['/dashboard/perawat-hewan/'],
            }
            
            for role, prefixes in role_required_prefixes.items():
                for prefix in prefixes:
                    if request.path.startswith(prefix) and user_role != role:
                        messages.warning(request, "You don't have permission to access this page")
                        return redirect('dashboard:index')
            
        response = self.get_response(request)
        return response
