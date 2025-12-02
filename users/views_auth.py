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
        validated_data = serializer.validated_data
        
        # User model fields
        email = validated_data.get("email", "").strip()
        phone_number = validated_data.get("phone_number", "").strip()
        password = validated_data["password"]
        provider = validated_data.get("provider", "email")
        provider_id = validated_data.get("provider_id", "")
        
        # UserProfile model fields
        full_name = validated_data.get("full_name", "").strip()
        nickname = validated_data.get("nickname", "").strip()
        date_of_birth = validated_data.get("date_of_birth")
        teaser_description = validated_data.get("teaser_description", "").strip()
        profile_photo_url = validated_data.get("profile_photo_url", "").strip()
        verification_video_url = validated_data.get("verification_video_url", "").strip()
        home_latitude = validated_data.get("home_latitude")
        home_longitude = validated_data.get("home_longitude")

        # Generate username from email or phone_number
        if email:
            username = email.split("@")[0]
        else:
            username = phone_number.replace("+", "").replace("-", "").replace(" ", "")

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email or "",
            phone_number=phone_number or None,
            password=password,
            provider=provider,
            provider_id=provider_id
        )

        # Create or update profile with all provided information
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.full_name = full_name
        profile.nickname = nickname
        profile.date_of_birth = date_of_birth
        profile.teaser_description = teaser_description
        profile.profile_photo_url = profile_photo_url
        profile.verification_video_url = verification_video_url
        profile.home_latitude = home_latitude
        profile.home_longitude = home_longitude
        profile.save()

        # Generate token
        token_plain, token_obj = ExpiringToken.generate_token_for_user(user, days_valid=365, name="initial")

        resp = {
            "token": token_plain,
            "expires_at": token_obj.expires_at,
            "user": {
                "id": user.id,
                "email": user.email,
                "phone_number": user.phone_number,
                "full_name": profile.full_name,
                "nickname": profile.nickname,
                "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
                "profile_photo_url": profile.profile_photo_url,
                "verification_video_url": profile.verification_video_url,
                "home_latitude": profile.home_latitude,
                "home_longitude": profile.home_longitude,
            }
        }
        return Response(resp, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        profile, created = UserProfile.objects.get_or_create(user=user)

        token_plain, token_obj = ExpiringToken.generate_token_for_user(user, days_valid=365, name="login")

        resp = {
            "token": token_plain,
            "expires_at": token_obj.expires_at,
            "user": {
                "id": user.id,
                "email": user.email,
                "phone_number": user.phone_number,
                "provider": user.provider,
                "full_name": profile.full_name,
                "nickname": profile.nickname,
                "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
                "profile_photo_url": profile.profile_photo_url,
                "verification_video_url": profile.verification_video_url,
                "is_verified": profile.is_verified,
                "total_xp": profile.total_xp,
                "home_latitude": profile.home_latitude,
                "home_longitude": profile.home_longitude,
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
