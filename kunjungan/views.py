import uuid
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.db import connection

# Helper untuk cek role
def is_front_desk(user):
    return user.groups.filter(name='FrontDesk').exists()

@login_required
def kunjungan_view(request):
    # Coba ambil role dari session (jika dashboard menyimpannya)
    user_role = request.session.get('role')  # Ganti 'role' dengan kunci session yang benar jika diketahui

    # Jika tidak ada di session, tentukan role berdasarkan tabel PEGAWAI
    if not user_role:
        try:
            with connection.cursor() as cursor:
                # Cek apakah pengguna adalah dokter
                cursor.execute(
                    "SELECT 1 FROM PEGAWAI p JOIN DOKTER_HEWAN d ON p.no_pegawai = d.no_dokter_hewan WHERE p.email_user = %s",
                    [request.user.email]
                )
                is_dokter = cursor.fetchone() is not None
                if is_dokter:
                    user_role = 'dokter_hewan'
                else:
                    # Cek apakah pengguna adalah front desk
                    cursor.execute(
                        "SELECT 1 FROM PEGAWAI p JOIN FRONT_DESK f ON p.no_pegawai = f.no_front_desk WHERE p.email_user = %s",
                        [request.user.email]
                    )
                    is_front_desk = cursor.fetchone() is not None
                    if is_front_desk:
                        user_role = 'front_desk'
                    else:
                        # Default ke klien
                        user_role = 'klien'
        except Exception as e:
            print(f"Error checking role: {str(e)}")
            user_role = 'klien'

    # Simpan role ke session
    request.session['user_role'] = user_role
    request.session.modified = True
    print(f"User role set to: {user_role}")

    kunjungans = []
    kliens = []
    dokters = []
    perawats = []

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan, tipe_kunjungan, timestamp_awal, timestamp_akhir, suhu, berat_badan, catatan FROM KUNJUNGAN"
            )
            kunjungans = [
                {
                    'id_kunjungan': row[0],
                    'nama_hewan': row[1],
                    'no_identitas_klien': row[2],
                    'no_front_desk': row[3],
                    'no_perawat_hewan': row[4],
                    'no_dokter_hewan': row[5],
                    'tipe_kunjungan': row[6],
                    'timestamp_awal': row[7],
                    'timestamp_akhir': row[8],
                    'suhu': row[9],
                    'berat_badan': row[10],
                    'catatan': row[11]
                } for row in cursor.fetchall()
            ]
            
            cursor.execute("SELECT no_identitas FROM KLIEN")
            kliens = [{'no_identitas': row[0]} for row in cursor.fetchall()]
            
            cursor.execute("SELECT p.no_pegawai AS no_dokter_hewan, p.email_user FROM PEGAWAI p JOIN DOKTER_HEWAN d ON d.no_dokter_hewan = p.no_pegawai")
            dokters = [{'no_dokter_hewan': row[0], 'email': row[1]} for row in cursor.fetchall()]
            
            cursor.execute("SELECT p.no_pegawai AS no_perawat_hewan, p.email_user FROM PEGAWAI p JOIN PERAWAT_HEWAN d ON d.no_perawat_hewan = p.no_pegawai")
            perawats = [{'no_perawat_hewan': row[0], 'email': row[1]} for row in cursor.fetchall()]
            
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        kunjungans = []

    # Filter kunjungan untuk klien
    if user_role == 'klien':
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT no_identitas FROM KLIEN WHERE email = %s", [request.user.email])
                klien_id = cursor.fetchone()
                if klien_id:
                    kunjungans = [k for k in kunjungans if k['no_identitas_klien'] == klien_id[0]]
        except Exception as e:
            print(f"Error filtering kunjungan: {str(e)}")

    return render(request, 'kunjungan/kunjungan.html', {
        'kunjungans': kunjungans,
        'kliens': kliens,
        'dokters': dokters,
        'perawats': perawats,
        'user_role': user_role
    })

