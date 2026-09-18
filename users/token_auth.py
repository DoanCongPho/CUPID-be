from rest_framework import authentication, exceptions

from .models import ExpiringToken

class ExpiringTokenAuthentication(authentication.BaseAuthentication):
    """
    Authentication accepting:
    - Authorization: Token <token>
    - Authorization: Bearer <token>
    Returns (user, token_obj) on success.
    """
    keyword_tokens = ("Token", "Bearer")

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).split()
        if not header:
            return None

        if len(header) == 1:
            raise exceptions.AuthenticationFailed("Invalid token header. No credentials provided.")
        if len(header) > 2:
            raise exceptions.AuthenticationFailed("Invalid token header. Token string should not contain spaces.")

        scheme = header[0].decode()
        token = header[1].decode()

        if scheme not in self.keyword_tokens:
            return None

        tok_obj = ExpiringToken.verify_token(token)
        if not tok_obj:
            # Scheme "Bearer" dùng chung với Auth0. Nếu raise ở đây thì cả chuỗi
            # DEFAULT_AUTHENTICATION_CLASSES dừng lại và Auth0JSONWebTokenAuthentication
            # không bao giờ được thử. Trả None để nhường cho class kế tiếp.
            # Scheme "Token" là của riêng app nên vẫn báo lỗi thẳng.
            if scheme.lower() == "bearer":
                return None
            raise exceptions.AuthenticationFailed("Invalid or expired token.")
        user = tok_obj.user
        return (user, tok_obj)

    def authenticate_header(self, request):
        """
        Giá trị cho header WWW-Authenticate.

        DRF chỉ trả 401 Unauthorized khi authentication class có khai hàm này;
        nếu không nó trả 403 Forbidden cho cả request thiếu credentials — sai
        ngữ nghĩa HTTP. Có hàm này thì:
          - chưa đăng nhập        -> 401 Unauthorized
          - đăng nhập nhưng cấm   -> 403 Forbidden
        """
        return self.keyword_tokens[0]
