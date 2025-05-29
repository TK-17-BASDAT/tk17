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
@role_required(['front_desk', 'klien_individu', 'klien_perusahaan'])
def list_hewan_peliharaan(request):
    user_role = request.session.get('user_role')
    
    
    client_id = None
    if user_role in ['klien_individu', 'klien_perusahaan']:
        client_id = request.session.get('no_identitas')
    
    with connection.cursor() as cursor:
        
        base_query = """
            SELECT 
                h.nama,
                CASE 
                    WHEN i.nama_depan IS NOT NULL THEN CONCAT(i.nama_depan, ' ', i.nama_belakang)
                    WHEN p.nama_perusahaan IS NOT NULL THEN p.nama_perusahaan
                    ELSE 'Unknown'
                END as nama_pemilik,
                h.no_identitas_klien,
                jh.nama_jenis,
                h.nama,
                h.tanggal_lahir,
                h.url_foto,
                jh.id as id_jenis
            FROM 
                petclinic.hewan h
            JOIN 
                petclinic.jenis_hewan jh ON h.id_jenis = jh.id
            LEFT JOIN 
                petclinic.klien k ON h.no_identitas_klien = k.no_identitas
            LEFT JOIN 
                petclinic.individu i ON h.no_identitas_klien = i.no_identitas_klien
            LEFT JOIN 
                petclinic.perusahaan p ON h.no_identitas_klien = p.no_identitas_klien
        """
        
        
        if client_id:
            query = base_query + " WHERE h.no_identitas_klien = %s"
            cursor.execute(query + " ORDER BY nama_pemilik ASC, nama_jenis ASC, h.nama ASC", [client_id])
        else:
            
            cursor.execute(base_query + " ORDER BY nama_pemilik ASC, nama_jenis ASC, h.nama ASC")
            
        hewan_list = cursor.fetchall()
        
        
        hewan_with_delete_info = []
        for i, hw in enumerate(hewan_list):
            cursor.execute(
                """
                SELECT COUNT(*) 
                FROM petclinic.kunjungan 
                WHERE nama_hewan = %s AND no_identitas_klien = %s
                """,
                [hw[4], hw[2]]  
            )
            active_visits = cursor.fetchone()[0]
            can_delete = active_visits == 0
            
            
            from datetime import datetime
            date_obj = hw[5]  
            formatted_date = date_obj.strftime('%d %B %Y') if date_obj else 'Unknown'
            
            
            composite_id = f"{hw[4]}:{hw[2]}"  
            
            hewan_with_delete_info.append({
                'id': composite_id,
                'nama_pemilik': hw[1],
                'no_identitas_klien': hw[2],
                'jenis_hewan': hw[3],
                'nama_hewan': hw[4],
                'tanggal_lahir': hw[5],  
                'tanggal_lahir_formatted': formatted_date,
                'url_foto': hw[6] or "https://placedog.net/60/60",  
                'id_jenis': hw[7],
                'can_delete': can_delete,
                'counter': i + 1  
            })
        
        
        clients = []
        if user_role == 'front_desk':
            cursor.execute("""
                SELECT k.no_identitas, CONCAT(i.nama_depan, ' ', i.nama_belakang) as nama
                FROM petclinic.klien k
                JOIN petclinic.individu i ON k.no_identitas = i.no_identitas_klien
            """)
            individuals = [{'id': c[0], 'name': c[1]} for c in cursor.fetchall()]
            
            cursor.execute("""
                SELECT k.no_identitas, p.nama_perusahaan
                FROM petclinic.klien k
                JOIN petclinic.perusahaan p ON k.no_identitas = p.no_identitas_klien
            """)
            companies = [{'id': c[0], 'name': c[1]} for c in cursor.fetchall()]
            
            clients = individuals + companies
        
        
        cursor.execute("SELECT id, nama_jenis FROM petclinic.jenis_hewan ORDER BY nama_jenis")
        jenis_hewan_list = [{'id': j[0], 'nama': j[1]} for j in cursor.fetchall()]
    
    context = {
        'hewan_list': hewan_with_delete_info,
        'jenis_hewan_list': jenis_hewan_list,
        'clients': clients,
        'user_role': user_role,
    }
    
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('hewan_peliharaan/list_partial.html', context, request)
        return JsonResponse({'html': html})
        
    return render(request, 'hewan_peliharaan/list.html', context)