@login_required
def kunjungan_create(request):
    if request.method == 'POST':
        with connection.cursor() as cursor:
            # Ambil no_front_desk dari user yang login
            cursor.execute("SELECT p.no_pegawai, p.email_user FROM PEGAWAI p JOIN FRONT_DESK fd ON fd.no_front_desk = p.no_pegawai WHERE email_user = %s", [request.user.email])
            no_front_desk = cursor.fetchone()
            if not no_front_desk:
                messages.error(request, 'Front Desk tidak ditemukan!')
                return redirect('kunjungan:kunjungan_view')
                
            cursor.execute(
                "INSERT INTO KUNJUNGAN (id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan, tipe_kunjungan, timestamp_awal, timestamp_akhir) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                [
                    str(uuid.uuid4()),
                    request.POST['nama_hewan'],
                    request.POST['no_identitas_klien'],
                    no_front_desk[0],
                    request.POST['no_perawat_hewan'],
                    request.POST['no_dokter_hewan'],
                    request.POST['tipe_kunjungan'],
                    request.POST['timestamp_awal'],
                    request.POST['timestamp_akhir']
                ]
            )
            messages.success(request, 'Kunjungan berhasil dibuat!')
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def kunjungan_update(request, id_kunjungan):
    if request.method == 'POST':
        with connection.cursor() as cursor:
            # Ambil no_front_desk dari user yang login
            cursor.execute("SELECT p.no_pegawai, p.email_user FROM PEGAWAI p JOIN FRONT_DESK fd ON fd.no_front_desk = p.no_pegawai WHERE email_user = %s", [request.user.email])
            no_front_desk = cursor.fetchone()
            if not no_front_desk:
                messages.error(request, 'Front Desk tidak ditemukan!')
                return JsonResponse({'status': 'error'}, status=400)
                
            cursor.execute(
                "UPDATE KUNJUNGAN SET nama_hewan = %s, no_identitas_klien = %s, no_front_desk = %s, no_perawat_hewan = %s, no_dokter_hewan = %s, tipe_kunjungan = %s, timestamp_awal = %s, timestamp_akhir = %s WHERE id_kunjungan = %s",
                [
                    request.POST['nama_hewan'],
                    request.POST['no_identitas_klien'],
                    no_front_desk[0],
                    request.POST['no_perawat_hewan'],
                    request.POST['no_dokter_hewan'],
                    request.POST['tipe_kunjungan'],
                    request.POST['timestamp_awal'],
                    request.POST['timestamp_akhir'],
                    id_kunjungan
                ]
            )
            messages.success(request, 'Kunjungan berhasil diperbarui!')
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def kunjungan_delete(request, id_kunjungan):
    if request.method == 'POST':
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM KUNJUNGAN WHERE id_kunjungan = %s", [id_kunjungan])
            messages.success(request, 'Kunjungan berhasil dihapus!')
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def kunjungan_data(request, id_kunjungan):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan, tipe_kunjungan, timestamp_awal, timestamp_akhir FROM KUNJUNGAN WHERE id_kunjungan = %s", [id_kunjungan])
        result = cursor.fetchone()
        if result:
            return JsonResponse({
                'id_kunjungan': result[0],
                'nama_hewan': result[1],
                'no_identitas_klien': result[2],
                'no_front_desk': result[3],
                'no_perawat_hewan': result[4],
                'no_dokter_hewan': result[5],
                'tipe_kunjungan': result[6],
                'timestamp_awal': result[7],
                'timestamp_akhir': result[8]
            })
        return JsonResponse({'status': 'error'}, status=404)
    
