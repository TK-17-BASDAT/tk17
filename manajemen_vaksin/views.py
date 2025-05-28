from django.shortcuts import render, redirect
from django.db import connection, IntegrityError, DatabaseError, transaction
from django.contrib import messages
from django.urls import reverse 
from datetime import date, datetime
import locale
import uuid

# --- Pengaturan Locale (Opsional) ---
try:
    locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8') # Untuk Linux/macOS
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'Indonesian_Indonesia.1252') # Untuk Windows
    except locale.Error:
        print("Peringatan: Locale Bahasa Indonesia tidak ditemukan, menggunakan locale default.")
        pass

# --- Helper Functions ---
def format_tanggal_indonesia(tanggal_obj):
    """Memformat objek tanggal atau datetime ke string Bahasa Indonesia."""
    if isinstance(tanggal_obj, datetime):
        tanggal_obj = tanggal_obj.date()
    elif not isinstance(tanggal_obj, date):
        return str(tanggal_obj) 
    try:
        return tanggal_obj.strftime("%A, %d %B %Y").title()
    except ValueError: # Jika tahun terlalu kecil/besar untuk strftime locale tertentu
        return tanggal_obj.strftime("%Y-%m-%d")


def dictfetchall(cursor):
    """Mengembalikan semua baris dari cursor sebagai list of dictionaries."""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def dictfetchone(cursor):
    """Mengembalikan satu baris dari cursor sebagai dictionary, atau None jika tidak ada baris."""
    columns = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    return dict(zip(columns, row)) if row else None

# --- Views ---
def vaccination_list_view(request):
    """Menampilkan daftar vaksinasi yang sudah ada dan opsi untuk form."""
    vaccinations_data = []
    kunjungan_options_for_create = [] # Kunjungan yang BELUM ada vaksinnya
    vaksin_options = [] # Semua jenis vaksin yang tersedia

    try:
        with connection.cursor() as cursor:
            # 1. Ambil data Kunjungan yang SUDAH memiliki Vaksin (untuk tabel utama)
            query_existing_vaccinations = """
                SELECT
                    k.id_kunjungan, 
                    k.timestamp_awal,
                    k.kode_vaksin,
                    v.nama AS nama_vaksin,
                    h.nama AS nama_hewan_display 
                FROM PETCLINIC.KUNJUNGAN k
                JOIN PETCLINIC.VAKSIN v ON k.kode_vaksin = v.kode
                JOIN PETCLINIC.HEWAN h ON k.nama_hewan = h.nama AND k.no_identitas_klien = h.no_identitas_klien
                WHERE k.kode_vaksin IS NOT NULL
                ORDER BY k.timestamp_awal DESC;
            """
            cursor.execute(query_existing_vaccinations)
            for row in dictfetchall(cursor):
                vaccinations_data.append({
                    "kunjungan_id": str(row['id_kunjungan']), # Identifier utama untuk URL
                    "timestamp_awal": row['timestamp_awal'],
                    "tanggal_kunjungan_formatted": format_tanggal_indonesia(row['timestamp_awal']),
                    "vaksin_id": row['kode_vaksin'],
                    "vaksin_nama": row['nama_vaksin'],
                    "display_kunjungan": f"{str(row['id_kunjungan'])[:8]}... - {row['nama_hewan_display']}"
                })

            # 2. Ambil Kunjungan yang BELUM memiliki vaksin (untuk dropdown Create)
            query_kunjungan_no_vaksin = """
                SELECT
                    k.id_kunjungan,
                    h.nama as nama_hewan_display,
                    k.timestamp_awal
                FROM PETCLINIC.KUNJUNGAN k
                JOIN PETCLINIC.HEWAN h ON k.nama_hewan = h.nama AND k.no_identitas_klien = h.no_identitas_klien
                WHERE k.kode_vaksin IS NULL
                ORDER BY k.timestamp_awal DESC;
            """
            cursor.execute(query_kunjungan_no_vaksin)
            for row in dictfetchall(cursor):
                kunjungan_options_for_create.append({
                    "id": str(row['id_kunjungan']), # Value untuk <option>
                    "display_text": f"{str(row['id_kunjungan'])[:8]}... - {row['nama_hewan_display']} ({format_tanggal_indonesia(row['timestamp_awal'])})"
                })
            
            # 3. Ambil semua Vaksin yang tersedia (untuk dropdown)
            cursor.execute("SELECT kode, nama, stok FROM PETCLINIC.VAKSIN ORDER BY nama;")
            for row in dictfetchall(cursor):
                vaksin_options.append({
                    "id": row['kode'], "nama": row['nama'], "stok": row['stok']
                })
    except Exception as e:
        messages.error(request, f"Gagal memuat data vaksinasi: {e}")
        print(f"Database error in vaccination_list_view: {e}")

    context = {
        'vaccinations': vaccinations_data,
        'kunjungan_options_for_create': kunjungan_options_for_create,
        'vaksin_options': vaksin_options,
    }
    return render(request, 'manajemen_vaksin/vaksin.html', context)


