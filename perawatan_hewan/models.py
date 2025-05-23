# perawatan_hewan/models.py
import uuid
from django.db import models

class Obat(models.Model):
    kode = models.CharField(max_length=10, primary_key=True)
    nama = models.CharField(max_length=100)
    harga = models.IntegerField()
    stok = models.IntegerField()
    dosis = models.TextField()

    def __str__(self):
        return f"{self.kode} - {self.nama}"

    class Meta:
        db_table = 'obat'

class Perawatan(models.Model):
    kode_perawatan = models.CharField(max_length=10, primary_key=True)
    nama_perawatan = models.CharField(max_length=100)
    biaya_perawatan = models.IntegerField()
    obat_terkait = models.ManyToManyField(Obat, through='PerawatanObat', related_name='perawatan_menggunakan')

    def __str__(self):
        return f"{self.kode_perawatan} - {self.nama_perawatan}"

    class Meta:
        db_table = 'perawatan'

class PerawatanObat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kode_perawatan = models.ForeignKey(Perawatan, on_delete=models.CASCADE, db_column='kode_perawatan')
    kode_obat = models.ForeignKey(Obat, on_delete=models.CASCADE, db_column='kode_obat')
    kuantitas_obat = models.IntegerField()

    def __str__(self):
        return f"{self.kode_perawatan.nama_perawatan} menggunakan {self.kode_obat.nama} (Qty: {self.kuantitas_obat})"

    class Meta:
        db_table = 'perawatan_obat'
        unique_together = (('kode_perawatan', 'kode_obat'),)