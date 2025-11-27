from django.contrib.auth import get_user_model
from rest_framework import serializers
from datetime import datetime

User = get_user_model()

class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    dateofBirth = serializers.CharField()  # Accept as string, will parse to date
    avatar_url = serializers.URLField(allow_blank=True, required=False)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email đã được sử dụng.")
        return value

    def validate_dateofBirth(self, value):
        """
        Validate and parse date string. Accepts formats like:
        - "YYYY-MM-DD" (2000-01-15)
        - "DD/MM/YYYY" (15/01/2000)
        - "MM/DD/YYYY" (01/15/2000)
        """
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
                # Validate age (optional - must be at least 13 years old)
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

    def validate_avatar_url(self, value):
        """
        Validate profile picture URL
        """
        if not value:
            return ""
        
        # URLField already validates it's a proper URL
        # Just ensure it's http/https
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("Profile picture must be a valid HTTP/HTTPS URL")
        
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        from django.contrib.auth import authenticate
        user = authenticate(email=data.get("email"), password=data.get("password"))
        if user is None:
            raise serializers.ValidationError("Email hoặc mật khẩu không đúng.")
        if not user.is_active:
            raise serializers.ValidationError("Tài khoản đã bị vô hiệu hóa.")
        data["user"] = user
        return data


class TokenResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    expires_at = serializers.DateTimeField()