from django.shortcuts import render
from django.db import connection
from django.http import JsonResponse 
from django.contrib import messages 

def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def dictfetchone(cursor):
    columns = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    if row:
        return dict(zip(columns, row))
    return None

def client_list_view(request):
    clients_data = []

    search_query = request.GET.get('search_query', '').strip()
    jenis_klien_filter = request.GET.get('jenis_klien', '').strip()

    base_query = """
        SELECT
            u.email,
            k.no_identitas,
            k.tanggal_registrasi,
            u.alamat,
            u.nomor_telepon,
            i.nama_depan,
            i.nama_tengah,
            i.nama_belakang,
            p.nama_perusahaan,
            CASE
                WHEN i.no_identitas_klien IS NOT NULL THEN 'Individu'
                WHEN p.no_identitas_klien IS NOT NULL THEN 'Perusahaan'
                ELSE 'Tidak Diketahui'
            END AS jenis_klien
        FROM
            PETCLINIC.KLIEN k
        JOIN
            PETCLINIC."user" u ON k.email = u.email
        LEFT JOIN
            PETCLINIC.INDIVIDU i ON k.no_identitas = i.no_identitas_klien
        LEFT JOIN
            PETCLINIC.PERUSAHAAN p ON k.no_identitas = p.no_identitas_klien
    """
    
    conditions = []
    params = []

    if search_query:
        search_term = f"%{search_query}%"
        conditions.append("""
            (u.email ILIKE %s OR
             i.nama_depan ILIKE %s OR
             i.nama_tengah ILIKE %s OR
             i.nama_belakang ILIKE %s OR
             p.nama_perusahaan ILIKE %s OR
             (i.nama_depan || ' ' || COALESCE(i.nama_tengah || ' ', '') || i.nama_belakang) ILIKE %s)
        """)

        for _ in range(6):
            params.append(search_term)
            
    if jenis_klien_filter:
        if jenis_klien_filter == 'Individu':
            conditions.append("i.no_identitas_klien IS NOT NULL")
        elif jenis_klien_filter == 'Perusahaan':
            conditions.append("p.no_identitas_klien IS NOT NULL")

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
    
    base_query += " ORDER BY u.email;"

    try:
        with connection.cursor() as cursor:
            cursor.execute(base_query, params) 
            clients_raw = dictfetchall(cursor)

            for client_row in clients_raw:
                nama_lengkap = "N/A"
                if client_row['jenis_klien'] == 'Individu':
                    nama_lengkap = f"{client_row.get('nama_depan', '')} {client_row.get('nama_tengah', '') or ''} {client_row.get('nama_belakang', '')}".strip().replace('  ', ' ')
                elif client_row['jenis_klien'] == 'Perusahaan':
                    nama_lengkap = client_row.get('nama_perusahaan', 'N/A')
                
                clients_data.append({
                    'no_identitas': str(client_row['no_identitas']),
                    'email': client_row['email'],
                    'nama_display': nama_lengkap,
                    'jenis_klien': client_row['jenis_klien'],
                    'alamat': client_row['alamat'],
                    'nomor_telepon': client_row['nomor_telepon'],
                    'tanggal_registrasi': client_row['tanggal_registrasi'],
                    'raw_data': client_row
                })

    except Exception as e:
        messages.error(request, f"Gagal mengambil data klien: {e}")
        print(f"Error fetching client list with search: {e}")

    context = {
        'client_list': clients_data
    }
    return render(request, 'dataklien/dataklien.html', context)


def get_client_details_json(request, no_identitas_klien):
    client_details = {}
    hewan_list = []
    client_type = None

    try:
        with connection.cursor() as cursor:
            query_client = """
                SELECT
                    k.no_identitas,
                    u.email,
                    u.alamat,
                    u.nomor_telepon,
                    k.tanggal_registrasi,
                    i.nama_depan,
                    i.nama_tengah,
                    i.nama_belakang,
                    p.nama_perusahaan,
                    CASE
                        WHEN i.no_identitas_klien IS NOT NULL THEN 'Individu'
                        WHEN p.no_identitas_klien IS NOT NULL THEN 'Perusahaan'
                        ELSE 'Tidak Diketahui'
                    END AS jenis_klien
                FROM
                    PETCLINIC.KLIEN k
                JOIN
                    PETCLINIC."user" u ON k.email = u.email
                LEFT JOIN
                    PETCLINIC.INDIVIDU i ON k.no_identitas = i.no_identitas_klien
                LEFT JOIN
                    PETCLINIC.PERUSAHAAN p ON k.no_identitas = p.no_identitas_klien
                WHERE
                    k.no_identitas = %s;
            """
            cursor.execute(query_client, [no_identitas_klien])
            client_row = dictfetchone(cursor)

            if not client_row:
                return JsonResponse({'error': 'Klien tidak ditemukan'}, status=404)

            client_type = client_row['jenis_klien']
            client_details = {
                'no_identitas': str(client_row['no_identitas']),
                'email': client_row['email'],
                'alamat': client_row['alamat'],
                'nomor_telepon': client_row['nomor_telepon'],
                'tanggal_registrasi': client_row['tanggal_registrasi'].strftime('%d %B %Y') if client_row['tanggal_registrasi'] else None,
                'jenis_klien': client_type,
            }
            if client_type == 'Individu':
                client_details['nama_lengkap'] = f"{client_row.get('nama_depan', '')} {client_row.get('nama_tengah', '') or ''} {client_row.get('nama_belakang', '')}".strip().replace('  ', ' ')
            elif client_type == 'Perusahaan':
                client_details['nama_perusahaan'] = client_row.get('nama_perusahaan')

            query_hewan = """
                SELECT
                    h.nama,
                    h.tanggal_lahir,
                    jh.nama_jenis
                FROM
                    PETCLINIC.HEWAN h
                JOIN
                    PETCLINIC.JENIS_HEWAN jh ON h.id_jenis = jh.id
                WHERE
                    h.no_identitas_klien = %s
                ORDER BY
                    h.nama;
            """
            cursor.execute(query_hewan, [no_identitas_klien])
            hewan_rows = dictfetchall(cursor)
            for hewan_row in hewan_rows:
                hewan_list.append({
                    'nama': hewan_row['nama'],
                    'nama_jenis': hewan_row['nama_jenis'],
                    'tanggal_lahir': hewan_row['tanggal_lahir'].strftime('%Y-%m-%d') if hewan_row['tanggal_lahir'] else None,
                })
            
            client_details['hewan_peliharaan'] = hewan_list
            
            return JsonResponse(client_details)

    except Exception as e:
        print(f"Error fetching client details JSON for {no_identitas_klien}: {e}")
        return JsonResponse({'error': f'Kesalahan server: {str(e)}'}, status=500)