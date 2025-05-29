# manajemen_vaksin views.py
from django.shortcuts import render, redirect
from django.db import connection, IntegrityError, DatabaseError, transaction # Pastikan DatabaseError diimpor
from django.contrib import messages
from django.urls import reverse
from datetime import date, datetime
import locale
import uuid
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

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
    if isinstance(tanggal_obj, datetime):
        tanggal_obj = tanggal_obj.date()
    elif not isinstance(tanggal_obj, date):
        return str(tanggal_obj)
    try:
        return tanggal_obj.strftime("%A, %d %B %Y").title()
    except ValueError:
        return tanggal_obj.strftime("%Y-%m-%d")

def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def dictfetchone(cursor):
    columns = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    return dict(zip(columns, row)) if row else None

# --- Views ---
def vaccination_list_view(request):
    vaccinations_data = []
    kunjungan_options_for_create = []
    vaksin_options = []

    try:
        with connection.cursor() as cursor:
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
                    "kunjungan_id": str(row['id_kunjungan']),
                    "timestamp_awal": row['timestamp_awal'],
                    "tanggal_kunjungan_formatted": format_tanggal_indonesia(row['timestamp_awal']),
                    "vaksin_id": row['kode_vaksin'],
                    "vaksin_nama": row['nama_vaksin'],
                    "display_kunjungan": f"{str(row['id_kunjungan'])[:8]}... - {row['nama_hewan_display']}"
                })

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
                    "id": str(row['id_kunjungan']),
                    "display_text": f"{str(row['id_kunjungan'])[:8]}... - {row['nama_hewan_display']} ({format_tanggal_indonesia(row['timestamp_awal'])})"
                })

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
    if request.method == 'POST':
        kunjungan_id_to_update = request.POST.get('kunjungan_id') 
        vaksin_kode_to_add = request.POST.get('vaksin_id')

        if not kunjungan_id_to_update or not vaksin_kode_to_add:
            messages.error(request, "Kunjungan dan Vaksin harus dipilih.")
            return redirect('manajemen_vaksin:vaccination_list')

        try:
            # Tidak perlu cek stok di sini lagi, biarkan trigger yang handle
            # with connection.cursor() as cursor:
            #     cursor.execute("SELECT stok, nama FROM PETCLINIC.VAKSIN WHERE kode = %s", [vaksin_kode_to_add])
            #     vaksin_info = dictfetchone(cursor)
            #     if not vaksin_info:
            #         messages.error(request, f"Vaksin dengan kode {vaksin_kode_to_add} tidak ditemukan.")
            #         return redirect('manajemen_vaksin:vaccination_list')
            #     if vaksin_info['stok'] <= 0: # Validasi stok di sisi aplikasi DIHAPUS
            #         messages.error(request, f"Stok vaksin '{vaksin_info['nama']}' (Kode: {vaksin_kode_to_add}) habis.")
            #         return redirect('manajemen_vaksin:vaccination_list')
            
            # Langsung lakukan operasi database, biarkan trigger yang bekerja
            with transaction.atomic(): # Pastikan operasi update KUNJUNGAN dan VAKSIN (oleh trigger) atomik
                with connection.cursor() as cursor:
                    # Cek dulu apakah kunjungan memang belum ada vaksinnya
                    cursor.execute("SELECT kode_vaksin, id_kunjungan FROM PETCLINIC.KUNJUNGAN WHERE id_kunjungan = %s", [kunjungan_id_to_update])
                    kunjungan_status = dictfetchone(cursor)
                    if not kunjungan_status:
                        messages.error(request, f"Kunjungan dengan ID {kunjungan_id_to_update} tidak ditemukan.")
                        return redirect('manajemen_vaksin:vaccination_list')
                    if kunjungan_status.get('kode_vaksin') is not None:
                        messages.warning(request, f"Kunjungan {str(kunjungan_status['id_kunjungan'])[:8]}... sudah memiliki data vaksin.")
                        return redirect('manajemen_vaksin:vaccination_list')


                    sql_update_kunjungan = "UPDATE PETCLINIC.KUNJUNGAN SET kode_vaksin = %s WHERE id_kunjungan = %s"
                    cursor.execute(sql_update_kunjungan, [vaksin_kode_to_add, kunjungan_id_to_update])

                    if cursor.rowcount > 0:
                        # Pengurangan stok sekarang ditangani oleh trigger, jadi tidak perlu query UPDATE VAKSIN di sini
                        # Cukup tampilkan pesan sukses
                        # Ambil nama vaksin untuk pesan sukses
                        cursor.execute("SELECT nama FROM PETCLINIC.VAKSIN WHERE kode = %s", [vaksin_kode_to_add])
                        vaksin_nama_for_msg = dictfetchone(cursor)['nama'] if cursor.rowcount > 0 else vaksin_kode_to_add
                        messages.success(request, f"Vaksin '{vaksin_nama_for_msg}' berhasil ditambahkan ke kunjungan {kunjungan_id_to_update[:8]}...")
                    else:
                        messages.error(request, f"Gagal mengupdate kunjungan {kunjungan_id_to_update[:8]}.... Kunjungan mungkin tidak ditemukan atau sudah memiliki vaksin.")
        
        except (IntegrityError, DatabaseError) as e: # Tangkap error dari DB, termasuk dari trigger
            # Pesan error dari trigger (RAISE EXCEPTION) akan ada di e
            error_message = str(e)
            # Cek apakah pesan mengandung format error stok dari trigger
            if "tidak mencukupi untuk vaksinasi" in error_message or "Vaksin dengan kode" in error_message and "tidak ditemukan" in error_message :
                messages.error(request, error_message) # Tampilkan pesan error dari trigger
            else:
                messages.error(request, f"Gagal menambahkan vaksinasi: {error_message}")
            print(f"Error creating vaccination: {error_message}")
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan tidak terduga: {e}")
            print(f"Unexpected error creating vaccination: {e}")
        
        return redirect('manajemen_vaksin:vaccination_list')

    return redirect('manajemen_vaksin:vaccination_list')


