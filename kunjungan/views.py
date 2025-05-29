# tk17/kunjungan/views.py
from django.shortcuts import render, redirect
from django.db import connection
from django.http import Http404
import uuid # Jika kamu menggunakan tipe UUID di Python, meskipun di query bisa string

# Helper function untuk mengubah hasil query cursor menjadi list of dictionaries
def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

# Helper function untuk mengubah satu hasil query cursor menjadi dictionary
def dictfetchone(cursor):
    "Return one row from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    if row:
        return dict(zip(columns, row))
    return None

def list_kunjungan_view(request):
    query = """
    SELECT
        k.id_kunjungan,
        k.nama_hewan,
        k.no_identitas_klien,
        k.no_front_desk,
        k.no_perawat_hewan,
        k.no_dokter_hewan,
        k.tipe_kunjungan,
        k.timestamp_awal,
        k.timestamp_akhir,
        k.suhu,
        h.url_foto AS foto_hewan,
        jh.nama_jenis AS jenis_hewan,
        COALESCE(i.nama_depan || ' ' || i.nama_belakang, p.nama_perusahaan) AS nama_klien,
        udh.email AS email_dokter
    FROM KUNJUNGAN k
    JOIN HEWAN h ON k.nama_hewan = h.nama AND k.no_identitas_klien = h.no_identitas_klien
    JOIN JENIS_HEWAN jh ON h.id_jenis = jh.id
    JOIN KLIEN kl ON k.no_identitas_klien = kl.no_identitas
    LEFT JOIN INDIVIDU i ON kl.no_identitas = i.no_identitas_klien
    LEFT JOIN PERUSAHAAN p ON kl.no_identitas = p.no_identitas_klien
    
    JOIN DOKTER_HEWAN dh ON k.no_dokter_hewan = dh.no_dokter_hewan 
    JOIN TENAGA_MEDIS tm_dh ON dh.no_dokter_hewan = tm_dh.no_tenaga_medis
    JOIN PEGAWAI peg_dh ON tm_dh.no_tenaga_medis = peg_dh.no_pegawai 
    JOIN "user" udh ON peg_dh.email_user = udh.email
    
    ORDER BY k.timestamp_awal DESC;
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        kunjungan_list = dictfetchall(cursor)

    return render(request, 'kunjungan/kunjungan.html', {'kunjungan_list': kunjungan_list})

def rekam_medis_view(request, id_kunjungan, nama_hewan, no_identitas_klien,
                       no_front_desk, no_perawat_hewan, no_dokter_hewan):
    # Kunci komposit untuk identifikasi kunjungan unik
    kunjungan_pk_tuple = (
        str(id_kunjungan), # Pastikan string untuk parameter query SQL
        str(nama_hewan),
        str(no_identitas_klien),
        str(no_front_desk),
        str(no_perawat_hewan),
        str(no_dokter_hewan)
    )

    query_select_kunjungan = """
    SELECT
        k.id_kunjungan, k.nama_hewan, k.no_identitas_klien,
        k.no_front_desk, k.no_perawat_hewan, k.no_dokter_hewan,
        k.suhu, k.berat_badan, k.catatan,
        h_display.nama AS nama_hewan_display, -- Kolom HEWAN.nama untuk display
        COALESCE(i.nama_depan || ' ' || i.nama_belakang, p.nama_perusahaan) AS nama_klien_display
    FROM KUNJUNGAN k
    JOIN HEWAN h_display ON k.nama_hewan = h_display.nama AND k.no_identitas_klien = h_display.no_identitas_klien
    JOIN KLIEN kl ON k.no_identitas_klien = kl.no_identitas
    LEFT JOIN INDIVIDU i ON kl.no_identitas = i.no_identitas_klien
    LEFT JOIN PERUSAHAAN p ON kl.no_identitas = p.no_identitas_klien
    WHERE k.id_kunjungan = %s AND k.nama_hewan = %s AND k.no_identitas_klien = %s
      AND k.no_front_desk = %s AND k.no_perawat_hewan = %s AND k.no_dokter_hewan = %s;
    """
    
    kunjungan_data = None
    with connection.cursor() as cursor:
        cursor.execute(query_select_kunjungan, kunjungan_pk_tuple)
        kunjungan_data = dictfetchone(cursor)

    if not kunjungan_data:
        raise Http404("Data Kunjungan tidak ditemukan.")

    # Cek apakah salah satu field rekam medis sudah ada isinya
    rekam_medis_exists = kunjungan_data.get('suhu') is not None or \
                         kunjungan_data.get('berat_badan') is not None or \
                         (kunjungan_data.get('catatan') is not None and kunjungan_data.get('catatan').strip() != '')


    if request.method == 'POST':
        suhu_str = request.POST.get('suhu')
        berat_badan_str = request.POST.get('berat_badan')
        catatan = request.POST.get('catatan', '') # Default ke string kosong jika tidak ada

        suhu_val = None
        berat_badan_val = None

        try:
            if suhu_str and suhu_str.strip():
                suhu_val = int(suhu_str) # Atau float jika perlu desimal
            if berat_badan_str and berat_badan_str.strip():
                berat_badan_val = float(berat_badan_str) # NUMERIC(5,2) bisa float
        except ValueError:
            # Jika konversi gagal, biarkan None dan mungkin tambahkan pesan error ke context
            # Untuk sekarang, kita lanjutkan dengan nilai None jika error
            pass 
            # Anda bisa menambahkan pesan error ke form di sini jika diperlukan
            # context = {..., 'error_message': 'Input suhu atau berat badan tidak valid.'}
            # return render(request, 'kunjungan/rekam_medis_form.html', context)


        query_update_rekam_medis = """
        UPDATE KUNJUNGAN
        SET suhu = %s, berat_badan = %s, catatan = %s
        WHERE id_kunjungan = %s AND nama_hewan = %s AND no_identitas_klien = %s
          AND no_front_desk = %s AND no_perawat_hewan = %s AND no_dokter_hewan = %s;
        """
        
        update_params = (
            suhu_val, berat_badan_val, catatan,
            *kunjungan_pk_tuple # unpack tuple kunci komposit
        )

        with connection.cursor() as cursor:
            cursor.execute(query_update_rekam_medis, update_params)
        
        # Redirect kembali ke halaman yang sama untuk melihat perubahan
        return redirect('kunjungan:rekam_medis_detail', # Gunakan nama URL yang benar
                        id_kunjungan=id_kunjungan, nama_hewan=nama_hewan, 
                        no_identitas_klien=no_identitas_klien, no_front_desk=no_front_desk, 
                        no_perawat_hewan=no_perawat_hewan, no_dokter_hewan=no_dokter_hewan)

    context = {
        'kunjungan_data': kunjungan_data, # Mengganti 'kunjungan' menjadi 'kunjungan_data'
        'rekam_medis_exists': rekam_medis_exists,
        'is_update_form': rekam_medis_exists, # Untuk logika di template (misal teks tombol)
        # PKs untuk form action atau link
        'id_kunjungan_url': id_kunjungan, # Mengganti nama agar tidak bentrok dgn dict key
        'nama_hewan_url': nama_hewan,
        'no_identitas_klien_url': no_identitas_klien,
        'no_front_desk_url': no_front_desk,
        'no_perawat_hewan_url': no_perawat_hewan,
        'no_dokter_hewan_url': no_dokter_hewan,
    }
    return render(request, 'kunjungan/rekam_medis_form.html', context)

def tambah_kunjungan_view(request):
    """View untuk menampilkan form tambah kunjungan baru"""
    
    # Query untuk mendapatkan data dropdown
    query_klien = """
    SELECT 
        kl.no_identitas,
        COALESCE(i.nama_depan || ' ' || i.nama_belakang, p.nama_perusahaan) AS nama_klien
    FROM KLIEN kl
    LEFT JOIN INDIVIDU i ON kl.no_identitas = i.no_identitas_klien
    LEFT JOIN PERUSAHAAN p ON kl.no_identitas = p.no_identitas_klien
    ORDER BY nama_klien;
    """
    
    # PERBAIKAN: Join melalui KLIEN table untuk mendapatkan email
    query_dokter = """
    SELECT DISTINCT ON (u.email)
        dh.no_dokter_hewan,
        u.email as email_dokter,
        u.nomor_telepon as telepon_dokter,
        CONCAT(u.alamat, ' (', u.nomor_telepon, ')') as info_kontak
    FROM DOKTER_HEWAN dh
    JOIN TENAGA_MEDIS tm ON dh.no_dokter_hewan = tm.no_tenaga_medis
    JOIN PEGAWAI p ON tm.no_tenaga_medis = p.no_pegawai
    JOIN "user" u ON p.email_user = u.email
    ORDER BY u.email;
    """
    
    # PERBAIKAN: Join melalui KLIEN table untuk mendapatkan email
    query_perawat = """
    SELECT DISTINCT ON (u.email)
        ph.no_perawat_hewan,
        u.email as email_perawat,
        u.nomor_telepon as telepon_perawat,
        CONCAT(u.alamat, ' (', u.nomor_telepon, ')') as info_kontak
    FROM PERAWAT_HEWAN ph
    JOIN TENAGA_MEDIS tm ON ph.no_perawat_hewan = tm.no_tenaga_medis
    JOIN PEGAWAI p ON tm.no_tenaga_medis = p.no_pegawai
    JOIN "user" u ON p.email_user = u.email
    ORDER BY u.email;
    """
    
    # PERBAIKAN: Join melalui KLIEN table untuk mendapatkan email
    query_front_desk = """
    SELECT 
        fd.no_front_desk,
        u_fd.email as email_front_desk,
        COALESCE(i_fd.nama_depan || ' ' || i_fd.nama_belakang, p_fd.nama_perusahaan) AS nama_front_desk
    FROM FRONT_DESK fd
    JOIN PEGAWAI peg_fd ON fd.no_front_desk = peg_fd.no_pegawai 
    JOIN "user" u_fd ON peg_fd.email_user = u_fd.email
    JOIN KLIEN kl_fd ON u_fd.email = kl_fd.email
    LEFT JOIN INDIVIDU i_fd ON kl_fd.no_identitas = i_fd.no_identitas_klien
    LEFT JOIN PERUSAHAAN p_fd ON kl_fd.no_identitas = p_fd.no_identitas_klien
    ORDER BY nama_front_desk;
    """

    with connection.cursor() as cursor:
        cursor.execute(query_klien)
        klien_list = dictfetchall(cursor)
        
        cursor.execute(query_dokter)
        dokter_list = dictfetchall(cursor)
        
        cursor.execute(query_perawat)
        perawat_list = dictfetchall(cursor)
        
        cursor.execute(query_front_desk)
        front_desk_list = dictfetchall(cursor)

    # Untuk AJAX request mendapatkan hewan berdasarkan klien
    if request.method == 'GET' and request.GET.get('klien_id'):
        klien_id = request.GET.get('klien_id')
        query_hewan = """
        SELECT nama, id_jenis
        FROM HEWAN h
        WHERE h.no_identitas_klien = %s
        ORDER BY nama;
        """
        with connection.cursor() as cursor:
            cursor.execute(query_hewan, [klien_id])
            hewan_list = dictfetchall(cursor)
        
        from django.http import JsonResponse
        return JsonResponse({'hewan_list': hewan_list})

    if request.method == 'POST':
        # Ambil data dari form
        klien_id = request.POST.get('klien')
        nama_hewan = request.POST.get('nama_hewan')
        dokter_id = request.POST.get('dokter')
        perawat_id = request.POST.get('perawat')
        front_desk_id = request.POST.get('front_desk')
        tipe_kunjungan = request.POST.get('tipe_kunjungan')
        waktu_mulai = request.POST.get('waktu_mulai')
        waktu_akhir = request.POST.get('waktu_akhir', None)

        try:
            # Generate UUID untuk id_kunjungan
            import uuid
            id_kunjungan = str(uuid.uuid4())
            
            # Insert kunjungan baru
            query_insert = """
            INSERT INTO KUNJUNGAN (
                id_kunjungan, nama_hewan, no_identitas_klien,
                no_front_desk, no_perawat_hewan, no_dokter_hewan,
                tipe_kunjungan, timestamp_awal, timestamp_akhir
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            
            with connection.cursor() as cursor:
                cursor.execute(query_insert, [
                    id_kunjungan, nama_hewan, klien_id,
                    front_desk_id, perawat_id, dokter_id,
                    tipe_kunjungan, waktu_mulai, waktu_akhir
                ])
            
            from django.contrib import messages
            messages.success(request, f'Kunjungan untuk {nama_hewan} berhasil ditambahkan!')
            return redirect('kunjungan:list_all_kunjungan')
            
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'Gagal menambahkan kunjungan: {str(e)}')

    context = {
        'klien_list': klien_list,
        'dokter_list': dokter_list,
        'perawat_list': perawat_list,
        'front_desk_list': front_desk_list,
    }
    
    return render(request, 'kunjungan/tambah_kunjungan_form.html', context)