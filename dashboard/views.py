from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connection, transaction
from django.http import Http404
from django.contrib import messages
import uuid # Meskipun tidak dipakai langsung di sini, jaga-jaga
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required # for function-based view
from django.utils.decorators import method_decorator # for class-based view
from .forms import CustomPasswordChangeForm # Import the new form

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
        # Pengguna terautentikasi tetapi tidak memiliki peran yang dikenali di sesi
        # Atau ini adalah halaman dashboard umum
        # Anda bisa logout pengguna atau menampilkan halaman error/dashboard umum
        # messages.warning(request, "Peran pengguna tidak dikenali. Silakan login kembali.")
        # return redirect('authentication:logout_view')
        return render(request, 'dashboard/index.html', {'message': 'Selamat datang di Dashboard!'})


class KlienProfileView(LoginRequiredMixin, View):
    login_url = LOGIN_URL
    template_name = 'dashboard/klien.html' # Sesuaikan dengan nama file template Anda

    def dispatch(self, request, *args, **kwargs):
        if request.session.get('user_role') != 'klien_individu':
            messages.error(request, "Akses ditolak. Anda bukan Klien Individu.")
            return redirect('dashboard:index') # atau ke halaman login
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
    template_name = 'dashboard/frontdesk.html' # Buat template ini

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
                # Front desk tidak punya nama sendiri di tabelnya, nama diambil dari USER
                # tapi user tidak ada nama, jadi kita hanya ambil email, alamat, dll.
                # Biasanya nama pegawai akan dihandle oleh sistem HR terpisah atau field nama di tabel User/Pegawai
                # Untuk contoh ini, kita asumsikan Front Desk tidak memiliki 'nama' spesifik di luar email.
                # Jika ada tabel terpisah untuk nama pegawai (misal di `USER` atau `PEGAWAI` ada kolom nama), querynya perlu disesuaikan.
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
                        # Tambahkan 'nama' jika ada di tabel USER atau PEGAWAI
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
        # tanggal_mulai_kerja, tanggal_akhir_kerja biasanya tidak diupdate oleh user sendiri
        
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
    template_name = 'dashboard/dokter.html' # Buat template ini

    def dispatch(self, request, *args, **kwargs):
        if request.session.get('user_role') != 'dokter_hewan':
            messages.error(request, "Akses ditolak. Anda bukan Dokter Hewan.")
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        no_pegawai_str = request.session.get('no_pegawai') # Ini adalah no_tenaga_medis / no_dokter_hewan
        if not no_pegawai_str:
            messages.error(request, "Informasi dokter tidak ditemukan di sesi.")
            return redirect(LOGIN_URL)

        context = {}
        try:
            with connection.cursor() as cursor:
                # Asumsi dokter juga punya nama depan, tengah, belakang di tabel USER
                # Jika tidak, skema USER perlu ditambah field nama atau join ke tabel lain
                # Untuk saat ini, kita ambil data dasar dokter
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
                    # Tambahkan 'nama' jika ada di tabel USER atau PEGAWAI. Jika tidak ada, nama harus diambil dari sumber lain atau form registrasi yang lebih lengkap.
                    # Untuk simulasi, kita anggap nama ada di form registrasi dan disimpan di session atau tabel USER.
                    # Jika nama ada di USER, perlu JOIN atau query tambahan.
                }
                
                # Ambil Sertifikat Kompetensi
                query_sertifikat = """
                    SELECT no_sertifikat_kompetensi, nama_sertifikat
                    FROM PETCLINIC.SERTIFIKAT_KOMPETENSI
                    WHERE no_tenaga_medis = %s;
                """
                cursor.execute(query_sertifikat, [no_pegawai_str])
                sertifikat_list = [{'no': r[0], 'nama': r[1]} for r in cursor.fetchall()]
                user_data['sertifikat_kompetensi'] = sertifikat_list

                # Ambil Jadwal Praktik
                query_jadwal = """
                    SELECT hari, jam
                    FROM PETCLINIC.JADWAL_PRAKTIK
                    WHERE no_dokter_hewan = %s;
                """
                cursor.execute(query_jadwal, [no_pegawai_str])
                jadwal_list = [{'hari': r[0], 'jam': r[1]} for r in cursor.fetchall()]
                user_data['jadwal_praktik'] = jadwal_list
                
                context['user_data'] = user_data

        except Http404:
            raise
        except Exception as e:
            messages.error(request, f"Gagal memuat data profil dokter: {str(e)}")
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
        no_izin_praktik_baru = request.POST.get('no_izin_praktik') # Jika ini bisa diubah

        # Mengupdate sertifikat dan jadwal praktik memerlukan logika yang lebih kompleks
        # (menghapus yang lama, menambah yang baru, atau memodifikasi yang ada).
        # Untuk contoh ini, kita hanya update data dasar.

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
                
                # Update nomor izin praktik jika diizinkan
                if no_izin_praktik_baru:
                    cursor.execute(
                        """
                        UPDATE PETCLINIC.TENAGA_MEDIS
                        SET no_izin_praktik = %s
                        WHERE no_tenaga_medis = %s;
                        """,
                        [no_izin_praktik_baru, no_pegawai_str]
                    )

            messages.success(request, "Profil dokter berhasil diperbarui!")
        except Exception as e:
            messages.error(request, f"Gagal memperbarui profil dokter: {str(e)}")

        return redirect('dashboard:dokter')


class PerawatProfileView(LoginRequiredMixin, View):
    login_url = LOGIN_URL
    template_name = 'dashboard/perawat.html' # Buat template ini

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

        context = {}
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
                    # Tambahkan 'nama' jika ada.
                }

                # Ambil Sertifikat Kompetensi
                query_sertifikat = """
                    SELECT no_sertifikat_kompetensi, nama_sertifikat
                    FROM PETCLINIC.SERTIFIKAT_KOMPETENSI
                    WHERE no_tenaga_medis = %s;
                """
                cursor.execute(query_sertifikat, [no_pegawai_str])
                sertifikat_list = [{'no': r[0], 'nama': r[1]} for r in cursor.fetchall()]
                user_data['sertifikat_kompetensi'] = sertifikat_list
                
                context['user_data'] = user_data
        except Http404:
            raise
        except Exception as e:
            messages.error(request, f"Gagal memuat data profil perawat: {str(e)}")
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
        no_izin_praktik_baru = request.POST.get('no_izin_praktik')

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
                
                if no_izin_praktik_baru:
                    cursor.execute(
                        """
                        UPDATE PETCLINIC.TENAGA_MEDIS
                        SET no_izin_praktik = %s
                        WHERE no_tenaga_medis = %s;
                        """,
                        [no_izin_praktik_baru, no_pegawai_str]
                    )
            messages.success(request, "Profil perawat berhasil diperbarui!")
        except Exception as e:
            messages.error(request, f"Gagal memperbarui profil perawat: {str(e)}")

        return redirect('dashboard:perawat')
    
class PasswordChangeCustomView(LoginRequiredMixin, View):
    login_url = LOGIN_URL # Make sure LOGIN_URL is defined
    template_name = 'dashboard/password_change_form.html' # New template
    form_class = CustomPasswordChangeForm

    def get(self, request, *args, **kwargs):
        form = self.form_class(user=request.user)
        return render(request, self.template_name, {'form': form})

    @transaction.atomic # Ensure both password updates are atomic
    def post(self, request, *args, **kwargs):
        form = self.form_class(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Important: Update the session authentication hash, or the user will be logged out.
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            
            # Redirect to the appropriate profile page based on role
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