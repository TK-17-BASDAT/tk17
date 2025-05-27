# datavaksin/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse, Http404 # Http404 jika data tidak ditemukan
from django.urls import reverse
from django.contrib import messages
from django.db import connection, IntegrityError, DatabaseError # Untuk eksekusi SQL dan menangani error DB

# Helper function untuk mengubah hasil cursor menjadi list of dict
def dictfetchall(cursor):
    """Return all rows from a cursor as a list of dictionaries."""
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def dictfetchone(cursor):
    """Return one row from a cursor as a dictionary."""
    columns = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    if row:
        return dict(zip(columns, row))
    return None


def vaccine_data_list_view(request):
    vaksin_list = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT kode, nama, harga, stok FROM PETCLINIC.VAKSIN ORDER BY kode")
            vaksin_list = dictfetchall(cursor)
    except DatabaseError as e:
        messages.error(request, f"Gagal mengambil data vaksin: {e}")

    context = {
        'vaksin_list': vaksin_list,
        # Form create tidak lagi berbasis Django Form, jadi dikosongkan atau dihandle murni di frontend
    }
    return render(request, 'datavaksin/datavaksin.html', context)

def vaccine_data_create_view(request):
    if request.method == 'POST':
        kode = request.POST.get('kode')
        nama = request.POST.get('nama')
        harga_str = request.POST.get('harga')
        stok_str = request.POST.get('stok')

        # --- Validasi Manual Sederhana ---
        errors = []
        if not kode:
            errors.append("Kode vaksin tidak boleh kosong.")
        if not nama:
            errors.append("Nama vaksin tidak boleh kosong.")
        
        harga = None
        if harga_str:
            try:
                harga = int(harga_str)
                if harga < 0:
                    errors.append("Harga tidak boleh negatif.")
            except ValueError:
                errors.append("Harga harus berupa angka.")
        else:
            errors.append("Harga tidak boleh kosong.")

        stok = None
        if stok_str:
            try:
                stok = int(stok_str)
                if stok < 0:
                    errors.append("Stok tidak boleh negatif.")
            except ValueError:
                errors.append("Stok harus berupa angka.")
        else:
            errors.append("Stok tidak boleh kosong.")
        # --- Akhir Validasi ---

        if errors:
            for error in errors:
                messages.error(request, error)
            # Untuk mengisi kembali form di modal dengan data yang salah, ini jadi kompleks.
            # Biasanya, frontend akan menangani ini dengan AJAX dan menerima response JSON.
            # Untuk non-AJAX, kita redirect dan user harus input ulang.
            return redirect('datavaksin:vaccine_data_list')

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO PETCLINIC.VAKSIN (kode, nama, harga, stok) VALUES (%s, %s, %s, %s)",
                    [kode, nama, harga, stok]
                )
            messages.success(request, f"Vaksin '{nama}' berhasil ditambahkan.")
        except IntegrityError: # Tangkap error jika kode vaksin sudah ada (PK violation)
            messages.error(request, f"Gagal menambahkan vaksin. Kode vaksin '{kode}' sudah ada.")
        except DatabaseError as e:
            messages.error(request, f"Gagal menambahkan vaksin ke database: {e}")
        
        return redirect('datavaksin:vaccine_data_list')
    
    return redirect('datavaksin:vaccine_data_list') # Jika bukan POST