def vaccination_update_view(request, kunjungan_id):
    if request.method == 'POST':
        new_vaksin_kode = request.POST.get('vaksin_id')

        if not new_vaksin_kode:
            messages.error(request, "Vaksin baru harus dipilih untuk update.")
            return redirect('manajemen_vaksin:vaccination_list')
        
        try:
            # Tidak perlu cek stok di sini lagi, biarkan trigger yang handle
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # Dapatkan kode vaksin lama (trigger akan mengembalikan stoknya)
                    # dan pastikan kunjungan ada
                    cursor.execute("SELECT kode_vaksin FROM PETCLINIC.KUNJUNGAN WHERE id_kunjungan = %s", [kunjungan_id])
                    kunjungan_data = dictfetchone(cursor)
                    
                    if not kunjungan_data:
                        messages.error(request, f"Kunjungan dengan ID {str(kunjungan_id)[:8]}... tidak ditemukan.")
                        return redirect('manajemen_vaksin:vaccination_list')
                    
                    old_vaksin_kode = kunjungan_data.get('kode_vaksin')

                    if old_vaksin_kode == new_vaksin_kode:
                        messages.info(request, "Tidak ada perubahan vaksin.")
                        return redirect('manajemen_vaksin:vaccination_list')

                    # Langsung update, trigger akan menangani stok lama dan baru
                    cursor.execute("UPDATE PETCLINIC.KUNJUNGAN SET kode_vaksin = %s WHERE id_kunjungan = %s", [new_vaksin_kode, kunjungan_id])

                    if cursor.rowcount > 0:
                        # Ambil nama vaksin baru untuk pesan
                        cursor.execute("SELECT nama FROM PETCLINIC.VAKSIN WHERE kode = %s", [new_vaksin_kode])
                        vaksin_nama_for_msg = dictfetchone(cursor)['nama'] if cursor.rowcount > 0 else new_vaksin_kode
                        messages.success(request, f"Vaksinasi untuk kunjungan {str(kunjungan_id)[:8]}... berhasil diupdate ke '{vaksin_nama_for_msg}'.")
                    else:
                        messages.warning(request, f"Tidak ada data vaksinasi yang diupdate untuk kunjungan {str(kunjungan_id)[:8]}....")

        except (IntegrityError, DatabaseError) as e:
            error_message = str(e)
            if "tidak mencukupi untuk vaksinasi" in error_message or "Vaksin dengan kode" in error_message and "tidak ditemukan" in error_message or "tidak mencukupi untuk penggantian vaksinasi" in error_message :
                messages.error(request, error_message)
            else:
                messages.error(request, f"Gagal mengupdate vaksinasi: {error_message}")
            print(f"Error updating vaccination for {kunjungan_id}: {error_message}")
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan tidak terduga saat update: {e}")
            print(f"Unexpected error updating vaccination for {kunjungan_id}: {e}")
        
        return redirect('manajemen_vaksin:vaccination_list')

    return redirect('manajemen_vaksin:vaccination_list')


