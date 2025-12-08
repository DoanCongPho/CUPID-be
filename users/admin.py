from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile, Task, UserModeSettings

@admin.register(User)
class UserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        (_('Provider info'), {'fields': ('provider', 'provider_id')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "nickname", "is_verified", "total_xp", "created_at")
    search_fields = ("user__username", "user__email", "full_name", "nickname")
    ordering = ("user",)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("user", "description", "is_transformed_to_quest", "created_at")
    search_fields = ("user__username", "description")
    ordering = ("-created_at",)


@admin.register(UserModeSettings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "ghost_mode_enabled",
        "daily_reminders_enabled",
        "location_sharing_enabled",
        "spotmatch_notifications_enabled",
    )
    search_fields = ("user__username", "user__email")
    list_filter = (
        "ghost_mode_enabled",
        "daily_reminders_enabled",
        "location_sharing_enabled",
        "spotmatch_notifications_enabled",
    )
    ordering = ("user",)