@login_required
def rekam_medis_check(request, id_kunjungan):
    print(f"Checking rekam medis for id_kunjungan: {id_kunjungan}")
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT suhu, berat_badan, catatan FROM KUNJUNGAN WHERE id_kunjungan = %s",
                [str(id_kunjungan)]
            )
            result = cursor.fetchone()
            print(f"Query result: {result}")
            if result:
                return JsonResponse({
                    'exists': True,
                    'suhu': result[0],
                    'berat_badan': result[1],
                    'catatan': result[2] or ''
                }, status=200)
            return JsonResponse({'exists': False}, status=200)
    except Exception as e:
        print(f"Error in rekam_medis_check: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def rekam_medis_create(request, id_kunjungan):
    if request.method == 'POST':
        if request.user.groups.filter(name='DokterHewan').exists():
            try:
                with connection.cursor() as cursor:
                    # Cek apakah rekam medis sudah ada
                    cursor.execute(
                        "SELECT suhu, berat_badan FROM KUNJUNGAN WHERE id_kunjungan = %s",
                        (id_kunjungan)
                    )
                    result = cursor.fetchone()
                    if not result:
                        return JsonResponse({'status': 'error', 'message': 'Kunjungan tidak ditemukan!'}, status=404)
                    if result[0] is not None and result[1] is not None:  # Jika suhu dan berat_badan sudah ada
                        return JsonResponse({'status': 'error', 'message': 'Rekam medis untuk kunjungan ini sudah ada!'}, status=400)

                    # Ambil data dari form
                    try:
                        suhu = float(request.POST.get('suhu'))
                        berat_badan = float(request.POST.get('berat_badan'))
                        if suhu <= 0 or berat_badan <= 0:
                            return JsonResponse({'status': 'error', 'message': 'Suhu dan berat badan harus lebih dari 0!'}, status=400)
                    except (ValueError, TypeError):
                        return JsonResponse({'status': 'error', 'message': 'Suhu dan berat badan harus berupa angka!'}, status=400)
                    catatan = request.POST.get('catatan', '')

                    # Validasi data
                    if not all([suhu, berat_badan]):
                        return JsonResponse({'status': 'error', 'message': 'Suhu dan berat badan wajib diisi!'}, status=400)

                    # Simpan ke tabel REKAM_MEDIS
                    cursor.execute(
                        "UPDATE KUNJUNGAN SET suhu = %s, berat_badan = %s, catatan = %s WHERE id_kunjungan = %s",
                        [suhu, berat_badan, catatan, id_kunjungan]
                    )
                    return JsonResponse({'status': 'success', 'message': 'Rekam medis berhasil dibuat!'}, status=200)
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        else:
            return JsonResponse({'status': 'error', 'message': 'Hanya dokter yang dapat membuat rekam medis!'}, status=403)
    return JsonResponse({'status': 'error', 'message': 'Metode tidak diizinkan!'}, status=405)

@login_required
def rekam_medis_update(request, id_kunjungan):
    if request.method == 'POST':
        if request.user.groups.filter(name='DokterHewan').exists():
            try:
                with connection.cursor() as cursor:
                    # Cek apakah rekam medis ada
                    cursor.execute(
                        "SELECT 1 FROM KUNJUNGAN WHERE id_kunjungan = %s",
                        [id_kunjungan]
                    )
                    if not cursor.fetchone():
                        return JsonResponse({'status': 'error', 'message': 'Rekam medis tidak ditemukan!'}, status=400)

                    # Ambil data dari form
                    suhu = request.POST.get('suhu')
                    berat_badan = request.POST.get('berat_badan')
                    catatan = request.POST.get('catatan', '')

                    # Validasi data
                    if not all([suhu, berat_badan]):
                        return JsonResponse({'status': 'error', 'message': 'Suhu dan berat badan wajib diisi!'}, status=400)

                    # Update data di tabel REKAM_MEDIS
                    cursor.execute(
                        "UPDATE KUNJUNGAN SET suhu = %s, berat_badan = %s, catatan = %s WHERE id_kunjungan = %s",
                        [suhu, berat_badan, catatan, id_kunjungan]
                    )
                    return JsonResponse({'status': 'success', 'message': 'Rekam medis berhasil diperbarui!'}, status=200)
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        else:
            return JsonResponse({'status': 'error', 'message': 'Hanya dokter yang dapat memperbarui rekam medis!'}, status=403)
    return JsonResponse({'status': 'error', 'message': 'Metode tidak diizinkan!'}, status=405)

# AJAX untuk dropdown dinamis Nama Hewan
def get_hewan_by_klien(request):
    no_identitas_klien = request.GET.get('no_identitas_klien')
    hewan = []
    with connection.cursor() as cursor:
        cursor.execute("SELECT nama FROM HEWAN WHERE no_identitas_klien = %s", [no_identitas_klien])
        hewan = [{'nama': row[0]} for row in cursor.fetchall()]
    return JsonResponse({'hewan': hewan})