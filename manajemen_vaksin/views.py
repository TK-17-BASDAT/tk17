# /your_app/views.py
from django.shortcuts import render
from datetime import date
import locale
from .models import Vaksin

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
    # --- Hardcoded Data (Simulating Database Fetch) ---
    
    # List of existing vaccinations
    vaccinations_data = [
        {
            "id": 1, # Usually a primary key from the database
            "kunjungan_id": "KJN001",
            "tanggal_kunjungan": date(2025, 2, 5),
            "vaksin_id": "VAC001",
            "vaksin_nama": "Feline Panleukopenia",
        },
        {
            "id": 2,
            "kunjungan_id": "KJN002",
            "tanggal_kunjungan": date(2025, 2, 21),
            "vaksin_id": "VAC002",
            "vaksin_nama": "Canine Parvovirus",
        },
        {
            "id": 3,
            "kunjungan_id": "KJN003",
            "tanggal_kunjungan": date(2025, 3, 15),
            "vaksin_id": "VAC003",
            "vaksin_nama": "Canine Adenovirus",
        },
    ]

    # Format the date for display
    for vac in vaccinations_data:
        vac['tanggal_kunjungan_formatted'] = format_tanggal_indonesia(vac['tanggal_kunjungan'])

    # List of available Kunjungan (Visits) - could be fetched from another model
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


