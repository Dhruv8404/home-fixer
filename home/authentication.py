from rest_framework_simplejwt.authentication import JWTAuthentication

class CsrfExemptJWTAuthentication(JWTAuthentication):
    def enforce_csrf(self, request):
        return