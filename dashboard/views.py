from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connection, transaction
from django.http import Http404
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required 
from django.utils.decorators import method_decorator
from .forms import CustomPasswordChangeForm, SertifikatFormSet, JadwalPraktikFormSet 
from django.db import connection, transaction, IntegrityError, DatabaseError
# Login URL, sesuaikan jika berbeda
LOGIN_URL = '/auth/login/'

def index(request):
    """
    Dashboard index view.
    Bisa mengarahkan ke halaman spesifik berdasarkan role,
    atau menampilkan dashboard umum jika pengguna sudah login tapi belum ada role spesifik
    atau jika URL ini diakses langsung.
    """
    if not request.user.is_authenticated:
        return redirect(LOGIN_URL)

    user_role = request.session.get('user_role')

    if user_role == 'klien_individu':
        return redirect('dashboard:klien')
    elif user_role == 'klien_perusahaan':
        return redirect('dashboard:kliencompany')
    elif user_role == 'front_desk':
        return redirect('dashboard:frontdesk')
    elif user_role == 'dokter_hewan':
        return redirect('dashboard:dokter')
    elif user_role == 'perawat_hewan':
        return redirect('dashboard:perawat')
    else:
        return render(request, 'dashboard/index.html', {'message': 'Selamat datang di Dashboard!'})


class KlienProfileView(LoginRequiredMixin, View):
    login_url = LOGIN_URL
    template_name = 'dashboard/klien.html' 

    def dispatch(self, request, *args, **kwargs):
        if request.session.get('user_role') != 'klien_individu':
            messages.error(request, "Akses ditolak. Anda bukan Klien Individu.")
            return redirect('dashboard:index') 
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        no_identitas_klien_str = request.session.get('no_identitas')
        if not no_identitas_klien_str:
            messages.error(request, "Informasi klien tidak ditemukan di sesi.")
            return redirect(LOGIN_URL)

        context = {}
        try:
            with connection.cursor() as cursor:
                query = """
                    SELECT
                        k.no_identitas, k.tanggal_registrasi,
                        u.email, u.alamat, u.nomor_telepon,
                        i.nama_depan, i.nama_tengah, i.nama_belakang
                    FROM PETCLINIC.KLIEN k
                    JOIN PETCLINIC.USER u ON k.email = u.email
                    JOIN PETCLINIC.INDIVIDU i ON k.no_identitas = i.no_identitas_klien
                    WHERE k.no_identitas = %s;
                """
                cursor.execute(query, [no_identitas_klien_str])
                row = cursor.fetchone()

                if row:
                    user_data = {
                        'no_identitas': row[0], 'tanggal_registrasi': row[1],
                        'email': row[2], 'alamat': row[3], 'nomor_telepon': row[4],
                        'nama_depan': row[5], 'nama_tengah': row[6] or '',
                        'nama_belakang': row[7],
                        'nama_lengkap': f"{row[5]} {row[6] or ''} {row[7]}".strip().replace('  ', ' ')
                    }
                    context['user_data'] = user_data
                else:
                    raise Http404("Data klien individu tidak ditemukan.")
        except Http404:
            raise
        except Exception as e:
            messages.error(request, f"Gagal memuat data profil: {str(e)}")
            context['error_message'] = "Gagal memuat data profil."
        
        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request):
        no_identitas_klien_str = request.session.get('no_identitas')
        if not no_identitas_klien_str:
            messages.error(request, "Sesi tidak valid untuk update.")
            return redirect(LOGIN_URL)

        nama_depan = request.POST.get('nama_depan')
        nama_tengah = request.POST.get('nama_tengah', '')
        nama_belakang = request.POST.get('nama_belakang')
        alamat = request.POST.get('alamat')
        nomor_telepon = request.POST.get('nomor_telepon')

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT email FROM PETCLINIC.KLIEN WHERE no_identitas = %s;",
                    [no_identitas_klien_str]
                )
                klien_email_row = cursor.fetchone()
                if not klien_email_row:
                    raise Exception("Email klien tidak ditemukan untuk update USER.")
                klien_email = klien_email_row[0]

                cursor.execute(
                    """
                    UPDATE PETCLINIC.INDIVIDU
                    SET nama_depan = %s, nama_tengah = %s, nama_belakang = %s
                    WHERE no_identitas_klien = %s;
                    """,
                    [nama_depan, nama_tengah if nama_tengah else None, nama_belakang, no_identitas_klien_str]
                )
                cursor.execute(
                    """
                    UPDATE PETCLINIC.USER
                    SET alamat = %s, nomor_telepon = %s
                    WHERE email = %s;
                    """,
                    [alamat, nomor_telepon, klien_email]
                )
            messages.success(request, "Profil berhasil diperbarui!")
        except Exception as e:
            messages.error(request, f"Gagal memperbarui profil: {str(e)}")
        
        return redirect('dashboard:klien')


