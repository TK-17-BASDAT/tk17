from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import connection, transaction
from django.views import View
import uuid

class LoginView(View):
    template_name = 'authentication/login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        return render(request, self.template_name)
    
    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT no_identitas FROM petclinic.klien WHERE email = %s", [email])
                klien_row = cursor.fetchone()
                
                if klien_row:
                    no_identitas = klien_row[0]
                    
                    cursor.execute("SELECT 1 FROM petclinic.individu WHERE no_identitas_klien = %s", [no_identitas])
                    is_individu = cursor.fetchone() is not None
                    
                    cursor.execute("SELECT 1 FROM petclinic.perusahaan WHERE no_identitas_klien = %s", [no_identitas])
                    is_perusahaan = cursor.fetchone() is not None
                    
                    if is_individu:
                        request.session['user_role'] = 'klien_individu'
                        request.session['no_identitas'] = str(no_identitas)
                        return redirect('dashboard:klien')
                    elif is_perusahaan:
                        request.session['user_role'] = 'klien_perusahaan'
                        request.session['no_identitas'] = str(no_identitas)
                        return redirect('dashboard:kliencompany')
                else:
                    cursor.execute("SELECT no_pegawai FROM petclinic.pegawai WHERE email_user = %s", [email])
                    pegawai_row = cursor.fetchone()
                    
                    if pegawai_row:
                        no_pegawai = pegawai_row[0]
                        
                        cursor.execute("SELECT 1 FROM petclinic.front_desk WHERE no_front_desk = %s", [no_pegawai])
                        is_front_desk = cursor.fetchone() is not None
                        
                        if is_front_desk:
                            request.session['user_role'] = 'front_desk'
                            request.session['no_pegawai'] = str(no_pegawai)
                            return redirect('dashboard:frontdesk')
                        else:
                            cursor.execute("SELECT no_tenaga_medis FROM petclinic.tenaga_medis WHERE no_tenaga_medis = %s", [no_pegawai])
                            tenaga_medis_row = cursor.fetchone()
                            
                            if tenaga_medis_row:
                                no_tenaga_medis = tenaga_medis_row[0]
                                
                                cursor.execute("SELECT 1 FROM petclinic.dokter_hewan WHERE no_dokter_hewan = %s", [no_tenaga_medis])
                                is_dokter = cursor.fetchone() is not None
                                
                                cursor.execute("SELECT 1 FROM petclinic.perawat_hewan WHERE no_perawat_hewan = %s", [no_tenaga_medis])
                                is_perawat = cursor.fetchone() is not None
                                
                                if is_dokter:
                                    request.session['user_role'] = 'dokter_hewan'
                                    request.session['no_pegawai'] = str(no_pegawai)
                                    return redirect('dashboard:dokter')
                                elif is_perawat:
                                    request.session['user_role'] = 'perawat_hewan'
                                    request.session['no_pegawai'] = str(no_pegawai)
                                    return redirect('dashboard:perawat')
            
            return redirect('dashboard:index')
        else:
            messages.error(request, "Invalid email or password")
            return render(request, self.template_name)


