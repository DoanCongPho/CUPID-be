from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .serializers_auth import RegisterSerializer, LoginSerializer
from .models import UserProfile, ExpiringToken

User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extract validated data
        name = serializer.validated_data["name"]
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        date_of_birth = serializer.validated_data["dateofBirth"]
        profile_photo_url = serializer.validated_data.get("profile_photo_url", "")


        # Parse name into first_name and last_name
        name_parts = name.strip().split(maxsplit=1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        # Generate username from email
        username = email.split("@")[0]

        # Create user with name
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Update profile with additional fields
        # Profile is auto-created via signals, but we need to update it
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.full_name = name
        profile.date_of_birth = date_of_birth
        profile.profile_photo_url = profile_photo_url
        profile.save(update_fields=["full_name", "date_of_birth", "profile_photo_url", "updated_at"])

        # Generate token
        token_plain, token_obj = ExpiringToken.generate_token_for_user(user, days_valid=365, name="initial")

        resp = {
            "token": token_plain,
            "expires_at": token_obj.expires_at,
            "user": {
                "id": user.id,
                "name": profile.full_name,
                "email": user.email,
                "dateofBirth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
                "profile_photo_url": profile.profile_photo_url
            }
        }
        return Response(resp, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        user = None
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response({"detail": "Email hoặc mật khẩu không đúng."}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({"detail": "Email hoặc mật khẩu không đúng."}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            return Response({"detail": "Tài khoản bị khóa."}, status=status.HTTP_400_BAD_REQUEST)
        
        profile, created = UserProfile.objects.get_or_create(user=user)

        token_plain, token_obj = ExpiringToken.generate_token_for_user(user, days_valid=365, name="login")

        resp = {
            "token": token_plain,
            "expires_at": token_obj.expires_at,
            "user": {
                "id": user.id,
                "name": profile.full_name or user.get_full_name(),
                "email": user.email,
                "dateofBirth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
                "profile_photo_url": profile.profile_photo_url
            }
        }
        return Response(resp, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        auth = request.auth
        if hasattr(auth, "revoke"):
            auth.revoke()
            return Response({"detail": "Token revoked"}, status=status.HTTP_200_OK)

        header = request.META.get("HTTP_AUTHORIZATION", "")
        parts = header.split()
        if len(parts) == 2:
            token_plain = parts[1]
            tok = ExpiringToken.verify_token(token_plain)
            if tok:
                tok.revoke()
                return Response({"detail": "Token revoked"}, status=status.HTTP_200_OK)
        return Response({"detail": "No token found"}, status=status.HTTP_400_BAD_REQUEST)


class TokenListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tokens = request.user.auth_tokens.all().values("id", "name", "created_at", "expires_at", "revoked")
        return Response(list(tokens))