class KlienCompanyProfileView(LoginRequiredMixin, View):
    login_url = LOGIN_URL
    template_name = 'dashboard/kliencompany.html' 

    def dispatch(self, request, *args, **kwargs):
        if request.session.get('user_role') != 'klien_perusahaan':
            messages.error(request, "Akses ditolak. Anda bukan Klien Perusahaan.")
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        no_identitas_klien_str = request.session.get('no_identitas')
        if not no_identitas_klien_str:
            messages.error(request, "Informasi klien tidak ditemukan di sesi.")
            return redirect(LOGIN_URL)

        context = {}
        try:
            with connection.cursor() as cursor:
                query = """
                    SELECT
                        k.no_identitas, k.tanggal_registrasi,
                        u.email, u.alamat, u.nomor_telepon,
                        p.nama_perusahaan
                    FROM PETCLINIC.KLIEN k
                    JOIN PETCLINIC.USER u ON k.email = u.email
                    JOIN PETCLINIC.PERUSAHAAN p ON k.no_identitas = p.no_identitas_klien
                    WHERE k.no_identitas = %s;
                """
                cursor.execute(query, [no_identitas_klien_str])
                row = cursor.fetchone()

                if row:
                    user_data = {
                        'no_identitas': row[0], 'tanggal_registrasi': row[1],
                        'email': row[2], 'alamat': row[3], 'nomor_telepon': row[4],
                        'nama_perusahaan': row[5]
                    }
                    context['user_data'] = user_data
                else:
                    raise Http404("Data klien perusahaan tidak ditemukan.")
        except Http404:
            raise
        except Exception as e:
            messages.error(request, f"Gagal memuat data profil perusahaan: {str(e)}")
            context['error_message'] = "Gagal memuat data profil."

        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request):
        no_identitas_klien_str = request.session.get('no_identitas')
        if not no_identitas_klien_str:
            messages.error(request, "Sesi tidak valid untuk update.")
            return redirect(LOGIN_URL)

        nama_perusahaan = request.POST.get('nama_perusahaan')
        alamat = request.POST.get('alamat')
        nomor_telepon = request.POST.get('nomor_telepon')

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT email FROM PETCLINIC.KLIEN WHERE no_identitas = %s;",
                    [no_identitas_klien_str]
                )
                klien_email_row = cursor.fetchone()
                if not klien_email_row:
                    raise Exception("Email klien tidak ditemukan untuk update USER.")
                klien_email = klien_email_row[0]

                cursor.execute(
                    """
                    UPDATE PETCLINIC.PERUSAHAAN
                    SET nama_perusahaan = %s
                    WHERE no_identitas_klien = %s;
                    """,
                    [nama_perusahaan, no_identitas_klien_str]
                )
                cursor.execute(
                    """
                    UPDATE PETCLINIC.USER
                    SET alamat = %s, nomor_telepon = %s
                    WHERE email = %s;
                    """,
                    [alamat, nomor_telepon, klien_email]
                )
            messages.success(request, "Profil perusahaan berhasil diperbarui!")
        except Exception as e:
            messages.error(request, f"Gagal memperbarui profil perusahaan: {str(e)}")

        return redirect('dashboard:kliencompany')


class FrontDeskProfileView(LoginRequiredMixin, View):
    login_url = LOGIN_URL
    template_name = 'dashboard/frontdesk.html'  

    def dispatch(self, request, *args, **kwargs):
        if request.session.get('user_role') != 'front_desk':
            messages.error(request, "Akses ditolak. Anda bukan Front Desk.")
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        no_pegawai_str = request.session.get('no_pegawai')
        if not no_pegawai_str:
            messages.error(request, "Informasi pegawai tidak ditemukan di sesi.")
            return redirect(LOGIN_URL)

        context = {}
        try:
            with connection.cursor() as cursor:
                query = """
                    SELECT
                        p.no_pegawai, p.tanggal_mulai_kerja, p.tanggal_akhir_kerja,
                        u.email, u.alamat, u.nomor_telepon
                    FROM PETCLINIC.PEGAWAI p
                    JOIN PETCLINIC.USER u ON p.email_user = u.email
                    JOIN PETCLINIC.FRONT_DESK fd ON p.no_pegawai = fd.no_front_desk
                    WHERE p.no_pegawai = %s;
                """
                cursor.execute(query, [no_pegawai_str])
                row = cursor.fetchone()

                if row:
                    user_data = {
                        'no_pegawai': row[0], 'tanggal_mulai_kerja': row[1],
                        'tanggal_akhir_kerja': row[2], 'email': row[3],
                        'alamat': row[4], 'nomor_telepon': row[5]
                    }
                    context['user_data'] = user_data
                else:
                    raise Http404("Data front desk tidak ditemukan.")
        except Http404:
            raise
        except Exception as e:
            messages.error(request, f"Gagal memuat data profil front desk: {str(e)}")
            context['error_message'] = "Gagal memuat data profil."

        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request):
        no_pegawai_str = request.session.get('no_pegawai')
        if not no_pegawai_str:
            messages.error(request, "Sesi tidak valid untuk update.")
            return redirect(LOGIN_URL)

        alamat = request.POST.get('alamat')
        nomor_telepon = request.POST.get('nomor_telepon')
        tanggal_akhir_kerja = request.POST.get('tanggal_akhir_kerja') or None
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT email_user FROM PETCLINIC.PEGAWAI WHERE no_pegawai = %s;",
                    [no_pegawai_str]
                )
                pegawai_email_row = cursor.fetchone()
                if not pegawai_email_row:
                    raise Exception("Email pegawai tidak ditemukan untuk update USER.")
                pegawai_email = pegawai_email_row[0]

                cursor.execute(
                    """
                    UPDATE PETCLINIC.USER
                    SET alamat = %s, nomor_telepon = %s
                    WHERE email = %s;
                    """,
                    [alamat, nomor_telepon, pegawai_email]
                )
                cursor.execute(
                    """
                    UPDATE PETCLINIC.PEGAWAI
                    SET tanggal_akhir_kerja = %s
                    WHERE no_pegawai = %s;
                    """,
                    [tanggal_akhir_kerja, no_pegawai_str]
                )
            messages.success(request, "Profil front desk berhasil diperbarui!")
        except Exception as e:
            messages.error(request, f"Gagal memperbarui profil front desk: {str(e)}")

        return redirect('dashboard:frontdesk')