def vaccination_create_view(request):
    """Menambahkan data vaksin ke sebuah kunjungan yang sudah ada."""
    if request.method == 'POST':
        kunjungan_id_to_update = request.POST.get('kunjungan_id') 
        vaksin_kode_to_add = request.POST.get('vaksin_id')

        print(f"DEBUG - Create vaccination:")
        print(f"  kunjungan_id: {kunjungan_id_to_update}")
        print(f"  vaksin_id: {vaksin_kode_to_add}")

        if not kunjungan_id_to_update or not vaksin_kode_to_add:
            messages.error(request, "Kunjungan dan Vaksin harus dipilih.")
            return redirect('manajemen_vaksin:vaccination_list')

        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # Validasi 1: Cek apakah kunjungan ada dan belum ada vaksin
                    cursor.execute("SELECT kode_vaksin FROM PETCLINIC.KUNJUNGAN WHERE id_kunjungan = %s", [kunjungan_id_to_update])
                    kunjungan_status = dictfetchone(cursor)
                    
                    print(f"DEBUG - Kunjungan status: {kunjungan_status}")
                    
                    if not kunjungan_status:
                        messages.error(request, f"Kunjungan dengan ID {kunjungan_id_to_update} tidak ditemukan.")
                        return redirect('manajemen_vaksin:vaccination_list')
                    if kunjungan_status.get('kode_vaksin') is not None:
                        messages.warning(request, f"Kunjungan {kunjungan_id_to_update[:8]}... sudah memiliki data vaksin.")
                        return redirect('manajemen_vaksin:vaccination_list')

                    # Validasi 2: Cek stok vaksin
                    cursor.execute("SELECT stok, nama FROM PETCLINIC.VAKSIN WHERE kode = %s", [vaksin_kode_to_add])
                    vaksin_info = dictfetchone(cursor)
                    
                    print(f"DEBUG - Vaksin info: {vaksin_info}")
                    
                    if not vaksin_info:
                        messages.error(request, f"Vaksin dengan kode {vaksin_kode_to_add} tidak ditemukan.")
                        return redirect('manajemen_vaksin:vaccination_list')
                    if vaksin_info['stok'] <= 0:
                        messages.error(request, f"Stok vaksin '{vaksin_info['nama']}' (Kode: {vaksin_kode_to_add}) habis.")
                        return redirect('manajemen_vaksin:vaccination_list')

                    # Operasi utama: Update Kunjungan dan Stok Vaksin
                    sql_update_kunjungan = "UPDATE PETCLINIC.KUNJUNGAN SET kode_vaksin = %s WHERE id_kunjungan = %s"
                    params_update_kunjungan = [vaksin_kode_to_add, kunjungan_id_to_update]
                    
                    cursor.execute(sql_update_kunjungan, params_update_kunjungan)
                    print(f"DEBUG - Update kunjungan rows affected: {cursor.rowcount}")

                    if cursor.rowcount > 0:
                        cursor.execute("UPDATE PETCLINIC.VAKSIN SET stok = stok - 1 WHERE kode = %s", [vaksin_kode_to_add])
                        print(f"DEBUG - Update vaksin stok rows affected: {cursor.rowcount}")
                        messages.success(request, f"Vaksin '{vaksin_info['nama']}' berhasil ditambahkan ke kunjungan {kunjungan_id_to_update[:8]}...")
                    else:
                        messages.error(request, f"Gagal mengupdate kunjungan {kunjungan_id_to_update[:8]}.... Kunjungan mungkin tidak ditemukan atau sudah memiliki vaksin.")
        
        except IntegrityError as e:
            print(f"DEBUG - IntegrityError: {e}")
            messages.error(request, f"Gagal menambahkan vaksinasi (Kesalahan Integritas Data): {e}")
        except DatabaseError as e:
            print(f"DEBUG - DatabaseError: {e}")
            messages.error(request, f"Gagal menambahkan vaksinasi (Kesalahan Database): {e}")
        except Exception as e:
            print(f"DEBUG - Exception: {e}")
            messages.error(request, f"Terjadi kesalahan tidak terduga: {e}")
        
        return redirect('manajemen_vaksin:vaccination_list')

    return redirect('manajemen_vaksin:vaccination_list')


