import secrets
import hashlib
from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Lưu trữ thông tin cốt lõi dùng cho việc xác thực (đăng nhập/đăng ký).
    Đây là bảng trung tâm của hệ thống.
    """
    email = models.EmailField(_("email address"), unique=True)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    provider = models.CharField(max_length=50, blank=True, default="")  # e.g., "google", "facebook", "email"
    provider_id = models.CharField(max_length=255, blank=True, default="")  # e.g., Auth0 sub
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email if self.email else self.username

class UserProfile(models.Model):
    """
    Lưu trữ tất cả thông tin công khai và mô tả về người dùng.
    Được tách biệt khỏi bảng User để tăng cường bảo mật.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="profile", on_delete=models.CASCADE, primary_key=True)
    full_name = models.CharField(max_length=255, blank=True)  # Tên thật
    date_of_birth = models.DateField(null=True, blank=True)
    nickname = models.CharField(max_length=255, blank=True)  # Tên hiển thị chính
    teaser_description = models.CharField(max_length=255, blank=True)  # Mô tả gián tiếp
    profile_photo_url = models.URLField(blank=True)
    verification_video_url = models.URLField(blank=True)
    is_verified = models.BooleanField(default=False)
    total_xp = models.IntegerField(default=0)  # Điểm kinh nghiệm
    home_latitude = models.FloatField(null=True, blank=True)  # Vị trí cố định
    home_longitude = models.FloatField(null=True, blank=True)
    external_id = models.CharField(max_length=255, blank=True, db_index=True)
    is_service_account = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("user profile")
        verbose_name_plural = _("user profiles")
        indexes = [
            models.Index(fields=["external_id"]),
        ]

    def __str__(self):
        return f"Profile of {self.user.username}"

class ExpiringToken(models.Model):
    """
    Lưu hash của token (không lưu token plaintext), hạn dùng (expires_at),
    và flag revoked để có thể thu hồi.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="auth_tokens")
    key_hash = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=100, blank=True, default="")  # optional label
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    revoked = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Token for {self.user_id} (revoked={self.revoked})"

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def generate_token_for_user(cls, user, days_valid: int = 365, name: str = ""):
        """
        Tạo token plaintext và lưu hash vào DB. Trả về (plaintext_token, token_obj).
        - Bạn phải trả plaintext_token cho client **một lần** (sau đó server chỉ lưu hash).
        """
        # token entropy: 48 bytes => ~64+ chars (URL-safe)
        plaintext = secrets.token_urlsafe(48)
        key_hash = cls._hash_token(plaintext)
        expires = timezone.now() + timedelta(days=days_valid)
        obj = cls.objects.create(user=user, key_hash=key_hash, expires_at=expires, name=name)
        return plaintext, obj

    @classmethod
    def verify_token(cls, token_plaintext: str):
        """
        Trả token object nếu hợp lệ & chưa hết hạn & chưa bị revoked, else None.
        """
        key_hash = cls._hash_token(token_plaintext)
        now = timezone.now()
        try:
            tok = cls.objects.get(key_hash=key_hash, revoked=False)
        except cls.DoesNotExist:
            return None
        if tok.expires_at < now:
            return None
        return tok

    def revoke(self):
        self.revoked = True
        self.save(update_fields=["revoked"])

class Task(models.Model):
    """
    Lưu trữ các công việc (to-do) thô do người dùng nhập vào.
    Đóng vai trò là dữ liệu đầu vào cho model AI.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="tasks", on_delete=models.CASCADE)
    description = models.TextField()  # Nội dung công việc
    scheduled_start_time = models.DateTimeField(null=True, blank=True)
    scheduled_end_time = models.DateTimeField(null=True, blank=True)
    is_transformed_to_quest = models.BooleanField(default=False)  # Đã được xử lý hay chưa
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Task: {self.description[:50]}"
