from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # First check for temporary token
        temp_token = request.COOKIES.get('temp_token')
        if temp_token:
            try:
                validated_token = self.get_validated_token(temp_token)
                return self.get_user(validated_token), validated_token
            except:
                pass

        # Then check for regular token
        raw_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except (InvalidToken, TokenError) as e:
            return None

    def authenticate_header(self, request):
        return 'Bearer' 