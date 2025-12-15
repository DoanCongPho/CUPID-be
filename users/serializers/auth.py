"""
Authentication Serializers
Serializers for user registration, login, and token management
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers
from datetime import datetime

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    """
    Serializer for user registration.
    Accepts either email or phone_number + password.
    """
    # User model fields
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    provider = serializers.CharField(max_length=50, required=False, allow_blank=True, default="email")
    provider_id = serializers.CharField(max_length=255, required=False, allow_blank=True)

    # UserProfile model fields (optional)
    full_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    nickname = serializers.CharField(max_length=255, required=False, allow_blank=True)
    date_of_birth = serializers.CharField(required=False, allow_blank=True)
    teaser_description = serializers.CharField(max_length=255, required=False, allow_blank=True)
    profile_photo_url = serializers.URLField(required=False, allow_blank=True)
    verification_video_url = serializers.URLField(required=False, allow_blank=True)
    home_latitude = serializers.FloatField(required=False, allow_null=True)
    home_longitude = serializers.FloatField(required=False, allow_null=True)

    # Preferences
    preferences = serializers.ListField(child=serializers.IntegerField(), required=False)

    def validate(self, data):
        """Validate that either email or phone_number is provided"""
        email = data.get("email", "").strip()
        phone_number = data.get("phone_number", "").strip()

        if not email and not phone_number:
            raise serializers.ValidationError("Email hoặc phone_number là bắt buộc.")

        return data

    def validate_email(self, value):
        """Validate email uniqueness"""
        if value:
            value = value.strip()
            if User.objects.filter(email__iexact=value).exists():
                raise serializers.ValidationError("Email đã được sử dụng.")
        return value

    def validate_phone_number(self, value):
        """Validate phone number uniqueness"""
        if value:
            value = value.strip()
            if User.objects.filter(phone_number=value).exists():
                raise serializers.ValidationError("Số điện thoại đã được sử dụng.")
        return value

    def validate_date_of_birth(self, value):
        """
        Validate and parse date string.
        Accepts formats: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY
        """
        if not value:
            return None

        date_formats = [
            "%Y-%m-%d",      # 2000-01-15
            "%d/%m/%Y",      # 15/01/2000
            "%m/%d/%Y",      # 01/15/2000
            "%Y/%m/%d",      # 2000/01/15
            "%d-%m-%Y",      # 15-01-2000
        ]

        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(value, fmt).date()
                today = datetime.now().date()
                age = today.year - parsed_date.year - ((today.month, today.day) < (parsed_date.month, parsed_date.day))

                if age < 13:
                    raise serializers.ValidationError("Bạn phải ít nhất 13 tuổi để đăng ký.")
                if parsed_date > today:
                    raise serializers.ValidationError("Ngày sinh không thể là ngày trong tương lai.")

                return parsed_date
            except ValueError:
                continue

        raise serializers.ValidationError(
            "Định dạng ngày không hợp lệ. Vui lòng sử dụng: YYYY-MM-DD, DD/MM/YYYY, hoặc MM/DD/YYYY"
        )

    def validate_profile_photo_url(self, value):
        """Validate profile picture URL"""
        if not value:
            return ""
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("Profile picture must be a valid HTTP/HTTPS URL")
        return value

    def validate_verification_video_url(self, value):
        """Validate verification video URL"""
        if not value:
            return ""
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("Verification video must be a valid HTTP/HTTPS URL")
        return value


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Accepts either email or phone_number + password.
    """
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Validate credentials and authenticate user"""
        email = data.get("email", "").strip()
        phone_number = data.get("phone_number", "").strip()
        password = data.get("password")

        if not email and not phone_number:
            raise serializers.ValidationError("Email hoặc phone_number là bắt buộc.")

        user = None

        # Try email authentication
        if email:
            try:
                user = User.objects.get(email__iexact=email)
                if not user.check_password(password):
                    raise serializers.ValidationError("Email hoặc mật khẩu không đúng.")
            except User.DoesNotExist:
                pass

        # Try phone number authentication
        if not user and phone_number:
            try:
                user = User.objects.get(phone_number=phone_number)
                if not user.check_password(password):
                    raise serializers.ValidationError("Số điện thoại hoặc mật khẩu không đúng.")
            except User.DoesNotExist:
                pass

        if not user:
            raise serializers.ValidationError("Email/Số điện thoại hoặc mật khẩu không đúng.")

        if not user.is_active:
            raise serializers.ValidationError("Tài khoản đã bị vô hiệu hóa.")

        data["user"] = user
        return data


class TokenResponseSerializer(serializers.Serializer):
    """Serializer for token response"""
    token = serializers.CharField()
    expires_at = serializers.DateTimeField()
