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