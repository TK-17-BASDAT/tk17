# dashboard/forms.py
from django import forms
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm
from django.contrib.auth.models import User # Assuming you use Django's User

class CustomPasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        label="Old password",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'autofocus': True, 'class': 'mt-1 w-full border rounded-lg px-3 py-2'}),
    )
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'mt-1 w-full border rounded-lg px-3 py-2'}),
        strip=False,
        help_text="Your password can’t be too similar to your other personal information. "
                  "Your password must contain at least 8 characters. "
                  "Your password can’t be a commonly used password. "
                  "Your password can’t be entirely numeric.", # You can customize or use Django's validators
    )
    new_password2 = forms.CharField(
        label="New password confirmation",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'mt-1 w-full border rounded-lg px-3 py-2'}),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get("old_password")
        if not self.user.check_password(old_password):
            raise forms.ValidationError(
                "Your old password was entered incorrectly. Please enter it again."
            )
        return old_password

    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get("new_password1")
        new_password2 = self.cleaned_data.get("new_password2")
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("The two password fields didn’t match.")
        # You can add Django's password validators here if needed
        # from django.contrib.auth.password_validation import validate_password
        # try:
        #     validate_password(new_password2, self.user)
        # except forms.ValidationError as e:
        #     self.add_error('new_password2', e)
        return new_password2

    def save(self):
        new_password = self.cleaned_data["new_password1"]
        self.user.set_password(new_password)
        self.user.save() # This saves the new hashed password to Django's auth_user table

        # Now, update the password in your PETCLINIC."USER" table
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                # request.user.password will contain the NEWLY HASHED password
                # after user.set_password() and user.save()
                cursor.execute(
                    'UPDATE PETCLINIC.USER SET password = %s WHERE email = %s',
                    [self.user.password, self.user.email]
                )
            return self.user
        except Exception as e:
            # Handle potential database error during the update of PETCLINIC."USER"
            # This is a critical part; if this fails, passwords are out of sync.
            # You might want to log this error extensively.
            print(f"CRITICAL: Failed to update password in PETCLINIC.USER for {self.user.email}: {e}")
            # Depending on policy, you might re-raise or handle to inform admin
            raise

class SertifikatForm(forms.Form):
    no_sertifikat_kompetensi = forms.CharField(
        max_length=10, # Sesuaikan dengan skema DB
        widget=forms.TextInput(attrs={'class': 'w-full border px-2 py-1 rounded-md text-sm', 'placeholder': 'No. Sertifikat'})
    )
    nama_sertifikat = forms.CharField(
        max_length=100, # Sesuaikan dengan skema DB
        widget=forms.TextInput(attrs={'class': 'w-full border px-2 py-1 rounded-md text-sm', 'placeholder': 'Nama Sertifikat'})
    )
    # Tambahkan field tersembunyi untuk menandai apakah akan dihapus
    DELETE = forms.BooleanField(required=False, widget=forms.HiddenInput())
    # Tambahkan field untuk PK asli jika kita mengedit, agar tahu mana yang diupdate
    # Ini bisa menjadi 'id' dari entri tabel sertifikat jika ada.
    # Untuk skema Anda, no_sertifikat_kompetensi adalah PK, jadi ini mungkin sudah cukup.
    # Jika Anda ingin mengizinkan perubahan no_sertifikat_kompetensi, Anda perlu cara lain untuk identifikasi.
    # Kita asumsikan no_sertifikat_kompetensi bisa berubah, jadi kita perlu PK asli (jika ada) atau cara lain.
    # Untuk sementara, kita akan mengandalkan `no_sertifikat_kompetensi` yang ada saat load untuk identifikasi
    # dan jika diubah, akan dianggap sebagai entri baru dan yang lama dihapus jika DELETE dicentang.
    # Atau, lebih baik, PK tidak boleh diubah. Jika no_sertifikat diubah, itu berarti entri baru.

# Buat formset factory
from django.forms import formset_factory
SertifikatFormSet = formset_factory(SertifikatForm, extra=1, can_delete=True)
# extra=1 berarti selalu ada satu form kosong untuk entri baru.
# can_delete=True akan menambahkan checkbox untuk menandai form yang akan dihapus.

# (Nanti, buat JadwalForm dan JadwalFormSet dengan cara yang sama)
class JadwalPraktikForm(forms.Form):
    hari = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={'class': 'w-full border px-2 py-1 rounded-md text-sm', 'placeholder': 'Hari (e.g., Senin)'})
    )
    jam = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'w-full border px-2 py-1 rounded-md text-sm', 'placeholder': 'Jam (e.g., 09:00 - 12:00)'})
    )
    DELETE = forms.BooleanField(required=False, widget=forms.HiddenInput())
    # Untuk jadwal, PK adalah (no_dokter_hewan, hari, jam).
    # Jika hari atau jam diubah, itu entri baru, dan yang lama harus dihapus jika DELETE.
    # Kita perlu menyimpan hari dan jam asli untuk identifikasi update/delete.
    original_hari = forms.CharField(widget=forms.HiddenInput(), required=False)
    original_jam = forms.CharField(widget=forms.HiddenInput(), required=False)


JadwalPraktikFormSet = formset_factory(JadwalPraktikForm, extra=1, can_delete=True)