class DokterProfileView(LoginRequiredMixin, View):
    login_url = LOGIN_URL
    template_name = 'dashboard/dokter.html'

    def dispatch(self, request, *args, **kwargs):
        if request.session.get('user_role') != 'dokter_hewan':
            messages.error(request, "Akses ditolak. Anda bukan Dokter Hewan.")
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        no_pegawai_str = request.session.get('no_pegawai')
        if not no_pegawai_str:
            messages.error(request, "Informasi dokter tidak ditemukan di sesi.")
            return redirect(LOGIN_URL)

        context = {'error_message': None}
        user_data = {}
        sertifikat_initial_data = []
        jadwal_initial_data = []

        try:
            with connection.cursor() as cursor:
                query_dokter = """
                    SELECT
                        p.no_pegawai, p.tanggal_mulai_kerja, p.tanggal_akhir_kerja,
                        u.email, u.alamat, u.nomor_telepon,
                        tm.no_izin_praktik
                    FROM PETCLINIC.PEGAWAI p
                    JOIN PETCLINIC.USER u ON p.email_user = u.email
                    JOIN PETCLINIC.TENAGA_MEDIS tm ON p.no_pegawai = tm.no_tenaga_medis
                    JOIN PETCLINIC.DOKTER_HEWAN dh ON tm.no_tenaga_medis = dh.no_dokter_hewan
                    WHERE p.no_pegawai = %s;
                """
                cursor.execute(query_dokter, [no_pegawai_str])
                row_dokter = cursor.fetchone()

                if not row_dokter:
                    raise Http404("Data dokter hewan tidak ditemukan.")
                
                user_data = {
                    'no_pegawai': row_dokter[0], 'tanggal_mulai_kerja': row_dokter[1],
                    'tanggal_akhir_kerja': row_dokter[2], 'email': row_dokter[3],
                    'alamat': row_dokter[4], 'nomor_telepon': row_dokter[5],
                    'no_izin_praktik': row_dokter[6]
                }
                
                query_sertifikat = """
                    SELECT no_sertifikat_kompetensi, nama_sertifikat
                    FROM PETCLINIC.SERTIFIKAT_KOMPETENSI
                    WHERE no_tenaga_medis = %s ORDER BY no_sertifikat_kompetensi;
                """
                cursor.execute(query_sertifikat, [no_pegawai_str])
                for row in cursor.fetchall():
                    sertifikat_initial_data.append({
                        'no_sertifikat_kompetensi': row[0],
                        'nama_sertifikat': row[1]
                    })
                user_data['sertifikat_kompetensi'] = sertifikat_initial_data # untuk view mode

                query_jadwal = """
                    SELECT hari, jam
                    FROM PETCLINIC.JADWAL_PRAKTIK
                    WHERE no_dokter_hewan = %s ORDER BY hari, jam;
                """
                cursor.execute(query_jadwal, [no_pegawai_str])
                for row in cursor.fetchall():
                    jadwal_initial_data.append({
                        'hari': row[0],
                        'jam': row[1],
                        'original_hari': row[0], # Untuk identifikasi saat update/delete
                        'original_jam': row[1]   # Untuk identifikasi saat update/delete
                    })
                user_data['jadwal_praktik'] = jadwal_initial_data # untuk view mode
                
            context['user_data'] = user_data
            # Inisialisasi formset dengan data awal
            context['sertifikat_formset'] = SertifikatFormSet(initial=sertifikat_initial_data, prefix='sertifikat')
            context['jadwal_formset'] = JadwalPraktikFormSet(initial=jadwal_initial_data, prefix='jadwal')

        except Http404:
            raise
        except Exception as e:
            messages.error(request, f"Gagal memuat data profil dokter: {str(e)}")
            context['error_message'] = "Gagal memuat data profil."
            if 'sertifikat_formset' not in context:
                 context['sertifikat_formset'] = SertifikatFormSet(prefix='sertifikat')
            if 'jadwal_formset' not in context:
                 context['jadwal_formset'] = JadwalPraktikFormSet(prefix='jadwal')


        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request):
        no_pegawai_str = request.session.get('no_pegawai') # Ini juga no_tenaga_medis
        if not no_pegawai_str:
            messages.error(request, "Sesi tidak valid untuk update.")
            return redirect(LOGIN_URL)

        # Data profil dasar
        alamat = request.POST.get('alamat')
        nomor_telepon = request.POST.get('nomor_telepon')
        # no_izin_praktik tidak diupdate dari sini lagi
        tanggal_akhir_kerja_str = request.POST.get('tanggal_akhir_kerja')
        tanggal_akhir_kerja_db = None
        if tanggal_akhir_kerja_str:
            tanggal_akhir_kerja_db = tanggal_akhir_kerja_str

        # Proses Formsets
        sertifikat_formset = SertifikatFormSet(request.POST, prefix='sertifikat')
        jadwal_formset = JadwalPraktikFormSet(request.POST, prefix='jadwal')

        # Validasi formset
        sertifikat_valid = sertifikat_formset.is_valid()
        jadwal_valid = jadwal_formset.is_valid()

        if not sertifikat_valid or not jadwal_valid:
            messages.error(request, "Terdapat kesalahan pada data sertifikat atau jadwal. Mohon periksa kembali.")
            context = {
                'user_data': {}, 
                'sertifikat_formset': sertifikat_formset, 
                'jadwal_formset': jadwal_formset, 
                'error_message': "Harap perbaiki kesalahan pada form.", # Pesan error yang lebih umum
                'open_edit_mode': True  
            }
            try:
                with connection.cursor() as cursor_get_user: # Ambil lagi user_data untuk tampilan
                    query_dokter = "SELECT p.no_pegawai, p.tanggal_mulai_kerja, p.tanggal_akhir_kerja, u.email, u.alamat, u.nomor_telepon, tm.no_izin_praktik FROM PETCLINIC.PEGAWAI p JOIN PETCLINIC.\"USER\" u ON p.email_user = u.email JOIN PETCLINIC.TENAGA_MEDIS tm ON p.no_pegawai = tm.no_tenaga_medis JOIN PETCLINIC.DOKTER_HEWAN dh ON tm.no_tenaga_medis = dh.no_dokter_hewan WHERE p.no_pegawai = %s;"
                    cursor_get_user.execute(query_dokter, [no_pegawai_str])
                    row_dokter = cursor_get_user.fetchone()
                    if row_dokter:
                        context['user_data'] = {
                            'no_pegawai': row_dokter[0], 'tanggal_mulai_kerja': row_dokter[1],
                            'tanggal_akhir_kerja': row_dokter[2], 'email': row_dokter[3],
                            'alamat': row_dokter[4], 'nomor_telepon': row_dokter[5],
                            'no_izin_praktik': row_dokter[6]
                        }
                    # Untuk view mode, ambil lagi data sertifikat dan jadwal dari DB
                    cursor_get_user.execute("SELECT no_sertifikat_kompetensi, nama_sertifikat FROM PETCLINIC.SERTIFIKAT_KOMPETENSI WHERE no_tenaga_medis = %s;", [no_pegawai_str])
                    context['user_data']['sertifikat_kompetensi'] = [{'no': r[0], 'nama': r[1]} for r in cursor_get_user.fetchall()]
                    cursor_get_user.execute("SELECT hari, jam FROM PETCLINIC.JADWAL_PRAKTIK WHERE no_dokter_hewan = %s;", [no_pegawai_str])
                    context['user_data']['jadwal_praktik'] = [{'hari': r[0], 'jam': r[1]} for r in cursor_get_user.fetchall()]

            except Exception as e_fetch:
                messages.error(request, f"Gagal memuat ulang data profil: {e_fetch}")

            # Paksa edit mode terbuka jika ada error formset
            context['open_edit_mode'] = True
            return render(request, self.template_name, context)


        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT email_user FROM PETCLINIC.PEGAWAI WHERE no_pegawai = %s;", [no_pegawai_str])
                pegawai_email_row = cursor.fetchone()
                if not pegawai_email_row:
                    raise Exception("Email pegawai tidak ditemukan.")
                pegawai_email = pegawai_email_row[0]

                cursor.execute(
                    'UPDATE PETCLINIC.USER SET alamat = %s, nomor_telepon = %s WHERE email = %s;',
                    [alamat, nomor_telepon, pegawai_email]
                )
                cursor.execute(
                    "UPDATE PETCLINIC.PEGAWAI SET tanggal_akhir_kerja = %s WHERE no_pegawai = %s;",
                    [tanggal_akhir_kerja_db, no_pegawai_str]
                )
                cursor.execute("SELECT no_sertifikat_kompetensi FROM PETCLINIC.SERTIFIKAT_KOMPETENSI WHERE no_tenaga_medis = %s", [no_pegawai_str])
                existing_sertifikat_pks = {row[0] for row in cursor.fetchall()}
                processed_sertifikat_pks = set()

                for form in sertifikat_formset:
                    if form.is_valid() and form.cleaned_data: # Pastikan form tidak kosong
                        no_sert = form.cleaned_data.get('no_sertifikat_kompetensi')
                        nama_sert = form.cleaned_data.get('nama_sertifikat')
                        to_delete = form.cleaned_data.get('DELETE', False)

                        if not no_sert or not nama_sert: # Lewati form kosong dari `extra`
                            if to_delete and no_sert in existing_sertifikat_pks: # Jika form kosong tapi ditandai delete dan ada di DB
                                cursor.execute("DELETE FROM PETCLINIC.SERTIFIKAT_KOMPETENSI WHERE no_sertifikat_kompetensi = %s AND no_tenaga_medis = %s", [no_sert, no_pegawai_str])
                                existing_sertifikat_pks.discard(no_sert)
                            continue
                        
                        processed_sertifikat_pks.add(no_sert)

                        if to_delete:
                            if no_sert in existing_sertifikat_pks:
                                cursor.execute("DELETE FROM PETCLINIC.SERTIFIKAT_KOMPETENSI WHERE no_sertifikat_kompetensi = %s AND no_tenaga_medis = %s", [no_sert, no_pegawai_str])
                                existing_sertifikat_pks.discard(no_sert)
                        elif no_sert in existing_sertifikat_pks:
                            # Update
                            cursor.execute(
                                "UPDATE PETCLINIC.SERTIFIKAT_KOMPETENSI SET nama_sertifikat = %s WHERE no_sertifikat_kompetensi = %s AND no_tenaga_medis = %s",
                                [nama_sert, no_sert, no_pegawai_str]
                            )
                        else:
                            # Insert baru
                            cursor.execute(
                                "INSERT INTO PETCLINIC.SERTIFIKAT_KOMPETENSI (no_sertifikat_kompetensi, no_tenaga_medis, nama_sertifikat) VALUES (%s, %s, %s)",
                                [no_sert, no_pegawai_str, nama_sert]
                            )

                cursor.execute("SELECT hari, jam FROM PETCLINIC.JADWAL_PRAKTIK WHERE no_dokter_hewan = %s", [no_pegawai_str])
                existing_jadwal = {(row[0], row[1]) for row in cursor.fetchall()} # set of (hari, jam) tuples

                for form_jadwal in jadwal_formset:
                    if form_jadwal.is_valid() and form_jadwal.cleaned_data:
                        hari = form_jadwal.cleaned_data.get('hari')
                        jam = form_jadwal.cleaned_data.get('jam')
                        to_delete = form_jadwal.cleaned_data.get('DELETE', False)
                        original_hari = form_jadwal.cleaned_data.get('original_hari')
                        original_jam = form_jadwal.cleaned_data.get('original_jam')

                        if not hari or not jam: # Lewati form kosong
                            if to_delete and original_hari and original_jam and (original_hari, original_jam) in existing_jadwal:
                                cursor.execute("DELETE FROM PETCLINIC.JADWAL_PRAKTIK WHERE no_dokter_hewan = %s AND hari = %s AND jam = %s",
                                               [no_pegawai_str, original_hari, original_jam])
                                existing_jadwal.discard((original_hari, original_jam))
                            continue

                        current_pk = (hari, jam)
                        original_pk = (original_hari, original_jam) if original_hari and original_jam else None
                        
                        if to_delete:
                            if original_pk and original_pk in existing_jadwal:
                                cursor.execute("DELETE FROM PETCLINIC.JADWAL_PRAKTIK WHERE no_dokter_hewan = %s AND hari = %s AND jam = %s",
                                               [no_pegawai_str, original_hari, original_jam])
                                existing_jadwal.discard(original_pk)
                        elif original_pk and original_pk in existing_jadwal : # Ini adalah entri yang ada
                            if original_pk != current_pk: # PK berubah, berarti delete yang lama, insert yang baru
                                cursor.execute("DELETE FROM PETCLINIC.JADWAL_PRAKTIK WHERE no_dokter_hewan = %s AND hari = %s AND jam = %s",
                                               [no_pegawai_str, original_hari, original_jam])
                                cursor.execute("INSERT INTO PETCLINIC.JADWAL_PRAKTIK (no_dokter_hewan, hari, jam) VALUES (%s, %s, %s)",
                                               [no_pegawai_str, hari, jam])
                                existing_jadwal.discard(original_pk) # Hapus yang lama
                                existing_jadwal.add(current_pk) # Tambah yang baru, meskipun mungkin tidak perlu jika loop ini selesai
                            # else: PK tidak berubah, tidak perlu update karena hanya ada PK.
                        elif current_pk not in existing_jadwal: # Ini entri baru
                            cursor.execute("INSERT INTO PETCLINIC.JADWAL_PRAKTIK (no_dokter_hewan, hari, jam) VALUES (%s, %s, %s)",
                                           [no_pegawai_str, hari, jam])
                            existing_jadwal.add(current_pk)


            messages.success(request, "Profil dokter berhasil diperbarui!")
        except IntegrityError as e:
            messages.error(request, f"Gagal memperbarui profil. Terjadi duplikasi data (misalnya nomor sertifikat atau jadwal): {e}")
        except DatabaseError as e:
            messages.error(request, f"Gagal memperbarui profil dokter: {e}")
        except Exception as e: # Tangkap error umum lainnya
            messages.error(request, f"Terjadi kesalahan tak terduga: {e}")
        
        return redirect('dashboard:dokter')


