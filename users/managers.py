"""
Custom manager cho User model.
"""
import re

from django.contrib.auth.models import UserManager as DjangoUserManager


class UserManager(DjangoUserManager):
    """
    Manager cho User model dùng email làm USERNAME_FIELD.

    User khai ``USERNAME_FIELD = "email"`` nhưng vẫn kế thừa field ``username``
    (unique=True, NOT NULL) từ AbstractUser. Manager mặc định của Django lại bắt
    buộc truyền ``username`` ở tham số đầu tiên, nên hai thứ vênh nhau.

    Manager này lấp khoảng trống đó: cho phép gọi
    ``User.objects.create_user(email=..., password=...)`` mà không cần username,
    username sẽ được sinh tự động từ email hoặc số điện thoại và đảm bảo không trùng.
    """

    def _base_username(self, email=None, phone_number=None):
        """Lấy phần gốc của username từ email hoặc số điện thoại."""
        if email:
            base = email.split("@")[0]
        elif phone_number:
            base = phone_number
        else:
            base = "user"

        # username của AbstractUser chỉ cho phép: chữ, số và @ . + - _
        base = re.sub(r"[^\w.@+-]", "", base).strip("._-")
        return base[:140] or "user"

    def generate_username(self, email=None, phone_number=None):
        """Sinh username duy nhất, thêm hậu tố số nếu bị trùng."""
        base = self._base_username(email, phone_number)
        candidate = base
        suffix = 1
        while self.model._default_manager.filter(username=candidate).exists():
            suffix += 1
            candidate = f"{base}{suffix}"[:150]
        return candidate

    def create_user(self, username=None, email=None, password=None, **extra_fields):
        if not username:
            username = self.generate_username(email, extra_fields.get("phone_number"))
        return super().create_user(
            username=username, email=email, password=password, **extra_fields
        )

    def create_superuser(self, username=None, email=None, password=None, **extra_fields):
        if not username:
            username = self.generate_username(email, extra_fields.get("phone_number"))
        return super().create_superuser(
            username=username, email=email, password=password, **extra_fields
        )
