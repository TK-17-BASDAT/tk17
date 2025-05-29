
from django.shortcuts import render, redirect
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.db import connection, IntegrityError, DatabaseError 


def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def dictfetchone(cursor):
    columns = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    if row:
        return dict(zip(columns, row))
    return None

def vaccine_data_list_view(request):
    vaksin_list_processed = [] 
    try:
        with connection.cursor() as cursor:
            
            
            query_vaksin_usage = """
                SELECT
                    v.kode,
                    v.nama,
                    v.harga,
                    v.stok,
                    CASE
                        WHEN COUNT(k.kode_vaksin) > 0 THEN TRUE
                        ELSE FALSE
                    END AS sudah_digunakan
                FROM
                    PETCLINIC.VAKSIN v
                LEFT JOIN
                    PETCLINIC.KUNJUNGAN k ON v.kode = k.kode_vaksin
                GROUP BY
                    v.kode, v.nama, v.harga, v.stok
                ORDER BY
                    v.kode;
            """
            
            
            
            
            
            
            
            
            
            
            
            
            
            cursor.execute(query_vaksin_usage)
            vaksin_list_raw = dictfetchall(cursor)

            for vaksin_data in vaksin_list_raw:
                vaksin_list_processed.append({
                    'kode': vaksin_data['kode'],
                    'nama': vaksin_data['nama'],
                    'harga': vaksin_data['harga'],
                    'stok': vaksin_data['stok'],
                    'sudah_digunakan': vaksin_data['sudah_digunakan'] 
                })

    except DatabaseError as e:
        messages.error(request, f"Gagal mengambil data vaksin: {e}")
        print(f"Database error in vaccine_data_list_view: {e}")


    context = {
        'vaksin_list': vaksin_list_processed, 
    }
    return render(request, 'datavaksin/datavaksin.html', context)

def vaccine_data_create_view(request):
    if request.method == 'POST':
        kode = request.POST.get('kode', '').strip()
        nama = request.POST.get('nama', '').strip()
        harga_str = request.POST.get('harga', '').strip()
        stok_str = request.POST.get('stok', '').strip()

        errors = []
        if not kode: errors.append("ID Vaksin tidak boleh kosong.")
        
        if not nama: errors.append("Nama Vaksin tidak boleh kosong.")
        harga = None
        if not harga_str:
            errors.append("Harga tidak boleh kosong.")
        else:
            try:
                harga = int(harga_str)
                if harga < 0: errors.append("Harga tidak boleh negatif.")
            except ValueError:
                errors.append("Harga harus berupa angka.")
        stok = None
        if not stok_str:
            errors.append("Stok tidak boleh kosong.")
        else:
            try:
                stok = int(stok_str)
                if stok < 0: errors.append("Stok tidak boleh negatif.")
            except ValueError:
                errors.append("Stok harus berupa angka.")


        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('datavaksin:vaccine_data_list')

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO PETCLINIC.VAKSIN (kode, nama, harga, stok) VALUES (%s, %s, %s, %s)",
                    [kode, nama, harga, stok]
                )
            messages.success(request, f"Vaksin '{nama}' (Kode: {kode}) berhasil ditambahkan.")
        except IntegrityError:
            messages.error(request, f"Gagal menambahkan vaksin. ID Vaksin '{kode}' sudah ada.")
        except DatabaseError as e:
            messages.error(request, f"Gagal menambahkan vaksin ke database: {e}")
        
        return redirect('datavaksin:vaccine_data_list')
    
    return redirect('datavaksin:vaccine_data_list')

def vaccine_data_update_view(request, kode_vaksin):
    
    current_vaksin = None
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT kode, nama, harga FROM PETCLINIC.VAKSIN WHERE kode = %s", [kode_vaksin])
            current_vaksin = dictfetchone(cursor)
    except DatabaseError as e:
        messages.error(request, f"Error mengambil data vaksin: {e}")
        return redirect('datavaksin:vaccine_data_list')

    if not current_vaksin:
        messages.error(request, f"Vaksin dengan ID '{kode_vaksin}' tidak ditemukan.")
        return redirect('datavaksin:vaccine_data_list')

    if request.method == 'POST':
        nama_baru = request.POST.get('nama', '').strip()
        harga_baru_str = request.POST.get('harga', '').strip()

        errors = []
        if not nama_baru: errors.append("Nama Vaksin tidak boleh kosong.")
        harga_baru = None
        if not harga_baru_str:
            errors.append("Harga tidak boleh kosong.")
        else:
            try:
                harga_baru = int(harga_baru_str)
                if harga_baru < 0: errors.append("Harga tidak boleh negatif.")
            except ValueError:
                errors.append("Harga harus berupa angka.")

        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('datavaksin:vaccine_data_list')

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE PETCLINIC.VAKSIN SET nama = %s, harga = %s WHERE kode = %s",
                    [nama_baru, harga_baru, kode_vaksin]
                )
            messages.success(request, f"Info vaksin '{nama_baru}' (ID: {kode_vaksin}) berhasil diupdate.")
        except DatabaseError as e:
            messages.error(request, f"Gagal mengupdate info vaksin: {e}")
        
        return redirect('datavaksin:vaccine_data_list')
    
    return redirect('datavaksin:vaccine_data_list')