class PerawatProfileView(LoginRequiredMixin, View):
    login_url = LOGIN_URL
    template_name = 'dashboard/perawat.html' 

    def dispatch(self, request, *args, **kwargs):
        if request.session.get('user_role') != 'perawat_hewan':
            messages.error(request, "Akses ditolak. Anda bukan Perawat Hewan.")
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        no_pegawai_str = request.session.get('no_pegawai') # Ini adalah no_tenaga_medis / no_perawat_hewan
        if not no_pegawai_str:
            messages.error(request, "Informasi perawat tidak ditemukan di sesi.")
            return redirect(LOGIN_URL)

        context = {'error_message': None, 'user_data': None}
        sertifikat_initial_data = []
        user_data = {}

        try:
            with connection.cursor() as cursor:
                query_perawat = """
                    SELECT
                        p.no_pegawai, p.tanggal_mulai_kerja, p.tanggal_akhir_kerja,
                        u.email, u.alamat, u.nomor_telepon,
                        tm.no_izin_praktik
                    FROM PETCLINIC.PEGAWAI p
                    JOIN PETCLINIC.USER u ON p.email_user = u.email
                    JOIN PETCLINIC.TENAGA_MEDIS tm ON p.no_pegawai = tm.no_tenaga_medis
                    JOIN PETCLINIC.PERAWAT_HEWAN ph ON tm.no_tenaga_medis = ph.no_perawat_hewan
                    WHERE p.no_pegawai = %s;
                """
                cursor.execute(query_perawat, [no_pegawai_str])
                row_perawat = cursor.fetchone()

                if not row_perawat:
                    raise Http404("Data perawat hewan tidak ditemukan.")
                
                user_data = {
                    'no_pegawai': row_perawat[0], 'tanggal_mulai_kerja': row_perawat[1],
                    'tanggal_akhir_kerja': row_perawat[2], 'email': row_perawat[3],
                    'alamat': row_perawat[4], 'nomor_telepon': row_perawat[5],
                    'no_izin_praktik': row_perawat[6]
                }
                
                query_sertifikat = """
                    SELECT no_sertifikat_kompetensi, nama_sertifikat
                    FROM PETCLINIC.SERTIFIKAT_KOMPETENSI
                    WHERE no_tenaga_medis = %s ORDER BY no_sertifikat_kompetensi;
                """
                cursor.execute(query_sertifikat, [no_pegawai_str])
                for row in cursor.fetchall():
                    sertifikat_initial_data.append({
                        'no_sertifikat_kompetensi': row[0],
                        'nama_sertifikat': row[1]
                    })
                user_data['sertifikat_kompetensi'] = sertifikat_initial_data # untuk view mode
                
            context['user_data'] = user_data
            context['sertifikat_formset'] = SertifikatFormSet(initial=sertifikat_initial_data, prefix='sertifikat')

        except Http404:
            # Jika Http404, biarkan Django yang handle atau redirect dengan pesan
            messages.error(request, "Data profil perawat tidak ditemukan.")
            return redirect('dashboard:index') # Atau halaman error yang sesuai
        except Exception as e:
            messages.error(request, f"Gagal memuat data profil perawat: {str(e)}")
            context['error_message'] = "Gagal memuat data profil."
            if 'sertifikat_formset' not in context: # Pastikan formset kosong jika ada error
                 context['sertifikat_formset'] = SertifikatFormSet(prefix='sertifikat')
        
        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request):
        no_pegawai_str = request.session.get('no_pegawai') # Ini adalah no_tenaga_medis
        alamat = request.POST.get('alamat')
        nomor_telepon = request.POST.get('nomor_telepon')
        tanggal_akhir_kerja_str = request.POST.get('tanggal_akhir_kerja')
        tanggal_akhir_kerja_db = None
        if tanggal_akhir_kerja_str and tanggal_akhir_kerja_str.strip() != "":
            tanggal_akhir_kerja_db = tanggal_akhir_kerja_str


        sertifikat_formset = SertifikatFormSet(request.POST, prefix='sertifikat')

        if not sertifikat_formset.is_valid():
            messages.error(request, "Terdapat kesalahan pada data sertifikat. Mohon periksa kembali.")
            context = {
                'user_data': {}, 
                'sertifikat_formset': sertifikat_formset, 
                'error_message': "Harap perbaiki kesalahan pada form.",
                'open_edit_mode': True
            }
            try:
                with connection.cursor() as cursor_get_user:
                    query_perawat = "SELECT p.no_pegawai, p.tanggal_mulai_kerja, p.tanggal_akhir_kerja, u.email, u.alamat, u.nomor_telepon, tm.no_izin_praktik FROM PETCLINIC.PEGAWAI p JOIN PETCLINIC.\"USER\" u ON p.email_user = u.email JOIN PETCLINIC.TENAGA_MEDIS tm ON p.no_pegawai = tm.no_tenaga_medis JOIN PETCLINIC.PERAWAT_HEWAN ph ON tm.no_tenaga_medis = ph.no_perawat_hewan WHERE p.no_pegawai = %s;"
                    cursor_get_user.execute(query_perawat, [no_pegawai_str])
                    row_perawat = cursor_get_user.fetchone()
                    current_user_data = {}
                    if row_perawat:
                        current_user_data = {
                            'no_pegawai': row_perawat[0], 'tanggal_mulai_kerja': row_perawat[1],
                            'tanggal_akhir_kerja': row_perawat[2], 'email': row_perawat[3],
                            'alamat': row_perawat[4], 'nomor_telepon': row_perawat[5],
                            'no_izin_praktik': row_perawat[6]
                        }
                    # Ambil data sertifikat aktual
                    cursor_get_user.execute("SELECT no_sertifikat_kompetensi, nama_sertifikat FROM PETCLINIC.SERTIFIKAT_KOMPETENSI WHERE no_tenaga_medis = %s;", [no_pegawai_str])
                    sert_data_for_context = []
                    for r_sert in cursor_get_user.fetchall():
                        sert_data_for_context.append({'no_sertifikat_kompetensi': r_sert[0], 'nama_sertifikat': r_sert[1]})
                    current_user_data['sertifikat_kompetensi'] = sert_data_for_context
                    context['user_data'] = current_user_data
            except Exception as e_fetch:
                messages.error(request, f"Gagal memuat ulang data profil: {e_fetch}")
                context['user_data'] = {'sertifikat_kompetensi': []} 
            return render(request, self.template_name, context)


        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT email_user FROM PETCLINIC.PEGAWAI WHERE no_pegawai = %s;", [no_pegawai_str])
                pegawai_email_row = cursor.fetchone()
                if not pegawai_email_row:
                    raise Exception("Email pegawai tidak ditemukan.")
                pegawai_email = pegawai_email_row[0]
                cursor.execute(
                    'UPDATE PETCLINIC.USER SET alamat = %s, nomor_telepon = %s WHERE email = %s;',
                    [alamat, nomor_telepon, pegawai_email]
                )
                cursor.execute(
                    "UPDATE PETCLINIC.PEGAWAI SET tanggal_akhir_kerja = %s WHERE no_pegawai = %s;",
                    [tanggal_akhir_kerja_db, no_pegawai_str]
                )

                cursor.execute("SELECT no_sertifikat_kompetensi, nama_sertifikat FROM PETCLINIC.SERTIFIKAT_KOMPETENSI WHERE no_tenaga_medis = %s", [no_pegawai_str])
                db_sertifikat_map = {row[0]: row[1] for row in cursor.fetchall()} # {no_sert: nama_sert_di_db}

                # Data dari form yang akan dipertahankan/diupdate/diinsert
                form_sertifikat_data = {} # {no_sert_form: nama_sert_form}
                sertifikat_to_delete_explicitly_pks = set() # PKs yang dicentang DELETE

                for form in sertifikat_formset:
                    if form.cleaned_data: # Hanya proses form yang valid dan punya data
                        no_sert_form = form.cleaned_data.get('no_sertifikat_kompetensi')
                        nama_sert_form = form.cleaned_data.get('nama_sertifikat')
                        to_delete_checked = form.cleaned_data.get('DELETE', False)
                        original_pk_from_form = form.initial.get('no_sertifikat_kompetensi')

                        if not no_sert_form or not nama_sert_form: # Data tidak lengkap
                            if to_delete_checked and original_pk_from_form and original_pk_from_form in db_sertifikat_map:
                                sertifikat_to_delete_explicitly_pks.add(original_pk_from_form)
                            continue

                        if to_delete_checked:
                            if original_pk_from_form and original_pk_from_form in db_sertifikat_map:
                                sertifikat_to_delete_explicitly_pks.add(original_pk_from_form)
                            # Jika dicentang delete tapi tidak ada original_pk atau tidak di DB, abaikan (form baru dicentang delete)
                            continue # Jangan proses lebih lanjut untuk insert/update
                        if original_pk_from_form and original_pk_from_form != no_sert_form and original_pk_from_form in db_sertifikat_map:
                             sertifikat_to_delete_explicitly_pks.add(original_pk_from_form) 
                        form_sertifikat_data[no_sert_form] = nama_sert_form
                
                pks_in_db = set(db_sertifikat_map.keys())
                pks_in_form_valid_data = set(form_sertifikat_data.keys())

                sertifikat_to_delete_db_pks = (pks_in_db - pks_in_form_valid_data) | sertifikat_to_delete_explicitly_pks
                
                for pk_del in sertifikat_to_delete_db_pks:
                    if pk_del in db_sertifikat_map: # Pastikan masih ada di map DB awal
                        cursor.execute(
                            "DELETE FROM PETCLINIC.SERTIFIKAT_KOMPETENSI WHERE no_sertifikat_kompetensi = %s AND no_tenaga_medis = %s",
                            [pk_del, no_pegawai_str]
                        )
                

                for no_sert_proses, nama_sert_proses in form_sertifikat_data.items():
                    if no_sert_proses in db_sertifikat_map: 
                        if db_sertifikat_map[no_sert_proses] != nama_sert_proses:
                            cursor.execute(
                                "UPDATE PETCLINIC.SERTIFIKAT_KOMPETENSI SET nama_sertifikat = %s WHERE no_sertifikat_kompetensi = %s AND no_tenaga_medis = %s",
                                [nama_sert_proses, no_sert_proses, no_pegawai_str]
                            )
                    else: 
                        cursor.execute(
                            "INSERT INTO PETCLINIC.SERTIFIKAT_KOMPETENSI (no_sertifikat_kompetensi, no_tenaga_medis, nama_sertifikat) VALUES (%s, %s, %s)",
                            [no_sert_proses, no_pegawai_str, nama_sert_proses]
                        )
                        # Jika insert berhasil, tambahkan ke db_sertifikat_map agar tidak diinsert lagi jika ada duplikat di form
                        db_sertifikat_map[no_sert_proses] = nama_sert_proses 

            messages.success(request, "Profil perawat berhasil diperbarui!")

        except IntegrityError as e:
            messages.error(request, f"Gagal memperbarui profil. Terjadi duplikasi data atau pelanggaran constraint: {e}")
            # Re-render form dengan error dan data yang diinput user
            context_error = {'user_data': {}, 'sertifikat_formset': sertifikat_formset, 'error_message': str(e), 'open_edit_mode': True}
            try:
                with connection.cursor() as cursor_get_user:
                    query_perawat = "SELECT p.no_pegawai, p.tanggal_mulai_kerja, p.tanggal_akhir_kerja, u.email, u.alamat, u.nomor_telepon, tm.no_izin_praktik FROM PETCLINIC.PEGAWAI p JOIN PETCLINIC.\"USER\" u ON p.email_user = u.email JOIN PETCLINIC.TENAGA_MEDIS tm ON p.no_pegawai = tm.no_tenaga_medis JOIN PETCLINIC.PERAWAT_HEWAN ph ON tm.no_tenaga_medis = ph.no_perawat_hewan WHERE p.no_pegawai = %s;"
                    cursor_get_user.execute(query_perawat, [no_pegawai_str])
                    row_perawat = cursor_get_user.fetchone()
                    current_user_data_err = {}
                    if row_perawat:
                        current_user_data_err = {
                            'no_pegawai': row_perawat[0], 'tanggal_mulai_kerja': row_perawat[1],
                            'tanggal_akhir_kerja': row_perawat[2], 'email': row_perawat[3],
                            'alamat': row_perawat[4], 'nomor_telepon': row_perawat[5],
                            'no_izin_praktik': row_perawat[6]
                        }
                    cursor_get_user.execute("SELECT no_sertifikat_kompetensi, nama_sertifikat FROM PETCLINIC.SERTIFIKAT_KOMPETENSI WHERE no_tenaga_medis = %s;", [no_pegawai_str])
                    sert_data_for_context_err = []
                    for r_sert_err in cursor_get_user.fetchall():
                        sert_data_for_context_err.append({'no_sertifikat_kompetensi': r_sert_err[0], 'nama_sertifikat': r_sert_err[1]})
                    current_user_data_err['sertifikat_kompetensi'] = sert_data_for_context_err
                    context_error['user_data'] = current_user_data_err
            except Exception as e_fetch_err:
                messages.error(request, f"Gagal memuat ulang data profil setelah error: {e_fetch_err}")
                context_error['user_data'] = {'sertifikat_kompetensi': []}
            return render(request, self.template_name, context_error)

        except DatabaseError as e: 
            messages.error(request, f"Gagal memperbarui profil perawat (Database Error): {e}")
        except Exception as e: 
            messages.error(request, f"Terjadi kesalahan tak terduga: {e}")
        
        return redirect('dashboard:perawat')
    
class PasswordChangeCustomView(LoginRequiredMixin, View):
    login_url = LOGIN_URL # Make sure LOGIN_URL is defined
    template_name = 'dashboard/password_change_form.html' # New template
    form_class = CustomPasswordChangeForm

    def get(self, request, *args, **kwargs):
        form = self.form_class(user=request.user)
        return render(request, self.template_name, {'form': form})

    @transaction.atomic 
    def post(self, request, *args, **kwargs):
        form = self.form_class(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            user_role = request.session.get('user_role')
            if user_role == 'klien_individu':
                return redirect('dashboard:klien')
            elif user_role == 'klien_perusahaan':
                return redirect('dashboard:kliencompany')
            elif user_role == 'front_desk':
                return redirect('dashboard:frontdesk')
            elif user_role == 'dokter_hewan':
                return redirect('dashboard:dokter')
            elif user_role == 'perawat_hewan':
                return redirect('dashboard:perawat')
            else:
                return redirect('dashboard:index') # Fallback
        else:
            messages.error(request, 'Please correct the error below.')
        return render(request, self.template_name, {'form': form})