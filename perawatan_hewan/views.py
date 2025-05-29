from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import connection

# Helper untuk cek role
def is_dokter_hewan(user):
    return user.groups.filter(name='DokterHewan').exists()

def is_klien(user):
    return user.groups.filter(name='Klien').exists()

@login_required
def perawatan_view(request):
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

    perawatans = []
    kunjungans = []

    try:
        with connection.cursor() as cursor:
            # Ambil data perawatan dari KUNJUNGAN_KEPERAWATAN dengan join ke KUNJUNGAN dan PEGAWAI
            cursor.execute(
                """
                SELECT 
                    kp.id_kunjungan,
                    kp.no_identitas_klien,
                    kp.nama_hewan,
                    p1.email_user AS perawat_email,
                    p2.email_user AS dokter_email,
                    p3.email_user AS front_desk_email,
                    kp.kode_perawatan,
                    k.catatan
                FROM KUNJUNGAN_KEPERAWATAN kp
                JOIN KUNJUNGAN k ON kp.id_kunjungan = k.id_kunjungan
                    AND kp.nama_hewan = k.nama_hewan
                    AND kp.no_identitas_klien = k.no_identitas_klien
                    AND kp.no_front_desk = k.no_front_desk
                    AND kp.no_perawat_hewan = k.no_perawat_hewan
                    AND kp.no_dokter_hewan = k.no_dokter_hewan
                LEFT JOIN PEGAWAI p1 ON kp.no_perawat_hewan = p1.no_pegawai
                LEFT JOIN PEGAWAI p2 ON kp.no_dokter_hewan = p2.no_pegawai
                LEFT JOIN PEGAWAI p3 ON kp.no_front_desk = p3.no_pegawai
                WHERE kp.kode_perawatan IS NOT NULL
                """
            )
            rows = cursor.fetchall()

            perawatans = [
                {
                    'id_kunjungan': row[0],
                    'no_identitas_klien': row[1],
                    'nama_hewan': row[2],
                    'perawat_email': row[3].capitalize() if row[3] else 'N/A',
                    'dokter_email': f"dr. {row[4].capitalize()}" if row[4] else 'N/A',
                    'front_desk_email': row[5].capitalize() if row[5] else 'N/A',
                    'tipe_kunjungan': row[6] if row[6] else 'N/A',  # Kode perawatan sebagai tipe kunjungan sementara
                    'catatan': row[7] if row[7] else 'N/A'
                } for row in rows
            ]

            # Filter untuk Klien
            if is_klien(request.user):
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT no_identitas FROM KLIEN WHERE email = %s",
                        [request.user.email]
                    )
                    klien_id = cursor.fetchone()
                    if klien_id:
                        perawatans = [p for p in perawatans if p['no_identitas_klien'] == klien_id[0]]

            # Ambil data kunjungan yang belum memiliki perawatan (kode_perawatan IS NULL)
            cursor.execute(
                """
                SELECT 
                    k.id_kunjungan,
                    k.nama_hewan,
                    k.no_identitas_klien,
                    k.no_front_desk,
                    k.no_dokter_hewan,
                    k.no_perawat_hewan,
                    k.tipe_kunjungan
                FROM KUNJUNGAN k
                LEFT JOIN KUNJUNGAN_KEPERAWATAN kp ON k.id_kunjungan = kp.id_kunjungan
                    AND k.nama_hewan = kp.nama_hewan
                    AND k.no_identitas_klien = kp.no_identitas_klien
                    AND k.no_front_desk = kp.no_front_desk
                    AND k.no_perawat_hewan = kp.no_perawat_hewan
                    AND k.no_dokter_hewan = kp.no_dokter_hewan
                WHERE kp.id_kunjungan IS NULL
                """
            )
            kunjungans = [
                {
                    'id_kunjungan': row[0],
                    'nama_hewan': row[1],
                    'no_identitas_klien': row[2],
                    'no_front_desk': row[3],
                    'no_dokter_hewan': row[4],
                    'no_perawat_hewan': row[5],
                    'tipe_kunjungan': row[6]
                } for row in cursor.fetchall()
            ]

    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        perawatans = []
        kunjungans = []

    return render(request, 'perawatan_hewan/perawatan_hewan.html', {
        'perawatans': perawatans,
        'kunjungans': kunjungans,
    })

