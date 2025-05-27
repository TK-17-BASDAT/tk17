# /your_app/views.py (misalnya, manajemen_vaksin/views.py)

from django.shortcuts import render
from django.db import connection # Untuk eksekusi query SQL langsung
from datetime import date, datetime
import locale

# Optional: Set locale for formatting dates in Indonesian
try:
    locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8') # Linux/macOS
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'Indonesian_Indonesia.1252') # Windows
    except locale.Error:
        print("Indonesian locale not found, using default.")
        pass # Use default locale if Indonesian isn't available


def format_tanggal_indonesia(tanggal_obj):
    """Helper function to format date object or datetime object into Indonesian string."""
    if isinstance(tanggal_obj, datetime):
        tanggal_obj = tanggal_obj.date() # Ambil bagian tanggal jika datetime
    elif not isinstance(tanggal_obj, date):
        return str(tanggal_obj) # Return as is if not a date object
    
    # Format: Hari, Tanggal Bulan Tahun (e.g., Rabu, 5 Februari 2025)
    return tanggal_obj.strftime("%A, %d %B %Y").title()

def dictfetchall(cursor):
    """Return all rows from a cursor as a list of dictionaries."""
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def vaccination_list_view(request):
    vaccinations_data = []
    kunjungan_options = [] # Akan diisi dari query jika diperlukan
    vaksin_options = []

    try:
        with connection.cursor() as cursor:
            # 1. Ambil data Kunjungan yang memiliki Vaksin (List of existing vaccinations)
            query_kunjungan_vaksin = """
                SELECT
                    k.id_kunjungan,
                    k.timestamp_awal,
                    k.kode_vaksin,
                    v.nama AS nama_vaksin,
                    h.nama AS nama_hewan,
                    u.email AS email_pemilik,
                    COALESCE(i.nama_depan || ' ' || i.nama_tengah || ' ' || i.nama_belakang, pr.nama_perusahaan) AS nama_pemilik
                FROM
                    PETCLINIC.KUNJUNGAN k
                JOIN
                    PETCLINIC.VAKSIN v ON k.kode_vaksin = v.kode
                JOIN
                    PETCLINIC.HEWAN h ON k.nama_hewan = h.nama AND k.no_identitas_klien = h.no_identitas_klien
                JOIN
                    PETCLINIC.KLIEN kl ON h.no_identitas_klien = kl.no_identitas
                JOIN
                    PETCLINIC."user" u ON kl.email = u.email
                LEFT JOIN
                    PETCLINIC.INDIVIDU i ON kl.no_identitas = i.no_identitas_klien
                LEFT JOIN
                    PETCLINIC.PERUSAHAAN pr ON kl.no_identitas = pr.no_identitas_klien
                WHERE
                    k.kode_vaksin IS NOT NULL
                ORDER BY
                    k.timestamp_awal DESC;
            """
            cursor.execute(query_kunjungan_vaksin)
            kunjungan_vaksin_rows = dictfetchall(cursor) # Menggunakan dictfetchall agar mudah diakses

            for row in kunjungan_vaksin_rows:
                # Bersihkan nama pemilik dari spasi ganda jika nama tengah kosong
                nama_pemilik_cleaned = row['nama_pemilik'].replace('  ', ' ').strip() if row['nama_pemilik'] else 'N/A'

                vaccinations_data.append({
                    "kunjungan_id": str(row['id_kunjungan']), # UUID jadi string
                    "timestamp_awal": row['timestamp_awal'], # Ini adalah objek datetime
                    "tanggal_kunjungan_formatted": format_tanggal_indonesia(row['timestamp_awal']),
                    "vaksin_id": row['kode_vaksin'],
                    "vaksin_nama": row['nama_vaksin'],
                    "nama_hewan": row['nama_hewan'],
                    "email_pemilik": row['email_pemilik'],
                    "nama_pemilik": nama_pemilik_cleaned
                })
            
            print(f"Jumlah kunjungan dengan vaksin ditemukan: {len(vaccinations_data)}")

            # 2. Ambil semua Kunjungan yang tersedia (untuk dropdown, jika diperlukan)
            # Ini contoh, sesuaikan field yang ingin ditampilkan di dropdown
            # Jika kunjungan sangat banyak, pertimbangkan pagination atau search
            query_all_kunjungan = """
                SELECT
                    k.id_kunjungan,
                    h.nama as nama_hewan,
                    k.timestamp_awal
                FROM
                    PETCLINIC.KUNJUNGAN k
                JOIN
                    PETCLINIC.HEWAN h ON k.nama_hewan = h.nama AND k.no_identitas_klien = h.no_identitas_klien
                ORDER BY
                    k.timestamp_awal DESC
                LIMIT 100; -- Batasi jumlah untuk contoh
            """
            cursor.execute(query_all_kunjungan)
            all_kunjungan_rows = dictfetchall(cursor)

            for row in all_kunjungan_rows:
                kunjungan_options.append({
                    "id": str(row['id_kunjungan']),
                    "display_text": f"{str(row['id_kunjungan'])} - {row['nama_hewan']} ({format_tanggal_indonesia(row['timestamp_awal'])})"
                })
            
            print(f"Jumlah opsi kunjungan: {len(kunjungan_options)}")

            # 3. Ambil semua Vaksin yang tersedia (List of available Vaksin)
            query_all_vaksin = """
                SELECT
                    kode,
                    nama,
                    stok
                FROM
                    PETCLINIC.VAKSIN
                ORDER BY
                    nama;
            """
            cursor.execute(query_all_vaksin)
            all_vaksin_rows = dictfetchall(cursor)

            for row in all_vaksin_rows:
                vaksin_options.append({
                    "id": row['kode'],
                    "nama": row['nama'],
                    "stok": row['stok']
                })
            
            print(f"Jumlah opsi vaksin: {len(vaksin_options)}")

    except Exception as e:
        print(f"Database error: {e}")
        # Handle error, mungkin tampilkan pesan di template
        # Atau set data ke list kosong jika ada error
        vaccinations_data = []
        kunjungan_options = []
        vaksin_options = []
        # Anda bisa menambahkan messages.error(request, "Gagal mengambil data dari database.")

    context = {
        'vaccinations': vaccinations_data,
        'kunjungan_options': kunjungan_options,
        'vaksin_options': vaksin_options,
    }
    return render(request, 'manajemen_vaksin/vaksin.html', context)