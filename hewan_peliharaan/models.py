# hewan_peliharaan/models.py
import uuid
from django.db import models

class Hewan(models.Model):
    id_hewan = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column='id_hewan_internal')
    nama = models.CharField(max_length=50)
    # String reference ke model Klien di aplikasi 'dataklien'
    no_identitas_klien = models.ForeignKey('dataklien.Klien', on_delete=models.CASCADE, db_column='no_identitas_klien')
    tanggal_lahir = models.DateField()
    # String reference ke model JenisHewan di aplikasi 'jenis_hewan'
    id_jenis = models.ForeignKey('jenis_hewan.JenisHewan', on_delete=models.PROTECT, db_column='id_jenis')
    url_foto = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nama} (Jenis: {self.id_jenis.nama_jenis}, Pemilik: {self.no_identitas_klien.email.email})"

    class Meta:
        db_table = 'hewan'
        unique_together = (('nama', 'no_identitas_klien'),)