def vaccination_delete_view(request, kunjungan_id):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # 1. Dapatkan kode vaksin yang akan dihapus (opsional, untuk info)
                    cursor.execute("SELECT kode_vaksin FROM PETCLINIC.KUNJUNGAN WHERE id_kunjungan = %s", [kunjungan_id])
                    kunjungan_data = dictfetchone(cursor)

                    if not kunjungan_data:
                        messages.error(request, f"Kunjungan dengan ID {str(kunjungan_id)[:8]}... tidak ditemukan.")
                        return redirect('manajemen_vaksin:vaccination_list')

                    vaksin_kode_to_return = kunjungan_data.get('kode_vaksin')

                    if not vaksin_kode_to_return:
                        messages.warning(request, f"Kunjungan {str(kunjungan_id)[:8]}... tidak memiliki data vaksinasi untuk dihapus.")
                        return redirect('manajemen_vaksin:vaccination_list')

                    # Operasi utama: Set kode_vaksin ke NULL. Trigger akan menangani pengembalian stok.
                    cursor.execute("UPDATE PETCLINIC.KUNJUNGAN SET kode_vaksin = NULL WHERE id_kunjungan = %s", [kunjungan_id])

                    if cursor.rowcount > 0:
                        messages.success(request, f"Vaksinasi untuk kunjungan {str(kunjungan_id)[:8]}... berhasil dibatalkan.")
                    else:
                        messages.warning(request, f"Tidak ada data vaksinasi yang dibatalkan untuk kunjungan {str(kunjungan_id)[:8]}....")

        except DatabaseError as e:
            # Error dari trigger seharusnya tidak terjadi di sini kecuali ada masalah dengan trigger itu sendiri
            # saat mengembalikan stok (misal vaksinnya terhapus dari tabel VAKSIN secara bersamaan)
            error_message = str(e)
            if "ERROR:" in error_message:
                error_message = error_message.split("ERROR:", 1)[1].split("CONTEXT:",1)[0].split("DETAIL:",1)[0].strip()
            messages.error(request, f"Gagal membatalkan vaksinasi: {error_message}")
            print(f"DEBUG - DatabaseError in delete: {e}")
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan tidak terduga saat pembatalan: {e}")
            print(f"DEBUG - Exception in delete: {e}")

        return redirect('manajemen_vaksin:vaccination_list')

    return redirect('manajemen_vaksin:vaccination_list')


