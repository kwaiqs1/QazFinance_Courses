from django import forms
from django.contrib.auth import authenticate
from .models import User

def _apply_bootstrap(field):
    if hasattr(field.widget, "attrs"):
        classes = field.widget.attrs.get("class", "")
        field.widget.attrs["class"] = (classes + " form-control input-dark").strip()

class SignUpForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label="Пароль")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Повторите пароль")

    class Meta:
        model = User
        fields = ["email", "full_name", "nickname", "age", "school", "country", "city"]
        labels = {
            "email": "Email",
            "full_name": "ФИО",
            "nickname": "Никнейм",
            "age": "Возраст",
            "school": "Школа",
            "country": "Страна",
            "city": "Город",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, f in self.fields.items():
            _apply_bootstrap(f)

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Пароли не совпадают.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = (user.email or "").strip().lower()
        user.set_password(self.cleaned_data["password1"])

        # Верификации больше нет — считаем email подтверждённым
        if hasattr(user, "email_verified"):
            user.email_verified = True

        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, f in self.fields.items():
            _apply_bootstrap(f)

    def clean(self):
        cleaned = super().clean()
        email = (cleaned.get("email") or "").strip().lower()
        password = cleaned.get("password")
        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise forms.ValidationError("Неверный email или пароль.")
            cleaned["user"] = user
        return cleaned

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["full_name", "nickname", "age", "school", "country", "city"]
        labels = {
            "full_name": "ФИО",
            "nickname": "Никнейм",
            "age": "Возраст",
            "school": "Школа",
            "country": "Страна",
            "city": "Город",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, f in self.fields.items():
            _apply_bootstrap(f)
