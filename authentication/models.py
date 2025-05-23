from django.db import models
import uuid

class User(models.Model):
    email = models.CharField(max_length=50, primary_key=True)
    password = models.CharField(max_length=100)
    alamat = models.TextField()
    nomor_telepon = models.CharField(max_length=15)

    def __str__(self):
        return self.email

    class Meta:
        db_table = 'user' 

class Pegawai(models.Model):
    no_pegawai = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tanggal_mulai_kerja = models.DateField()
    tanggal_akhir_kerja = models.DateField(null=True, blank=True)
    email_user = models.OneToOneField(User, on_delete=models.CASCADE, db_column='email_user')

    def __str__(self):
        return f"Pegawai: {self.email_user.email} ({self.no_pegawai})"

    class Meta:
        db_table = 'pegawai'

class FrontDesk(models.Model):
    no_front_desk = models.OneToOneField(Pegawai, on_delete=models.CASCADE, primary_key=True, db_column='no_front_desk')

    def __str__(self):
        return f"Front Desk: {self.no_front_desk.email_user.email}"

    class Meta:
        db_table = 'front_desk'

class TenagaMedis(models.Model):
    no_tenaga_medis = models.OneToOneField(Pegawai, on_delete=models.CASCADE, primary_key=True, db_column='no_tenaga_medis')
    no_izin_praktik = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"Tenaga Medis: {self.no_tenaga_medis.email_user.email} (Izin: {self.no_izin_praktik})"

    class Meta:
        db_table = 'tenaga_medis'

class PerawatHewan(models.Model):
    no_perawat_hewan = models.OneToOneField(TenagaMedis, on_delete=models.CASCADE, primary_key=True, db_column='no_perawat_hewan')

    def __str__(self):
        return f"Perawat: {self.no_perawat_hewan.no_tenaga_medis.email_user.email}"

    class Meta:
        db_table = 'perawat_hewan'

class DokterHewan(models.Model):
    no_dokter_hewan = models.OneToOneField(TenagaMedis, on_delete=models.CASCADE, primary_key=True, db_column='no_dokter_hewan')

    def __str__(self):
        return f"Dokter: {self.no_dokter_hewan.no_tenaga_medis.email_user.email}"

    class Meta:
        db_table = 'dokter_hewan'

class SertifikatKompetensi(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    no_sertifikat_kompetensi = models.CharField(max_length=10)
    no_tenaga_medis = models.ForeignKey(TenagaMedis, on_delete=models.CASCADE, db_column='no_tenaga_medis')
    nama_sertifikat = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nama_sertifikat} ({self.no_sertifikat_kompetensi}) untuk {self.no_tenaga_medis}"

    class Meta:
        db_table = 'sertifikat_kompetensi'
        unique_together = (('no_sertifikat_kompetensi', 'no_tenaga_medis'),)

class JadwalPraktik(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    no_dokter_hewan = models.ForeignKey(DokterHewan, on_delete=models.CASCADE, db_column='no_dokter_hewan')
    HARI_CHOICES = [
        ('Senin', 'Senin'), ('Selasa', 'Selasa'), ('Rabu', 'Rabu'),
        ('Kamis', 'Kamis'), ('Jumat', 'Jumat'), ('Sabtu', 'Sabtu'),
        ('Minggu', 'Minggu'),
    ]
    hari = models.CharField(max_length=10, choices=HARI_CHOICES)
    jam = models.CharField(max_length=20)

    def __str__(self):
        return f"Jadwal {self.no_dokter_hewan} - {self.hari} {self.jam}"

    class Meta:
        db_table = 'jadwak_praktik'
        unique_together = (('no_dokter_hewan', 'hari', 'jam'),)

