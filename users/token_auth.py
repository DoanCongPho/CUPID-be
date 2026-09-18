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
            # "Bearer" is shared with Auth0. Raising here aborts the whole
            # DEFAULT_AUTHENTICATION_CLASSES chain, so Auth0JSONWebTokenAuthentication
            # would never get a chance. Return None to defer to the next class.
            # "Token" belongs to this app alone, so it still fails loudly.
            if scheme.lower() == "bearer":
                return None
            raise exceptions.AuthenticationFailed("Invalid or expired token.")
        user = tok_obj.user
        return (user, tok_obj)

    def authenticate_header(self, request):
        """
        Value for the WWW-Authenticate header.

        DRF only returns 401 Unauthorized when an authentication class defines
        this method; otherwise it returns 403 Forbidden even for requests with
        no credentials, which is the wrong HTTP semantic. With it:
          - not authenticated      -> 401 Unauthorized
          - authenticated, denied  -> 403 Forbidden
        """
        return self.keyword_tokens[0]
