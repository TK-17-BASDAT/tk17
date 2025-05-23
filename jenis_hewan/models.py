
import uuid
from django.db import models

class JenisHewan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nama_jenis = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nama_jenis

    class Meta:
        db_table = 'jenis_hewan'