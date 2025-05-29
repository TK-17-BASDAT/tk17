import uuid
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db import connection
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

def role_required(allowed_roles):

    def decorator(view_func):
        @login_required
        def wrapped_view(request, *args, **kwargs):
            
            user_role = request.session.get('user_role')
            if user_role not in allowed_roles:
                return HttpResponseForbidden("You don't have permission to access this page")
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator

@login_required
@role_required(['front_desk', 'dokter_hewan'])
def list_jenis_hewan(request):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, nama_jenis FROM petclinic.jenis_hewan ORDER BY id ASC"
        )
        jenis_hewan_list = cursor.fetchall()
        
        jenis_hewan_with_delete_info = []
        for jh in jenis_hewan_list:
            cursor.execute(
                "SELECT COUNT(*) FROM petclinic.hewan WHERE id_jenis = %s",
                [jh[0]]
            )
            count = cursor.fetchone()[0]
            can_delete = count == 0
            jenis_hewan_with_delete_info.append({
                'id': jh[0],
                'nama_jenis': jh[1],
                'can_delete': can_delete
            })
    
    context = {
        'jenis_hewan_list': jenis_hewan_with_delete_info,
        'user_role': request.session.get('user_role', ''),
        'debug_info': {
            'session_user_role': request.session.get('user_role', '')
        }
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('jenis_hewan/list_partial.html', context, request)
        return JsonResponse({'html': html})
    return render(request, 'jenis_hewan/list.html', context)


@login_required
@role_required(['front_desk'])
def create_jenis_hewan(request):

    if request.method == 'POST':
        nama_jenis = request.POST.get('nama_jenis')
        
        if not nama_jenis:
            messages.error(request, "Nama jenis tidak boleh kosong!")
            return render(request, 'jenis_hewan/create.html')
        
        try:
            id_jenis = uuid.uuid4()
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO petclinic.jenis_hewan (id, nama_jenis) VALUES (%s, %s)",
                    [id_jenis, nama_jenis]
                )
            
            messages.success(request, f"Jenis hewan {nama_jenis} berhasil ditambahkan!")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('jenis_hewan:list')
            
        except Exception as e:
            error_message = str(e)
            # Check if this is custom trigger error about duplicate jenis
            if "Jenis hewan" in error_message and "sudah terdaftar dengan ID" in error_message:
                # trigger error, extract it directly
                messages.error(request, error_message)
            else:
                # Generic database error
                messages.error(request, f"Gagal menambahkan jenis hewan: {error_message}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                html = render_to_string('jenis_hewan/create.html', {'error': error_message}, request)
                return JsonResponse({'success': False, 'html': html})
    
    
    return render(request, 'jenis_hewan/create.html')

@login_required
@role_required(['front_desk'])
def update_jenis_hewan(request, id):

    with connection.cursor() as cursor:
        
        cursor.execute(
            "SELECT id, nama_jenis FROM petclinic.jenis_hewan WHERE id = %s",
            [id]
        )
        jenis_hewan = cursor.fetchone()
        
        if not jenis_hewan:
            messages.error(request, "Jenis hewan tidak ditemukan!")
            return redirect('jenis_hewan:list')
        
        context = {
            'id': jenis_hewan[0],
            'nama_jenis': jenis_hewan[1]
        }
    
    if request.method == 'POST':
        nama_jenis = request.POST.get('nama_jenis')
        
        if not nama_jenis:
            messages.error(request, "Nama jenis tidak boleh kosong!")
            return render(request, 'jenis_hewan/update.html', context)
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE petclinic.jenis_hewan SET nama_jenis = %s WHERE id = %s",
                    [nama_jenis, id]
                )
            
            messages.success(request, f"Jenis hewan berhasil diupdate menjadi {nama_jenis}!")
            
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('jenis_hewan:list')
            
        except Exception as e:
            messages.error(request, f"Gagal mengupdate jenis hewan: {str(e)}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                html = render_to_string('jenis_hewan/update.html', context, request)
                return JsonResponse({'success': False, 'html': html})
    
    
    return render(request, 'jenis_hewan/update.html', context)

@login_required
@role_required(['front_desk'])
def delete_jenis_hewan(request, id):

    with connection.cursor() as cursor:
        
        cursor.execute(
            "SELECT id, nama_jenis FROM petclinic.jenis_hewan WHERE id = %s",
            [id]
        )
        jenis_hewan = cursor.fetchone()
        
        if not jenis_hewan:
            messages.error(request, "Jenis hewan tidak ditemukan!")
            return redirect('jenis_hewan:list')
        
        
        cursor.execute(
            "SELECT COUNT(*) FROM petclinic.hewan WHERE id_jenis = %s",
            [id]
        )
        count = cursor.fetchone()[0]
        
        if count > 0:
            messages.error(request, "Tidak dapat menghapus jenis hewan yang sedang digunakan!")
            return redirect('jenis_hewan:list')
        
        context = {
            'id': jenis_hewan[0],
            'nama_jenis': jenis_hewan[1]
        }
    
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM petclinic.jenis_hewan WHERE id = %s",
                    [id]
                )
            
            messages.success(request, f"Jenis hewan {context['nama_jenis']} berhasil dihapus!")
            
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('jenis_hewan:list')
            
        except Exception as e:
            messages.error(request, f"Gagal menghapus jenis hewan: {str(e)}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                html = render_to_string('jenis_hewan/delete.html', context, request)
                return JsonResponse({'success': False, 'html': html})
    
    
    return render(request, 'jenis_hewan/delete.html', context)