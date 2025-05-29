# datavaksin/forms.py
from django import forms
from manajemen_vaksin.models import Vaksin

class VaksinForm(forms.ModelForm):
    class Meta:
        model = Vaksin
        fields = ['kode', 'nama', 'harga', 'stok'] # 'kode' akan jadi PK dan mungkin perlu penanganan khusus jika auto-generate
        widgets = {
            'kode': forms.TextInput(attrs={'class': 'w-full border rounded p-2', 'placeholder': 'e.g., VAC001'}),
            'nama': forms.TextInput(attrs={'class': 'w-full border rounded p-2', 'placeholder': 'Nama Vaksin'}),
            'harga': forms.NumberInput(attrs={'class': 'w-full border rounded p-2', 'placeholder': 'Harga (Rp)'}),
            'stok': forms.NumberInput(attrs={'class': 'w-full border rounded p-2', 'placeholder': 'Stok Awal'}),
        }
        labels = {
            'kode': 'ID Vaksin',
            'nama': 'Nama Vaksin',
            'harga': 'Harga (Rp)',
            'stok': 'Stok Awal',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Jika 'kode' adalah PK, mungkin kita ingin membuatnya readonly saat update
        if self.instance and self.instance.pk:
            self.fields['kode'].widget.attrs['readonly'] = True
            self.fields['kode'].required = False # Tidak wajib diisi lagi saat update
            # Saat update, stok tidak diubah di form ini, tapi di form terpisah
            # jadi kita bisa remove atau disable. Untuk Update Info (bukan stok):
            if 'stok' in self.fields: # Jika stok masih ada di fields
                 self.fields['stok'].widget.attrs['readonly'] = True
                 self.fields['stok'].widget.attrs['class'] += ' bg-gray-100' # Styling disabled
                 self.fields['stok'].help_text = "Stok diupdate melalui 'Stock Update'."


class VaksinInfoUpdateForm(forms.ModelForm):
    """Form untuk mengupdate nama dan harga saja."""
    class Meta:
        model = Vaksin
        fields = ['nama', 'harga']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'w-full border rounded p-2'}),
            'harga': forms.NumberInput(attrs={'class': 'w-full border rounded p-2'}),
        }
        labels = {
            'nama': 'Nama Vaksin',
            'harga': 'Harga (Rp)',
        }

class VaksinStockUpdateForm(forms.ModelForm):
    """Form khusus untuk mengupdate stok."""
    class Meta:
        model = Vaksin
        fields = ['stok']
        widgets = {
            'stok': forms.NumberInput(attrs={'class': 'w-full border rounded p-2'}),
        }
        labels = {
            'stok': 'Stok Baru',
        }