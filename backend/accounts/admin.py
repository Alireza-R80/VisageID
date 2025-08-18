from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, FaceEmbedding

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        (None, {"fields": ("email", "password", "display_name", "avatar_url")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )
    add_fieldsets = (
        (None, {"fields": ("email", "password1", "password2")}),
    )
    list_display = ("email", "display_name", "is_active")
    search_fields = ("email", "display_name")
    ordering = ("email",)

admin.site.register(FaceEmbedding)