def vaccine_stock_update_view(request, kode_vaksin):
    
    current_vaksin = None
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT kode, nama FROM PETCLINIC.VAKSIN WHERE kode = %s", [kode_vaksin])
            current_vaksin = dictfetchone(cursor)
    except DatabaseError as e:
        messages.error(request, f"Error mengambil data vaksin: {e}")
        return redirect('datavaksin:vaccine_data_list')

    if not current_vaksin:
        messages.error(request, f"Vaksin dengan ID '{kode_vaksin}' tidak ditemukan.")
        return redirect('datavaksin:vaccine_data_list')

    if request.method == 'POST':
        stok_baru_str = request.POST.get('stok', '').strip()
        stok_baru = None
        if not stok_baru_str:
            messages.error(request, "Stok tidak boleh kosong.")
            return redirect('datavaksin:vaccine_data_list')
        else:
            try:
                stok_baru = int(stok_baru_str)
                if stok_baru < 0:
                    messages.error(request, "Stok tidak boleh negatif.")
                    return redirect('datavaksin:vaccine_data_list')
            except ValueError:
                messages.error(request, "Stok harus berupa angka.")
                return redirect('datavaksin:vaccine_data_list')

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE PETCLINIC.VAKSIN SET stok = %s WHERE kode = %s",
                    [stok_baru, kode_vaksin]
                )
            messages.success(request, f"Stok vaksin '{current_vaksin['nama']}' berhasil diupdate menjadi {stok_baru}.")
        except DatabaseError as e:
            messages.error(request, f"Gagal mengupdate stok vaksin: {e}")
            
        return redirect('datavaksin:vaccine_data_list')
    
    return redirect('datavaksin:vaccine_data_list')


def vaccine_data_delete_view(request, kode_vaksin):
    
    
    
    if request.method == 'POST':
        nama_vaksin_temp = kode_vaksin
        try:
            with connection.cursor() as cursor:
                
                cursor.execute("SELECT 1 FROM PETCLINIC.KUNJUNGAN WHERE kode_vaksin = %s LIMIT 1", [kode_vaksin])
                is_used = cursor.fetchone()
                if is_used:
                    messages.error(request, f"Vaksin dengan ID '{kode_vaksin}' tidak dapat dihapus karena sudah digunakan dalam data kunjungan.")
                    return redirect('datavaksin:vaccine_data_list')

                
                cursor.execute("SELECT nama FROM PETCLINIC.VAKSIN WHERE kode = %s", [kode_vaksin])
                vaksin_row = cursor.fetchone()
                if vaksin_row:
                    nama_vaksin_temp = vaksin_row[0]
            
                cursor.execute("DELETE FROM PETCLINIC.VAKSIN WHERE kode = %s", [kode_vaksin])
                if cursor.rowcount == 0:
                    messages.warning(request, f"Vaksin dengan ID '{kode_vaksin}' tidak ditemukan untuk dihapus.")
                else:
                    messages.success(request, f"Vaksin '{nama_vaksin_temp}' (ID: {kode_vaksin}) berhasil dihapus.")
        
        except IntegrityError as e: 
             messages.error(request, f"Gagal menghapus vaksin '{nama_vaksin_temp}'. Constraint violation. Detail: {e}")
        except DatabaseError as e:
            messages.error(request, f"Gagal menghapus vaksin '{nama_vaksin_temp}': {e}")
        
        return redirect('datavaksin:vaccine_data_list')
    
    return redirect('datavaksin:vaccine_data_list')


def get_vaccine_details_json(request, kode_vaksin):
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT kode, nama, harga, stok FROM PETCLINIC.VAKSIN WHERE kode = %s", [kode_vaksin])
            vaksin = dictfetchone(cursor)
            if vaksin:
                return JsonResponse(vaksin)
            else:
                return JsonResponse({'error': 'Vaksin tidak ditemukan'}, status=404)
    except DatabaseError as e:
        return JsonResponse({'error': f'Kesalahan database: {str(e)}'}, status=500)