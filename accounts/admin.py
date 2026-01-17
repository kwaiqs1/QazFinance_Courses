from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "full_name", "nickname", "email_verified", "rating", "is_staff")
    search_fields = ("email", "full_name", "nickname")

    fieldsets = (
        ("Account", {"fields": ("email", "password")}),
        ("Profile", {"fields": ("full_name", "nickname", "age", "school", "country", "city", "rating")}),
        ("Verification", {"fields": ("email_verified",)}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "nickname", "password1", "password2", "is_staff", "is_superuser"),
        }),
    )

    # Needed because we are not using AbstractUser
    filter_horizontal = ("groups", "user_permissions")
    readonly_fields = ("date_joined",)
