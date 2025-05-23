import uuid
from django.db import models

class Klien(models.Model):
    no_identitas = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tanggal_registrasi = models.DateField()
    # Menggunakan string reference ke model User di aplikasi 'authentication'
    email = models.ForeignKey('authentication.User', on_delete=models.CASCADE, db_column='email')

    def __str__(self):
        return f"Klien: {self.email.email} ({self.no_identitas})"

    class Meta:
        db_table = 'klien'

class Individu(models.Model):
    no_identitas_klien = models.OneToOneField(Klien, on_delete=models.CASCADE, primary_key=True, db_column='no_identitas_klien')
    nama_depan = models.CharField(max_length=50)
    nama_tengah = models.CharField(max_length=50, null=True, blank=True)
    nama_belakang = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.nama_depan} {self.nama_belakang or ''}".strip()

    class Meta:
        db_table = 'individu'

class Perusahaan(models.Model):
    no_identitas_klien = models.OneToOneField(Klien, on_delete=models.CASCADE, primary_key=True, db_column='no_identitas_klien')
    nama_perusahaan = models.CharField(max_length=100)

    def __str__(self):
        return self.nama_perusahaan

    class Meta:
        db_table = 'perusahaan'