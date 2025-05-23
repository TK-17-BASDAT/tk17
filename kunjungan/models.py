# kunjungan/models.py
import uuid
from django.db import models
from django.utils import timezone # Untuk default timestamp_awal

class Kunjungan(models.Model):
    id_kunjungan = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column='id_kunjungan')
    # String reference ke model-model di aplikasi lain
    hewan = models.ForeignKey('hewan_peliharaan.Hewan', on_delete=models.PROTECT, db_column='nama_hewan')
    no_front_desk = models.ForeignKey('authentication.FrontDesk', on_delete=models.PROTECT, db_column='no_front_desk')
    no_perawat_hewan = models.ForeignKey('authentication.PerawatHewan', on_delete=models.PROTECT, db_column='no_perawat_hewan')
    no_dokter_hewan = models.ForeignKey('authentication.DokterHewan', on_delete=models.PROTECT, db_column='no_dokter_hewan')
    kode_vaksin = models.ForeignKey('manajemen_vaksin.Vaksin', on_delete=models.SET_NULL, null=True, blank=True, db_column='kode_vaksin')

    TIPE_KUNJUNGAN_CHOICES = [
        ('REGULER', 'Reguler'),
        ('VAKSINASI', 'Vaksinasi'),
        ('DARURAT', 'Darurat'),
        ('KONTROL', 'Kontrol'),
    ]
    tipe_kunjungan = models.CharField(max_length=10, choices=TIPE_KUNJUNGAN_CHOICES)
    timestamp_awal = models.DateTimeField(default=timezone.now) # Default ke waktu sekarang
    timestamp_akhir = models.DateTimeField(null=True, blank=True)
    suhu = models.IntegerField(null=True, blank=True)
    berat_badan = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Kunjungan {self.id_kunjungan} - {self.hewan.nama} ({self.timestamp_awal.strftime('%d-%m-%Y %H:%M')})"

    class Meta:
        db_table = 'kunjungan'

class KunjunganKeperawatan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kunjungan = models.ForeignKey(Kunjungan, on_delete=models.CASCADE)
    # String reference ke model Perawatan di aplikasi 'perawatan_hewan'
    kode_perawatan = models.ForeignKey('perawatan_hewan.Perawatan', on_delete=models.PROTECT, db_column='kode_perawatan')
    catatan = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Detail Perawatan untuk Kunjungan {self.kunjungan.id_kunjungan} - Perawatan: {self.kode_perawatan.nama_perawatan}"

    class Meta:
        db_table = 'kunjungan_keperawatan'
        unique_together = (('kunjungan', 'kode_perawatan'),)