def vaccination_update_view(request, kunjungan_id):  # <- Ubah dari kunjungan_id_pk ke kunjungan_id
    """Mengubah jenis vaksin pada kunjungan yang sudah ada vaksinasinya."""
    if request.method == 'POST':
        new_vaksin_kode = request.POST.get('vaksin_id')

        print(f"DEBUG - Update vaccination:")
        print(f"  kunjungan_id: {kunjungan_id}")  # <- Update variable name
        print(f"  new_vaksin_kode: {new_vaksin_kode}")

        if not new_vaksin_kode:
            messages.error(request, "Vaksin baru harus dipilih untuk update.")
            return redirect('manajemen_vaksin:vaccination_list')
        
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # 1. Dapatkan kode vaksin lama dari kunjungan ini (untuk mengembalikan stok)
                    cursor.execute("SELECT kode_vaksin FROM PETCLINIC.KUNJUNGAN WHERE id_kunjungan = %s", [kunjungan_id])
                    kunjungan_data = dictfetchone(cursor)
                    
                    print(f"DEBUG - Current kunjungan data: {kunjungan_data}")
                    
                    if not kunjungan_data:
                        messages.error(request, f"Kunjungan dengan ID {str(kunjungan_id)[:8]}... tidak ditemukan.")
                        return redirect('manajemen_vaksin:vaccination_list')
                    
                    old_vaksin_kode = kunjungan_data.get('kode_vaksin')

                    if old_vaksin_kode == new_vaksin_kode:
                        messages.info(request, "Tidak ada perubahan vaksin.")
                        return redirect('manajemen_vaksin:vaccination_list')

                    # 2. Cek stok vaksin BARU
                    cursor.execute("SELECT stok, nama FROM PETCLINIC.VAKSIN WHERE kode = %s", [new_vaksin_kode])
                    new_vaksin_info = dictfetchone(cursor)
                    
                    print(f"DEBUG - New vaksin info: {new_vaksin_info}")
                    
                    if not new_vaksin_info:
                        messages.error(request, f"Vaksin baru dengan kode {new_vaksin_kode} tidak ditemukan.")
                        return redirect('manajemen_vaksin:vaccination_list')
                    if new_vaksin_info['stok'] <= 0:
                        messages.error(request, f"Stok vaksin baru '{new_vaksin_info['nama']}' (Kode: {new_vaksin_kode}) habis.")
                        return redirect('manajemen_vaksin:vaccination_list')

                    # Operasi utama
                    cursor.execute("UPDATE PETCLINIC.KUNJUNGAN SET kode_vaksin = %s WHERE id_kunjungan = %s", [new_vaksin_kode, kunjungan_id])
                    print(f"DEBUG - Update kunjungan rows affected: {cursor.rowcount}")

                    if cursor.rowcount > 0:
                        # Kembalikan stok vaksin LAMA (jika ada dan berbeda dari yang baru)
                        if old_vaksin_kode:
                            cursor.execute("UPDATE PETCLINIC.VAKSIN SET stok = stok + 1 WHERE kode = %s", [old_vaksin_kode])
                            print(f"DEBUG - Return old vaksin stok rows affected: {cursor.rowcount}")
                        
                        # Kurangi stok vaksin BARU
                        cursor.execute("UPDATE PETCLINIC.VAKSIN SET stok = stok - 1 WHERE kode = %s", [new_vaksin_kode])
                        print(f"DEBUG - Reduce new vaksin stok rows affected: {cursor.rowcount}")
                        
                        messages.success(request, f"Vaksinasi untuk kunjungan {str(kunjungan_id)[:8]}... berhasil diupdate ke '{new_vaksin_info['nama']}'.")
                    else:
                        messages.warning(request, f"Tidak ada data vaksinasi yang diupdate untuk kunjungan {str(kunjungan_id)[:8]}....")

        except DatabaseError as e:
            print(f"DEBUG - DatabaseError: {e}")
            messages.error(request, f"Gagal mengupdate vaksinasi (Kesalahan Database): {e}")
        except Exception as e:
            print(f"DEBUG - Exception: {e}")
            messages.error(request, f"Terjadi kesalahan tidak terduga saat update: {e}")
        
        return redirect('manajemen_vaksin:vaccination_list')

    return redirect('manajemen_vaksin:vaccination_list')