class RegisterView(View):
    """
    View for user registration
    """
    template_name = 'authentication/register.html'
    
    def get(self, request):
        return render(request, self.template_name)
    
    @transaction.atomic
    def post(self, request):
        form_type = request.POST.get('form_type')
        
        if form_type == 'klien_individu':
            return self.register_klien_individu(request)
        elif form_type == 'klien_perusahaan':
            return self.register_klien_perusahaan(request)
        elif form_type == 'front_desk':
            return self.register_front_desk(request)
        elif form_type == 'dokter_hewan':
            return self.register_dokter_hewan(request)
        elif form_type == 'perawat_hewan':
            return self.register_perawat_hewan(request)
        else:
            messages.error(request, "Invalid form type")
            return render(request, self.template_name)
    
    def register_klien_individu(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        nomor_telepon = request.POST.get('nomor_telepon')
        alamat = request.POST.get('alamat')
        nama_depan = request.POST.get('nama_depan')
        nama_tengah = request.POST.get('nama_tengah', '')
        nama_belakang = request.POST.get('nama_belakang')
        
        try:
            user = User.objects.create_user(
                username=email, 
                email=email,
                password=password
            )
            
            with connection.cursor() as cursor:
                cursor.execute(
                    'INSERT INTO petclinic."user" (email, password, alamat, nomor_telepon) VALUES (%s, %s, %s, %s)',
                    [email, user.password, alamat, nomor_telepon]
                )
                
                no_identitas = uuid.uuid4()
                
                cursor.execute(
                    'INSERT INTO petclinic.klien (no_identitas, tanggal_registrasi, email) VALUES (%s, NOW(), %s)',
                    [no_identitas, email]
                )
                
                cursor.execute(
                    'INSERT INTO petclinic.individu (no_identitas_klien, nama_depan, nama_tengah, nama_belakang) VALUES (%s, %s, %s, %s)',
                    [no_identitas, nama_depan, nama_tengah, nama_belakang]
                )
            
            login(request, user)
            
            request.session['user_role'] = 'klien_individu'
            request.session['no_identitas'] = str(no_identitas)
            
            return redirect('authentication:login')
        
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return render(request, self.template_name)
    
    def register_klien_perusahaan(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        nomor_telepon = request.POST.get('nomor_telepon')
        alamat = request.POST.get('alamat')
        nama_perusahaan = request.POST.get('nama_perusahaan')
        
        try:
            user = User.objects.create_user(
                username=email,  
                email=email,
                password=password
            )
            
            with connection.cursor() as cursor:
                cursor.execute(
                    'INSERT INTO petclinic."user" (email, password, alamat, nomor_telepon) VALUES (%s, %s, %s, %s)',
                    [email, user.password, alamat, nomor_telepon]
                )
                
                no_identitas = uuid.uuid4()
                
                cursor.execute(
                    'INSERT INTO petclinic.klien (no_identitas, tanggal_registrasi, email) VALUES (%s, NOW(), %s)',
                    [no_identitas, email]
                )
                
                cursor.execute(
                    'INSERT INTO petclinic.perusahaan (no_identitas_klien, nama_perusahaan) VALUES (%s, %s)',
                    [no_identitas, nama_perusahaan]
                )
            
            
            login(request, user)
            
            
            request.session['user_role'] = 'klien_perusahaan'
            request.session['no_identitas'] = str(no_identitas)
            
            return redirect('authentication:login')
        
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return render(request, self.template_name)
    
    def register_front_desk(self, request):
        
        email = request.POST.get('email')
        password = request.POST.get('password')
        nomor_telepon = request.POST.get('nomor_telepon')
        alamat = request.POST.get('alamat')
        tanggal_diterima = request.POST.get('tanggal_diterima')
        
        try:
            
            user = User.objects.create_user(
                username=email,  
                email=email,
                password=password
            )
            
            
            with connection.cursor() as cursor:
                cursor.execute(
                    'INSERT INTO petclinic."user" (email, password, alamat, nomor_telepon) VALUES (%s, %s, %s, %s)',
                    [email, user.password, alamat, nomor_telepon]
                )
                no_pegawai = uuid.uuid4()
                cursor.execute(
                    'INSERT INTO petclinic.pegawai (no_pegawai, tanggal_mulai_kerja, email_user) VALUES (%s, %s, %s)',
                    [no_pegawai, tanggal_diterima, email]
                )
                cursor.execute(
                    'INSERT INTO petclinic.front_desk (no_front_desk) VALUES (%s)',
                    [no_pegawai]
                )
            
            
            login(request, user)
            
            
            request.session['user_role'] = 'front_desk'
            request.session['no_pegawai'] = str(no_pegawai)
            
            return redirect('authentication:login')
        
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return render(request, self.template_name)
    
    def register_dokter_hewan(self, request):
        
        email = request.POST.get('email')
        password = request.POST.get('password')
        nomor_telepon = request.POST.get('nomor_telepon')
        alamat = request.POST.get('alamat')
        tanggal_diterima = request.POST.get('tanggal_diterima')
        no_izin_praktik = request.POST.get('no_izin_praktik')
        
        
        sertifikat_numbers = request.POST.getlist('sertifikat_no[]')
        sertifikat_names = request.POST.getlist('sertifikat_nama[]')
        
        
        jadwal_hari = request.POST.getlist('jadwal_hari[]')
        jadwal_jam = request.POST.getlist('jadwal_jam[]')
        
        try:
            
            user = User.objects.create_user(
                username=email,  
                email=email,
                password=password
            )
            
            with connection.cursor() as cursor:
                
                cursor.execute(
                    'INSERT INTO petclinic."user" (email, password, alamat, nomor_telepon) '
                    'VALUES (%s, %s, %s, %s)',
                    [email, user.password, alamat, nomor_telepon]
                )

                
                no_pegawai = uuid.uuid4()
                cursor.execute(
                    'INSERT INTO petclinic.pegawai '
                    '(no_pegawai, tanggal_mulai_kerja, email_user) '
                    'VALUES (%s, %s, %s)',
                    [no_pegawai, tanggal_diterima, email]
                )

                
                cursor.execute(
                    'INSERT INTO petclinic.tenaga_medis '
                    '(no_tenaga_medis, no_izin_praktik) '
                    'VALUES (%s, %s)',
                    [no_pegawai, no_izin_praktik]
                )

                
                cursor.execute(
                    'INSERT INTO petclinic.dokter_hewan (no_dokter_hewan) VALUES (%s)',
                    [no_pegawai]
                )

                
                for no_s, nama_s in zip(sertifikat_numbers, sertifikat_names):
                    if no_s and nama_s:
                        cursor.execute(
                            'INSERT INTO petclinic.sertifikat_kompetensi '
                            '(no_sertifikat_kompetensi, no_tenaga_medis, nama_sertifikat) '
                            'VALUES (%s, %s, %s)',
                            [no_s, no_pegawai, nama_s]
                        )

                
                for hari, jam in zip(jadwal_hari, jadwal_jam):
                    if hari and jam:
                        cursor.execute(
                            'INSERT INTO petclinic.jadwal_praktik '
                            '(no_dokter_hewan, hari, jam) '
                            'VALUES (%s, %s, %s)',
                            [no_pegawai, hari, jam]
                        )

            
            
            login(request, user)
            
            
            request.session['user_role'] = 'dokter_hewan'
            request.session['no_pegawai'] = str(no_pegawai)
            
            return redirect('authentication:login')
        
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return render(request, self.template_name)
    
    def register_perawat_hewan(self, request):
        
        email = request.POST.get('email')
        password = request.POST.get('password')
        nomor_telepon = request.POST.get('nomor_telepon')
        alamat = request.POST.get('alamat')
        tanggal_diterima = request.POST.get('tanggal_diterima')
        no_izin_praktik = request.POST.get('no_izin_praktik')
        
        
        sertifikat_numbers = request.POST.getlist('sertifikat_no[]')
        sertifikat_names = request.POST.getlist('sertifikat_nama[]')
        
        try:
            
            user = User.objects.create_user(
                username=email,  
                email=email,
                password=password
            )
            
            with connection.cursor() as cursor:
                
                cursor.execute(
                    'INSERT INTO petclinic."user" (email, password, alamat, nomor_telepon) '
                    'VALUES (%s, %s, %s, %s)',
                    [email, user.password, alamat, nomor_telepon]
                )

                
                no_pegawai = uuid.uuid4()
                cursor.execute(
                    'INSERT INTO petclinic.pegawai '
                    '(no_pegawai, tanggal_mulai_kerja, email_user) '
                    'VALUES (%s, %s, %s)',
                    [no_pegawai, tanggal_diterima, email]
                )

                
                cursor.execute(
                    'INSERT INTO petclinic.tenaga_medis '
                    '(no_tenaga_medis, no_izin_praktik) '
                    'VALUES (%s, %s)',
                    [no_pegawai, no_izin_praktik]
                )

                
                cursor.execute(
                    'INSERT INTO petclinic.perawat_hewan (no_perawat_hewan) VALUES (%s)',
                    [no_pegawai]
                )

                
                for no_s, nama_s in zip(sertifikat_numbers, sertifikat_names):
                    if no_s and nama_s:
                        cursor.execute(
                            'INSERT INTO petclinic.sertifikat_kompetensi '
                            '(no_sertifikat_kompetensi, no_tenaga_medis, nama_sertifikat) '
                            'VALUES (%s, %s, %s)',
                            [no_s, no_pegawai, nama_s]
                        )
                
            
            login(request, user)
            
            
            request.session['user_role'] = 'perawat_hewan'
            request.session['no_pegawai'] = str(no_pegawai)
            
            return redirect('authentication:login')
        
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return render(request, self.template_name)


def logout_view(request):
    
    if 'user_role' in request.session:
        del request.session['user_role']
    
    if 'no_identitas' in request.session:
        del request.session['no_identitas']
    
    if 'no_pegawai' in request.session:
        del request.session['no_pegawai']
    
    
    logout(request)
    return redirect('authentication:login')