import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Ensure a Django superuser exists using env vars (Railway-friendly)."

    def handle(self, *args, **options):
        enabled = os.getenv("CREATE_SUPERUSER", "").lower() in ("1", "true", "yes", "y")
        if not enabled:
            self.stdout.write(self.style.WARNING("CREATE_SUPERUSER is not enabled. Skipping."))
            return

        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "").strip()
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "").strip()
        if not email or not password:
            self.stdout.write(self.style.WARNING("Missing DJANGO_SUPERUSER_EMAIL or DJANGO_SUPERUSER_PASSWORD. Skipping."))
            return

        nickname = os.getenv("DJANGO_SUPERUSER_NICKNAME", "admin").strip() or "admin"
        full_name = os.getenv("DJANGO_SUPERUSER_FULL_NAME", "Admin").strip() or "Admin"

        # опциональные поля (если у твоей модели они есть)
        age_raw = os.getenv("DJANGO_SUPERUSER_AGE", "").strip()
        try:
            age = int(age_raw) if age_raw else None
        except ValueError:
            age = None

        school = os.getenv("DJANGO_SUPERUSER_SCHOOL", "").strip()
        country = os.getenv("DJANGO_SUPERUSER_COUNTRY", "").strip()
        city = os.getenv("DJANGO_SUPERUSER_CITY", "").strip()

        update_password = os.getenv("DJANGO_SUPERUSER_UPDATE_PASSWORD", "false").lower() in ("1", "true", "yes", "y")

        User = get_user_model()

        # Готовим extra_fields только для тех полей, которые реально есть в модели
        extra_fields = {}

        def set_if_field_exists(field_name: str, value):
            if value is None:
                return
            try:
                User._meta.get_field(field_name)
                extra_fields[field_name] = value
            except Exception:
                pass

        set_if_field_exists("email", email)           # на случай если USERNAME_FIELD не email
        set_if_field_exists("nickname", nickname)
        set_if_field_exists("full_name", full_name)
        set_if_field_exists("age", age)
        set_if_field_exists("school", school)
        set_if_field_exists("country", country)
        set_if_field_exists("city", city)

        username_field = getattr(User, "USERNAME_FIELD", "email")

        # Куда класть "логин" — зависит от USERNAME_FIELD
        create_kwargs = dict(extra_fields)
        if username_field in create_kwargs:
            pass
        else:
            # если USERNAME_FIELD = email -> логинимся email
            if username_field == "email":
                create_kwargs["email"] = email
            else:
                # если вдруг USERNAME_FIELD = nickname/username
                create_kwargs[username_field] = nickname

        with transaction.atomic():
            # ищем пользователя по email (если поле есть)
            existing = None
            try:
                User._meta.get_field("email")
                existing = User.objects.filter(email__iexact=email).first()
            except Exception:
                # если у модели нет email (маловероятно), ищем по USERNAME_FIELD
                existing = User.objects.filter(**{f"{username_field}__iexact": create_kwargs.get(username_field, "")}).first()

            if existing:
                changed = False

                if not getattr(existing, "is_staff", False):
                    existing.is_staff = True
                    changed = True

                if not getattr(existing, "is_superuser", False):
                    existing.is_superuser = True
                    changed = True

                # заполняем пустые важные поля (если есть)
                for k, v in extra_fields.items():
                    if hasattr(existing, k):
                        cur = getattr(existing, k)
                        if cur in (None, "", 0) and v not in (None, ""):
                            setattr(existing, k, v)
                            changed = True

                if update_password:
                    existing.set_password(password)
                    changed = True

                if changed:
                    existing.save()
                    self.stdout.write(self.style.SUCCESS("Superuser exists: updated flags/fields (and password if enabled)."))
                else:
                    self.stdout.write(self.style.SUCCESS("Superuser exists: no changes."))
                return

            # если не существует — создаём
            try:
                user = User.objects.create_superuser(password=password, **create_kwargs)
            except TypeError:
                # fallback: create_user + руками выставим флаги
                user = User.objects.create_user(password=password, **create_kwargs)
                user.is_staff = True
                user.is_superuser = True
                user.save()

            self.stdout.write(self.style.SUCCESS(f"Superuser created: {email}"))

