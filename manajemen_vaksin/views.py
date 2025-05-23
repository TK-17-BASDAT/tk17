# /your_app/views.py
from django.shortcuts import render
from datetime import date
import locale
from .models import Vaksin
from kunjungan.models import Kunjungan

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
    """Helper function to format date object into Indonesian string."""
    if not isinstance(tanggal_obj, date):
        return str(tanggal_obj) # Return as is if not a date object
    # Format: Hari, Tanggal Bulan Tahun (e.g., Rabu, 5 Februari 2025)
    return tanggal_obj.strftime("%A, %d %B %Y").title()


def vaccination_list_view(request):
    kunjungan_dengan_vaksin = Kunjungan.objects.filter(kode_vaksin__isnull=False).select_related(
        'hewan', 'kode_vaksin'
    )
    print(kunjungan_dengan_vaksin.count())
    
    # # List of existing vaccinations
    vaccinations_data = []
    # for kun in kunjungan_dengan_vaksin:
    #     print("kunjungan id" + kun.id_kunjungan)
    #     vaccinations_data.append({
    #         "kunjungan_id": str(kun.id_kunjungan), # UUID jadi string jika perlu
    #         "tanggal_kunjungan": kun.timestamp_awal.date(), # Ambil bagian tanggal saja
    #         "tanggal_kunjungan_formatted": format_tanggal_indonesia(kun.timestamp_awal.date()),
    #         "vaksin_id": kun.kode_vaksin.kode,
    #         "vaksin_nama": kun.kode_vaksin.nama,
    #         # Tambahkan info hewan jika perlu di list utama
    #         "nama_hewan": kun.hewan.nama,
    #         "pemilik_hewan": kun.hewan.no_identitas_klien.email.email # contoh akses relasi
    #     })


    # Format the date for display
    # for vac in vaccinations_data:
    #     vac['tanggal_kunjungan_formatted'] = format_tanggal_indonesia(vac['tanggal_kunjungan'])

    # # List of available Kunjungan (Visits) - could be fetched from another model
    kunjungan_options = [
        {"id": "KJN001", "display_text": "KJN001 - (Info Kunjungan 1)"}, # Add more relevant info if needed
        {"id": "KJN002", "display_text": "KJN002 - (Info Kunjungan 2)"},
        {"id": "KJN003", "display_text": "KJN003 - (Info Kunjungan 3)"},
        {"id": "KJN004", "display_text": "KJN004 - (Info Kunjungan 4)"}, # Example of more visits
    ]


    all_vaksin = Vaksin.objects.all()
    print("Jumlah vaksin:", all_vaksin.count())

    # List of available Vaksin (Vaccines) with stock - could be fetched from another model
    vaksin_options = []
    for v in all_vaksin:
        print ("Vaksin: " + v.kode + v.nama)
        vaksin_options.append({
            "id": v.kode, # PK Vaksin
            "nama": v.nama,
            "stok": v.stok
        })

    context = {
        'vaccinations': vaccinations_data,
        'kunjungan_options': kunjungan_options,
        'vaksin_options': vaksin_options,
    }
    return render(request, 'manajemen_vaksin/vaksin.html', context)