@login_required
def perawatan_create(request):
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

    try:
        with connection.cursor() as cursor:
            id_kunjungan = request.POST.get('id_kunjungan')
            catatan = request.POST.get('catatan', '')
            jenis_perawatan = request.POST.get('jenis_perawatan', 'N/A')

            if not id_kunjungan:
                return JsonResponse({'status': 'error', 'message': 'Kunjungan wajib diisi!'}, status=400)

            # Cek apakah kunjungan ada di tabel KUNJUNGAN
            cursor.execute(
                "SELECT nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan FROM KUNJUNGAN WHERE id_kunjungan = %s",
                [id_kunjungan]
            )
            kunjungan_data = cursor.fetchone()
            if not kunjungan_data:
                return JsonResponse({'status': 'error', 'message': 'Kunjungan tidak ditemukan!'}, status=404)

            # Ambil data kunjungan
            nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan = kunjungan_data

            # Format catatan
            if jenis_perawatan != 'N/A' and catatan:
                catatan = f"Jenis: {jenis_perawatan}; Catatan: {catatan}"
            elif jenis_perawatan != 'N/A':
                catatan = f"Jenis: {jenis_perawatan}; Catatan: -"
            else:
                catatan = f"Jenis: N/A; Catatan: {catatan or '-'}"

            # Update catatan di KUNJUNGAN (langsung update tanpa pengecekan catatan sudah ada)
            cursor.execute(
                """
                UPDATE KUNJUNGAN 
                SET catatan = %s 
                WHERE id_kunjungan = %s 
                AND nama_hewan = %s 
                AND no_identitas_klien = %s 
                AND no_front_desk = %s 
                AND no_perawat_hewan = %s 
                AND no_dokter_hewan = %s
                """,
                [catatan, id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan]
            )

            # Cek apakah sudah ada entri di KUNJUNGAN_KEPERAWATAN
            cursor.execute(
                "SELECT 1 FROM KUNJUNGAN_KEPERAWATAN WHERE id_kunjungan = %s",
                [id_kunjungan]
            )
            exists = cursor.fetchone() is not None

            # Siapkan kode_perawatan
            kode_perawatan = jenis_perawatan.split(' - ')[0] if jenis_perawatan != 'N/A' else None

            if exists:
                # Update KUNJUNGAN_KEPERAWATAN jika sudah ada
                cursor.execute(
                    """
                    UPDATE KUNJUNGAN_KEPERAWATAN 
                    SET kode_perawatan = %s 
                    WHERE id_kunjungan = %s
                        AND nama_hewan = %s 
                        AND no_identitas_klien = %s 
                        AND no_front_desk = %s 
                        AND no_perawat_hewan = %s 
                        AND no_dokter_hewan = %s
                    """,
                    [kode_perawatan, id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan]
                )
                message = 'Perawatan berhasil diperbarui!'
            else:
                # Insert ke KUNJUNGAN_KEPERAWATAN jika belum ada
                cursor.execute(
                    """
                    INSERT INTO KUNJUNGAN_KEPERAWATAN (id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan, kode_perawatan)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    [id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan, kode_perawatan]
                )
                message = 'Perawatan berhasil dibuat!'

            return JsonResponse({'status': 'success', 'message': message}, status=200)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def perawatan_update(request, id_kunjungan):
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

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM KUNJUNGAN WHERE id_kunjungan = %s AND catatan IS NOT NULL",
                [str(id_kunjungan)]
            )
            if not cursor.fetchone():
                return JsonResponse({'status': 'error', 'message': 'Catatan tidak ditemukan!'}, status=404)

            catatan = request.POST.get('catatan', '')
            jenis_perawatan = request.POST.get('jenis_perawatan', 'N/A')

            if jenis_perawatan != 'N/A' and catatan:
                catatan = f"Jenis: {jenis_perawatan}; Catatan: {catatan}"
            elif jenis_perawatan != 'N/A':
                catatan = f"Jenis: {jenis_perawatan}; Catatan: -"
            else:
                catatan = f"Jenis: N/A; Catatan: {catatan or '-'}"

            cursor.execute(
                "UPDATE KUNJUNGAN SET catatan = %s WHERE id_kunjungan = %s",
                [catatan, str(id_kunjungan)]
            )

            return JsonResponse({'status': 'success', 'message': 'Catatan berhasil diperbarui!'}, status=200)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def perawatan_delete(request, id_kunjungan):
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

    try:
        with connection.cursor() as cursor:
            # Cek apakah entri ada di KUNJUNGAN_KEPERAWATAN
            cursor.execute(
                "SELECT 1 FROM KUNJUNGAN_KEPERAWATAN WHERE id_kunjungan = %s",
                [str(id_kunjungan)]
            )
            if not cursor.fetchone():
                return JsonResponse({'status': 'error', 'message': 'Perawatan tidak ditemukan di KUNJUNGAN_KEPERAWATAN!'}, status=404)

            # Hapus dari KUNJUNGAN_KEPERAWATAN
            cursor.execute(
                "DELETE FROM KUNJUNGAN_KEPERAWATAN WHERE id_kunjungan = %s",
                [str(id_kunjungan)]
            )

            # Set catatan di KUNJUNGAN menjadi NULL
            cursor.execute(
                """
                UPDATE KUNJUNGAN 
                SET catatan = NULL 
                WHERE id_kunjungan = %s
                """,
                [str(id_kunjungan)]
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Perawatan berhasil dihapus!',
                'id_kunjungan': str(id_kunjungan)
            }, status=200)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def perawatan_data(request, id_kunjungan):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT catatan
                FROM KUNJUNGAN
                WHERE id_kunjungan = %s
                """,
                [str(id_kunjungan)]
            )
            result = cursor.fetchone()
            if result and result[0]:
                return JsonResponse({
                    'catatan': result[0]
                }, status=200)
            return JsonResponse({'status': 'error', 'message': 'Catatan tidak ditemukan!'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)