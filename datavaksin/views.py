# datavaksin/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse # Jika ingin menggunakan AJAX nanti
from django.urls import reverse
from django.contrib import messages # Untuk feedback ke user
from manajemen_vaksin.models import Vaksin
from .forms import VaksinForm, VaksinInfoUpdateForm, VaksinStockUpdateForm
from django.db import IntegrityError # Untuk menangani error duplikasi PK


def vaccine_data_list_view(request):
    vaksin_list = Vaksin.objects.all().order_by('kode')
    form_create = VaksinForm() # Untuk modal create
    # Kita tidak perlu form update di sini karena akan di-handle via AJAX atau load data saat modal dibuka
    context = {
        'vaksin_list': vaksin_list,
        'form_create': form_create, # Kirim form ke template untuk modal create
    }
    return render(request, 'datavaksin/datavaksin.html', context)

def vaccine_data_create_view(request):
    if request.method == 'POST':
        form = VaksinForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f"Vaksin '{form.cleaned_data['nama']}' berhasil ditambahkan.")
                return redirect('datavaksin:vaccine_data_list') # Redirect ke halaman list
            except IntegrityError: # Menangkap error jika kode vaksin sudah ada (PK violation)
                messages.error(request, f"Gagal menambahkan vaksin. Kode vaksin '{form.cleaned_data['kode']}' sudah ada.")
                # Kembali ke halaman list, modal create bisa dibuka lagi dengan data error
                # Atau render halaman dengan form error (lebih kompleks untuk modal)
                # Untuk simplicity, kita redirect dan biarkan user coba lagi
                # Lebih baik: return ke list dengan cara membuka modal dan menampilkan error form.
                # Ini memerlukan penanganan di template/JS.
                # Untuk sekarang, redirect saja.
                return redirect('datavaksin:vaccine_data_list')

        else:
            # Jika form tidak valid, kita bisa kirim error kembali.
            # Ini juga lebih kompleks untuk modal. Idealnya, validasi dilakukan via AJAX.
            error_str = "Gagal menambahkan vaksin. Cek kembali data yang diinput: "
            for field, errors in form.errors.items():
                error_str += f"{field}: {', '.join(errors)} "
            messages.error(request, error_str)
            return redirect('datavaksin:vaccine_data_list')
    return redirect('datavaksin:vaccine_data_list') # Jika bukan POST, redirect

def vaccine_data_update_view(request, kode_vaksin):
    vaksin_instance = get_object_or_404(Vaksin, kode=kode_vaksin)
    if request.method == 'POST':
        form = VaksinInfoUpdateForm(request.POST, instance=vaksin_instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Info vaksin '{vaksin_instance.nama}' berhasil diupdate.")
            return redirect('datavaksin:vaccine_data_list')
        else:
            error_str = f"Gagal mengupdate vaksin '{vaksin_instance.nama}'. Cek kembali data: "
            for field, errors in form.errors.items():
                error_str += f"{field}: {', '.join(errors)} "
            messages.error(request, error_str)
            return redirect('datavaksin:vaccine_data_list') # Atau render template dengan error
    else: # Untuk GET request, biasanya untuk pre-fill form (jika tidak via JS)
        # Jika modal diisi via JS, view ini murni untuk POST.
        # Jika tidak, Anda akan merender form dengan instance di sini.
        # Karena JS Anda mengisi modal, kita bisa anggap GET tidak melakukan apa-apa disini
        # atau redirect.
        return redirect('datavaksin:vaccine_data_list')


def vaccine_stock_update_view(request, kode_vaksin):
    vaksin_instance = get_object_or_404(Vaksin, kode=kode_vaksin)
    if request.method == 'POST':
        form = VaksinStockUpdateForm(request.POST, instance=vaksin_instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Stok vaksin '{vaksin_instance.nama}' berhasil diupdate menjadi {form.cleaned_data['stok']}.")
            return redirect('datavaksin:vaccine_data_list')
        else:
            messages.error(request, f"Gagal mengupdate stok vaksin '{vaksin_instance.nama}'. Stok harus angka.")
            return redirect('datavaksin:vaccine_data_list')
    return redirect('datavaksin:vaccine_data_list')


def vaccine_data_delete_view(request, kode_vaksin):
    vaksin_instance = get_object_or_404(Vaksin, kode=kode_vaksin)
    if request.method == 'POST': # Pastikan ini benar-benar konfirmasi delete
        try:
            nama_vaksin = vaksin_instance.nama
            vaksin_instance.delete()
            messages.success(request, f"Vaksin '{nama_vaksin}' berhasil dihapus.")
        except Exception as e: # Tangkap error umum saat delete, misal terkait foreign key constraint
            messages.error(request, f"Gagal menghapus vaksin '{vaksin_instance.nama}'. Mungkin vaksin ini masih digunakan dalam data kunjungan. Error: {e}")
        return redirect('datavaksin:vaccine_data_list')
    # Jika GET, bisa tampilkan halaman konfirmasi, tapi karena modal JS sudah ada, redirect saja
    return redirect('datavaksin:vaccine_data_list')

# Opsional: View untuk mengambil data vaksin via AJAX untuk mengisi modal update
def get_vaccine_details_json(request, kode_vaksin):
    try:
        vaksin = Vaksin.objects.get(kode=kode_vaksin)
        data = {
            'kode': vaksin.kode,
            'nama': vaksin.nama,
            'harga': vaksin.harga,
            'stok': vaksin.stok, # Kirim stok juga jika diperlukan di modal update info
        }
        return JsonResponse(data)
    except Vaksin.DoesNotExist:
        return JsonResponse({'error': 'Vaksin tidak ditemukan'}, status=404)