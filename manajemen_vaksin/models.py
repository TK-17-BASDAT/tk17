from django.db import models

class Vaksin(models.Model):
    kode = models.CharField(max_length=6, primary_key=True)
    nama = models.CharField(max_length=50)
    harga = models.IntegerField()
    stok = models.IntegerField()

    class Meta:
        db_table = 'vaksin'  

    def __str__(self):
        return f"{self.nama} ({self.kode})"
