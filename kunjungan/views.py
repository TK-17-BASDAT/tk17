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
    
    -- Perbaikan di sini:
    -- TENAGA_MEDIS.no_tenaga_medis adalah PK dan FK ke PEGAWAI.no_pegawai
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