def vaccination_delete_view(request, kunjungan_id):  # <- Ubah dari kunjungan_id_pk ke kunjungan_id
    """Menghapus (membatalkan) vaksinasi dari sebuah kunjungan dengan set kode_vaksin menjadi NULL."""
    if request.method == 'POST':
        print(f"DEBUG - Delete vaccination:")
        print(f"  kunjungan_id: {kunjungan_id}")  # <- Update variable name
        
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # 1. Dapatkan kode vaksin yang akan dihapus untuk mengembalikan stoknya
                    cursor.execute("SELECT kode_vaksin FROM PETCLINIC.KUNJUNGAN WHERE id_kunjungan = %s", [kunjungan_id])
                    kunjungan_data = dictfetchone(cursor)

                    print(f"DEBUG - Kunjungan data to delete: {kunjungan_data}")

                    if not kunjungan_data:
                        messages.error(request, f"Kunjungan dengan ID {str(kunjungan_id)[:8]}... tidak ditemukan.")
                        return redirect('manajemen_vaksin:vaccination_list')
                    
                    vaksin_kode_to_return = kunjungan_data.get('kode_vaksin')

                    if not vaksin_kode_to_return:
                        messages.warning(request, f"Kunjungan {str(kunjungan_id)[:8]}... tidak memiliki data vaksinasi untuk dihapus.")
                        return redirect('manajemen_vaksin:vaccination_list')

                    # Operasi utama
                    cursor.execute("UPDATE PETCLINIC.KUNJUNGAN SET kode_vaksin = NULL WHERE id_kunjungan = %s", [kunjungan_id])
                    print(f"DEBUG - Delete vaccination rows affected: {cursor.rowcount}")

                    if cursor.rowcount > 0:
                        # Kembalikan stok vaksin yang dibatalkan
                        cursor.execute("UPDATE PETCLINIC.VAKSIN SET stok = stok + 1 WHERE kode = %s", [vaksin_kode_to_return])
                        print(f"DEBUG - Return vaksin stok rows affected: {cursor.rowcount}")
                        messages.success(request, f"Vaksinasi untuk kunjungan {str(kunjungan_id)[:8]}... berhasil dibatalkan.")
                    else:
                        messages.warning(request, f"Tidak ada data vaksinasi yang dibatalkan untuk kunjungan {str(kunjungan_id)[:8]}.... Mungkin sudah dibatalkan.")
        
        except DatabaseError as e:
            print(f"DEBUG - DatabaseError: {e}")
            messages.error(request, f"Gagal membatalkan vaksinasi (Kesalahan Database): {e}")
        except Exception as e:
            print(f"DEBUG - Exception: {e}")
            messages.error(request, f"Terjadi kesalahan tidak terduga saat pembatalan: {e}")

        return redirect('manajemen_vaksin:vaccination_list')

    return redirect('manajemen_vaksin:vaccination_list')