@login_required
@role_required(['front_desk', 'klien_individu', 'klien_perusahaan'])
def create_hewan_peliharaan(request):
    user_role = request.session.get('user_role')
    
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, nama_jenis FROM petclinic.jenis_hewan ORDER BY nama_jenis")
        jenis_hewan_list = [{'id': j[0], 'nama': j[1]} for j in cursor.fetchall()]
        
        
        clients = []
        if user_role == 'front_desk':
            cursor.execute("""
                SELECT k.no_identitas, CONCAT(i.nama_depan, ' ', i.nama_belakang) as nama
                FROM petclinic.klien k
                JOIN petclinic.individu i ON k.no_identitas = i.no_identitas_klien
            """)
            individuals = [{'id': c[0], 'name': c[1]} for c in cursor.fetchall()]
            
            cursor.execute("""
                SELECT k.no_identitas, p.nama_perusahaan
                FROM petclinic.klien k
                JOIN petclinic.perusahaan p ON k.no_identitas = p.no_identitas_klien
            """)
            companies = [{'id': c[0], 'name': c[1]} for c in cursor.fetchall()]
            
            clients = individuals + companies
    
    context = {
        'jenis_hewan_list': jenis_hewan_list,
        'clients': clients,
        'user_role': user_role
    }
    
    if request.method == 'POST':
        
        nama_hewan = request.POST.get('nama_hewan')
        tgl_lahir = request.POST.get('tgl_lahir')
        url_foto = request.POST.get('url_foto')
        id_jenis = request.POST.get('jenis_hewan')
        
        
        
        if user_role == 'front_desk':
            no_identitas_klien = request.POST.get('pemilik')
        else:
            no_identitas_klien = request.session.get('no_identitas')
        
        if not (nama_hewan and tgl_lahir and id_jenis and no_identitas_klien):
            messages.error(request, "Please fill in all required fields!")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                html = render_to_string('hewan_peliharaan/create.html', context, request)
                return JsonResponse({'success': False, 'html': html})
            return render(request, 'hewan_peliharaan/create.html', context)
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO petclinic.hewan 
                    (nama, no_identitas_klien, tanggal_lahir, id_jenis, url_foto) 
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    [nama_hewan, no_identitas_klien, tgl_lahir, id_jenis, url_foto]
                )
            
            messages.success(request, f"Pet {nama_hewan} successfully added!")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('hewan_peliharaan:list')
            
        except Exception as e:
            messages.error(request, f"Failed to add pet: {str(e)}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                html = render_to_string('hewan_peliharaan/create.html', context, request)
                return JsonResponse({'success': False, 'html': html})
    
    
    return render(request, 'hewan_peliharaan/create.html', context)


@login_required
@role_required(['front_desk', 'klien_individu', 'klien_perusahaan'])
def update_hewan_peliharaan(request, id):
    user_role = request.session.get('user_role')
    client_id = None
    
    if user_role in ['klien_individu', 'klien_perusahaan']:
        client_id = request.session.get('no_identitas')
    
    
    try:
        nama_hewan, no_identitas_klien = id.split(':')
    except ValueError:
        messages.error(request, "Invalid pet ID format")
        return redirect('hewan_peliharaan:list')
    
    with connection.cursor() as cursor:
        
        cursor.execute(
            """
            SELECT 
                h.*,
                jh.nama_jenis,
                CASE 
                    WHEN i.nama_depan IS NOT NULL THEN CONCAT(i.nama_depan, ' ', i.nama_belakang)
                    WHEN p.nama_perusahaan IS NOT NULL THEN p.nama_perusahaan
                    ELSE 'Unknown'
                END as nama_pemilik
            FROM 
                petclinic.hewan h
            JOIN 
                petclinic.jenis_hewan jh ON h.id_jenis = jh.id
            LEFT JOIN 
                petclinic.individu i ON h.no_identitas_klien = i.no_identitas_klien
            LEFT JOIN 
                petclinic.perusahaan p ON h.no_identitas_klien = p.no_identitas_klien
            WHERE 
                h.nama = %s AND h.no_identitas_klien = %s
            """,
            [nama_hewan, no_identitas_klien]
        )
        hewan = cursor.fetchone()
        
        if not hewan:
            messages.error(request, "Pet not found!")
            return redirect('hewan_peliharaan:list')
        
        
        if client_id and str(hewan[1]) != client_id:  
            return HttpResponseForbidden("You don't have permission to update this pet")
        
        
        cursor.execute("SELECT id, nama_jenis FROM petclinic.jenis_hewan ORDER BY nama_jenis")
        jenis_hewan_list = [{'id': j[0], 'nama': j[1]} for j in cursor.fetchall()]
        
        
        clients = []
        if user_role == 'front_desk':
            cursor.execute("""
                SELECT k.no_identitas, CONCAT(i.nama_depan, ' ', i.nama_belakang) as nama
                FROM petclinic.klien k
                JOIN petclinic.individu i ON k.no_identitas = i.no_identitas_klien
            """)
            individuals = [{'id': c[0], 'name': c[1]} for c in cursor.fetchall()]
            
            cursor.execute("""
                SELECT k.no_identitas, p.nama_perusahaan
                FROM petclinic.klien k
                JOIN petclinic.perusahaan p ON k.no_identitas = p.no_identitas_klien
            """)
            companies = [{'id': c[0], 'name': c[1]} for c in cursor.fetchall()]
            
            clients = individuals + companies
        
        
        from datetime import datetime
        tanggal_lahir = hewan[2]  
        formatted_date = tanggal_lahir.strftime('%Y-%m-%d') if tanggal_lahir else ''
        
        context = {
            'id': id,  
            'old_nama': hewan[0],  
            'old_owner_id': hewan[1],  
            'nama_hewan': hewan[0],
            'no_identitas_klien': hewan[1],
            'tanggal_lahir': formatted_date,
            'id_jenis': hewan[3],
            'url_foto': hewan[4] or "",
            'nama_jenis': hewan[5],
            'nama_pemilik': hewan[6],
            'jenis_hewan_list': jenis_hewan_list,
            'clients': clients,
            'user_role': user_role
        }
    
    if request.method == 'POST':
        nama_hewan_new = request.POST.get('nama_hewan')
        tgl_lahir = request.POST.get('tgl_lahir')
        url_foto = request.POST.get('url_foto')
        id_jenis = request.POST.get('jenis_hewan')
        
        
        
        if user_role == 'front_desk':
            no_identitas_klien_new = request.POST.get('pemilik')
        else:
            no_identitas_klien_new = no_identitas_klien  
        
        if not (nama_hewan_new and tgl_lahir and id_jenis):
            messages.error(request, "Please fill in all required fields!")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                html = render_to_string('hewan_peliharaan/update.html', context, request)
                return JsonResponse({'success': False, 'html': html})
            return render(request, 'hewan_peliharaan/update.html', context)
        
        try:
            with connection.cursor() as cursor:
                
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM petclinic.kunjungan
                    WHERE nama_hewan = %s AND no_identitas_klien = %s
                    """,
                    [nama_hewan, no_identitas_klien]
                )
                visit_count = cursor.fetchone()[0]
                
                
                
                if visit_count > 0 and (nama_hewan != nama_hewan_new or no_identitas_klien != no_identitas_klien_new):
                    messages.error(request, "Cannot change pet name or owner for pets with visits.")
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        html = render_to_string('hewan_peliharaan/update.html', context, request)
                        return JsonResponse({'success': False, 'html': html})
                    return render(request, 'hewan_peliharaan/update.html', context)
                
                
                cursor.execute(
                    """
                    UPDATE petclinic.hewan 
                    SET nama = %s, no_identitas_klien = %s, tanggal_lahir = %s, 
                        id_jenis = %s, url_foto = %s
                    WHERE nama = %s AND no_identitas_klien = %s
                    """,
                    [
                        nama_hewan_new, no_identitas_klien_new, tgl_lahir, 
                        id_jenis, url_foto, nama_hewan, no_identitas_klien
                    ]
                )
            
            messages.success(request, f"Pet {nama_hewan_new} successfully updated!")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('hewan_peliharaan:list')
            
        except Exception as e:
            messages.error(request, f"Failed to update pet: {str(e)}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                html = render_to_string('hewan_peliharaan/update.html', context, request)
                return JsonResponse({'success': False, 'html': html})
    
    
    return render(request, 'hewan_peliharaan/update.html', context)


@login_required
@role_required(['front_desk'])
def delete_hewan_peliharaan(request, id):
    user_role = request.session.get('user_role')
    if user_role != 'front_desk':
        return HttpResponseForbidden("Only Front Desk Officers can delete pets.")
    
    
    try:
        nama_hewan, no_identitas_klien = id.split(':')
    except ValueError:
        messages.error(request, "Invalid pet ID format")
        return redirect('hewan_peliharaan:list')
    
    with connection.cursor() as cursor:
        
        cursor.execute(
            """
            SELECT 
                h.*,
                CASE 
                    WHEN i.nama_depan IS NOT NULL THEN CONCAT(i.nama_depan, ' ', i.nama_belakang)
                    WHEN p.nama_perusahaan IS NOT NULL THEN p.nama_perusahaan
                    ELSE 'Unknown'
                END as nama_pemilik
            FROM 
                petclinic.hewan h
            LEFT JOIN 
                petclinic.individu i ON h.no_identitas_klien = i.no_identitas_klien
            LEFT JOIN 
                petclinic.perusahaan p ON h.no_identitas_klien = p.no_identitas_klien
            WHERE 
                h.nama = %s AND h.no_identitas_klien = %s
            """,
            [nama_hewan, no_identitas_klien]
        )
        hewan = cursor.fetchone()
        
        if not hewan:
            messages.error(request, "Pet not found!")
            return redirect('hewan_peliharaan:list')
        
        context = {
            'id': id,  
            'nama_hewan': hewan[0],
            'nama_pemilik': hewan[5]
        }
    
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM petclinic.hewan 
                    WHERE nama = %s AND no_identitas_klien = %s
                    """,
                    [nama_hewan, no_identitas_klien]
                )
            
            messages.success(request, f"Pet {nama_hewan} successfully deleted!")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('hewan_peliharaan:list')
            
        except Exception as e:
            error_message = str(e)
            
            if "masih memiliki kunjungan aktif" in error_message:
                
                messages.error(request, error_message)
            else:
                
                messages.error(request, f"Failed to delete pet: {error_message}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                context = {
                    'id': id,
                    'nama_hewan': nama_hewan,
                    'nama_pemilik': hewan[5],
                    'error': error_message
                }
                html = render_to_string('hewan_peliharaan/delete.html', context, request)
                return JsonResponse({'success': False, 'html': html})
    
    
    return render(request, 'hewan_peliharaan/delete.html', context)