def vaccine_data_update_view(request, kode_vaksin):
    # Cek dulu apakah vaksin ada
    vaksin_instance = None
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT kode, nama, harga, stok FROM PETCLINIC.VAKSIN WHERE kode = %s", [kode_vaksin])
            vaksin_instance = dictfetchone(cursor)
    except DatabaseError as e:
        messages.error(request, f"Error saat mengambil data vaksin: {e}")
        return redirect('datavaksin:vaccine_data_list')

    if not vaksin_instance:
        messages.error(request, f"Vaksin dengan kode '{kode_vaksin}' tidak ditemukan.")
        return redirect('datavaksin:vaccine_data_list')

    if request.method == 'POST':
        # Form yang di-submit untuk update info biasanya hanya nama dan harga
        nama_baru = request.POST.get('nama')
        harga_baru_str = request.POST.get('harga')

        # --- Validasi Manual Sederhana ---
        errors = []
        if not nama_baru:
            errors.append("Nama vaksin tidak boleh kosong.")
        
        harga_baru = None
        if harga_baru_str:
            try:
                harga_baru = int(harga_baru_str)
                if harga_baru < 0:
                    errors.append("Harga tidak boleh negatif.")
            except ValueError:
                errors.append("Harga harus berupa angka.")
        else:
            errors.append("Harga tidak boleh kosong.")
        # --- Akhir Validasi ---

        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('datavaksin:vaccine_data_list') # Atau render template error

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE PETCLINIC.VAKSIN SET nama = %s, harga = %s WHERE kode = %s",
                    [nama_baru, harga_baru, kode_vaksin]
                )
            messages.success(request, f"Info vaksin '{nama_baru}' (kode: {kode_vaksin}) berhasil diupdate.")
        except DatabaseError as e:
            messages.error(request, f"Gagal mengupdate info vaksin: {e}")

        return redirect('datavaksin:vaccine_data_list')
    
    # Jika GET, dan tidak menggunakan JS untuk prefill modal,
    # kamu bisa mengirim vaksin_instance ke template untuk form yang terpisah.
    # Namun, karena modal JS biasanya mengisi ini, redirect saja.
    return redirect('datavaksin:vaccine_data_list')


def vaccine_stock_update_view(request, kode_vaksin):
    vaksin_instance = None
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT kode, nama, stok FROM PETCLINIC.VAKSIN WHERE kode = %s", [kode_vaksin])
            vaksin_instance = dictfetchone(cursor)
    except DatabaseError as e:
        messages.error(request, f"Error saat mengambil data vaksin: {e}")
        return redirect('datavaksin:vaccine_data_list')

    if not vaksin_instance:
        messages.error(request, f"Vaksin dengan kode '{kode_vaksin}' tidak ditemukan.")
        return redirect('datavaksin:vaccine_data_list')

    if request.method == 'POST':
        stok_baru_str = request.POST.get('stok')
        
        stok_baru = None
        try:
            stok_baru = int(stok_baru_str)
            if stok_baru < 0:
                messages.error(request, "Stok tidak boleh negatif.")
                return redirect('datavaksin:vaccine_data_list')
        except (ValueError, TypeError): # TypeError jika stok_baru_str adalah None
            messages.error(request, "Stok harus berupa angka.")
            return redirect('datavaksin:vaccine_data_list')

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE PETCLINIC.VAKSIN SET stok = %s WHERE kode = %s",
                    [stok_baru, kode_vaksin]
                )
            messages.success(request, f"Stok vaksin '{vaksin_instance['nama']}' berhasil diupdate menjadi {stok_baru}.")
        except DatabaseError as e:
            messages.error(request, f"Gagal mengupdate stok vaksin: {e}")
            
        return redirect('datavaksin:vaccine_data_list')
    
    return redirect('datavaksin:vaccine_data_list')


def vaccine_data_delete_view(request, kode_vaksin):
    if request.method == 'POST': # Pastikan ini benar-benar konfirmasi delete
        nama_vaksin_temp = kode_vaksin # Untuk message jika gagal ambil nama
        try:
            # Opsional: Ambil nama dulu untuk pesan yang lebih baik
            with connection.cursor() as cursor_select:
                cursor_select.execute("SELECT nama FROM PETCLINIC.VAKSIN WHERE kode = %s", [kode_vaksin])
                vaksin_row = cursor_select.fetchone()
                if vaksin_row:
                    nama_vaksin_temp = vaksin_row[0]
            
            with connection.cursor() as cursor_delete:
                cursor_delete.execute("DELETE FROM PETCLINIC.VAKSIN WHERE kode = %s", [kode_vaksin])
                if cursor_delete.rowcount == 0: # Tidak ada baris yang terhapus
                    messages.warning(request, f"Vaksin dengan kode '{kode_vaksin}' tidak ditemukan untuk dihapus.")
                else:
                    messages.success(request, f"Vaksin '{nama_vaksin_temp}' (kode: {kode_vaksin}) berhasil dihapus.")
        
        except IntegrityError as e: # Tangkap error foreign key constraint
             messages.error(request, f"Gagal menghapus vaksin '{nama_vaksin_temp}'. Kemungkinan vaksin ini masih terikat dengan data lain (misalnya data kunjungan). Detail: {e}")
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
    except DatabaseError:
        return JsonResponse({'error': 'Kesalahan database saat mengambil detail vaksin'}, status=500)