class ClientPetVaccinationHistoryView(LoginRequiredMixin, View):
    login_url = '/auth/login/'
    template_name = 'manajemen_vaksin/vaksin_klien.html'

    def get(self, request):
        no_identitas_klien_str = request.session.get('no_identitas')
        user_role = request.session.get('user_role')

        if not no_identitas_klien_str or user_role not in ['klien_individu', 'klien_perusahaan']:
            messages.error(request, "Akses ditolak. Anda harus login sebagai klien untuk melihat halaman ini.")
            return redirect('dashboard:index')

        filter_pet_name = request.GET.get('pet_name', '').strip()
        filter_vaccine_kode = request.GET.get('vaccine_kode', '').strip()

        vaccination_history_list = []
        pet_options_for_filter = []
        vaccine_options_for_filter = []

        try:
            with connection.cursor() as cursor:
                query_client_pets = """
                    SELECT DISTINCT h.nama
                    FROM PETCLINIC.HEWAN h
                    WHERE h.no_identitas_klien = %s
                    ORDER BY h.nama;
                """
                cursor.execute(query_client_pets, [no_identitas_klien_str])
                for row in cursor.fetchall():
                    pet_options_for_filter.append(row[0])

                query_client_used_vaccines = """
                    SELECT DISTINCT v.kode, v.nama
                    FROM PETCLINIC.VAKSIN v
                    JOIN PETCLINIC.KUNJUNGAN k ON v.kode = k.kode_vaksin
                    WHERE k.no_identitas_klien = %s AND k.kode_vaksin IS NOT NULL
                    ORDER BY v.nama;
                """
                cursor.execute(query_client_used_vaccines, [no_identitas_klien_str])
                for row in dictfetchall(cursor):
                    vaccine_options_for_filter.append({'kode': row['kode'], 'nama': row['nama']})

                base_query_history = """
                    SELECT
                        h.nama AS nama_hewan,
                        v.nama AS nama_vaksin,
                        v.kode AS kode_vaksin,
                        v.harga AS harga_vaksin,
                        k.timestamp_awal AS tanggal_vaksinasi
                    FROM
                        PETCLINIC.KUNJUNGAN k
                    JOIN
                        PETCLINIC.HEWAN h ON k.nama_hewan = h.nama AND k.no_identitas_klien = h.no_identitas_klien
                    JOIN
                        PETCLINIC.VAKSIN v ON k.kode_vaksin = v.kode
                    WHERE
                        k.no_identitas_klien = %s AND k.kode_vaksin IS NOT NULL
                """
                params_history = [no_identitas_klien_str]
                conditions_history = []

                if filter_pet_name:
                    conditions_history.append("h.nama = %s")
                    params_history.append(filter_pet_name)

                if filter_vaccine_kode:
                    conditions_history.append("v.kode = %s")
                    params_history.append(filter_vaccine_kode)

                if conditions_history:
                    base_query_history += " AND " + " AND ".join(conditions_history)

                base_query_history += " ORDER BY k.timestamp_awal DESC, h.nama;"

                cursor.execute(base_query_history, params_history)
                for row_hist in dictfetchall(cursor):
                    tanggal_formatted = format_tanggal_indonesia(row_hist['tanggal_vaksinasi'])
                    waktu_formatted = row_hist['tanggal_vaksinasi'].strftime("%H:%M")

                    vaccination_history_list.append({
                        'nama_hewan': row_hist['nama_hewan'],
                        'nama_vaksin': row_hist['nama_vaksin'],
                        'kode_vaksin': row_hist['kode_vaksin'],
                        'harga_vaksin': row_hist['harga_vaksin'],
                        'tanggal_waktu_vaksinasi_formatted': f"{tanggal_formatted} {waktu_formatted}"
                    })

        except Exception as e:
            messages.error(request, f"Gagal memuat riwayat vaksinasi hewan Anda: {e}")
            print(f"Error in ClientPetVaccinationHistoryView: {e}")
            vaccination_history_list = []
            pet_options_for_filter = []
            vaccine_options_for_filter = []

        context = {
            'vaccination_history_list': vaccination_history_list,
            'pet_options_for_filter': pet_options_for_filter,
            'vaccine_options_for_filter': vaccine_options_for_filter,
            'current_filter_pet_name': filter_pet_name,
            'current_filter_vaccine_kode': filter_vaccine_kode,
        }
        return render(request, self.template_name, context)