from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import User, CustomerProfile, ServicemanProfile, VendorProfile, EmailOTP
from .serializers import (
    SendOTPSerializer,
    VerifyOTPSerializer,
    CompleteRegisterSerializer,
    UserProfileSerializer,
    LogoutSerializer,
    VendorProfileSerializer,
    ServicemanProfileSerializer,
    CustomerProfileSerializer,
    ProfileResponseSerializer,
    UniversalProfileUpdateSerializer,
)
from .utils import send_email_otp, verify_email_otp
from rest_framework import status

def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }

from .serializers import EmailPasswordLoginSerializer
from django.contrib.auth import authenticate

class EmailPasswordLoginAPI(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # No authentication required for email/password login

    @swagger_auto_schema(
        operation_summary="Login with Email & Password",
        request_body=EmailPasswordLoginSerializer,
        tags=["Auth"]
    )
    def post(self, request):
        serializer = EmailPasswordLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        return Response({
            "success": True,
            "message": "Login successful",
            "role": user.role,
            "tokens": get_tokens(user),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "phone": user.phone,
            }
        }, status=200)




#============Logout API =============#

class LogoutAPI(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = []  # No authentication required for logout since we are using refresh token

    @swagger_auto_schema(request_body=LogoutSerializer)
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
        except Exception:
            return Response(
                {"detail": "Invalid or expired refresh token"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"success": True, "message": "Logged out successfully"},
            status=status.HTTP_200_OK
        )




#=============Login APIs =============#

class LoginSendOTPAPI(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # No authentication required for sending OTP

    @swagger_auto_schema(request_body=SendOTPSerializer)
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        # user must exist
        if not User.objects.filter(email=email).exists():
            return Response(
                {"detail": "User not found. Please register."},
                status=404
            )

        send_email_otp(email)
        return Response({"message": "OTP sent for login"})



class LoginVerifyOTPAPI(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # No authentication required for OTP verification  

    @swagger_auto_schema(request_body=VerifyOTPSerializer)
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        if not verify_email_otp(email, otp):
            return Response(
                {"detail": "Invalid or expired OTP"},
                status=400
            )

        user = User.objects.get(email=email)

        return Response({
            "message": "Login successful",
            "role": user.role,
            "tokens": get_tokens(user),
        })


#=============Register APIs =============#

class RegisterSendOTPAPI(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # No authentication required for registration OTP

    @swagger_auto_schema(
        operation_summary="Send Registration OTP",
        operation_description="Send OTP to email for new user registration",
        request_body=SendOTPSerializer,
        tags=["Auth"],
        responses={
            200: openapi.Response(
                description="OTP Sent",
                examples={
                    "application/json": {
                        "message": "OTP sent for registration"
                    }
                }
            ),
            400: "User already exists"
        }
    )
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        if User.objects.filter(email=email).exists():
            return Response(
                {"detail": "User already exists. Please login."},
                status=400
            )

        send_email_otp(email)
        return Response({"message": "OTP sent for registration"})

class RegisterVerifyOTPAPI(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # No authentication required for OTP verification
    @swagger_auto_schema(
        operation_summary="Verify Registration OTP",
        request_body=VerifyOTPSerializer,
        responses={200: "OTP Verified", 400: "Invalid OTP"}
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        # 🔥 Use utility function
        if not verify_email_otp(email, otp):
            return Response(
                {"detail": "Invalid or expired OTP"},
                status=400
            )

        return Response({
            "message": "OTP verified successfully. Please complete registration."
        })

class RegisterCompleteAPI(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # No authentication required for completing registration
    @swagger_auto_schema(request_body=CompleteRegisterSerializer)
    def post(self, request):
        serializer = CompleteRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        # Check OTP verified
        if not EmailOTP.objects.filter(email=email, is_verified=True).exists():
            return Response(
                {"detail": "Email not verified or OTP expired"},
                status=400
            )

        # Prevent duplicate user
        if User.objects.filter(email=email).exists():
            return Response(
                {"detail": "User already exists"},
                status=400
            )

        # Create user
        user = User.objects.create_user(
            email=email,
            phone=serializer.validated_data["phone"],
            password=serializer.validated_data["password"],
            role=serializer.validated_data["role"],
        )

        user.name = serializer.validated_data["name"]
        user.is_verified = True
        user.save()

        # Create profile
        if user.role == "CUSTOMER":
            CustomerProfile.objects.create(user=user)
        elif user.role == "SERVICEMAN":
            ServicemanProfile.objects.create(user=user)
        elif user.role == "VENDOR":
            VendorProfile.objects.create(user=user)

        return Response({
            "success": True,
            "message": "User registered successfully",
            "tokens": get_tokens(user)
        })



#=============User Profile API =============#
class UserProfileAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get Logged In User Profile",
        security=[{"Bearer": []}],
        tags=["Profile"]
    )
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)



class CustomerProfileAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=CustomerProfileSerializer,
        responses={200: CustomerProfileSerializer}
    )
    def post(self, request):
        if request.user.role != "CUSTOMER":
            return Response(
                {"detail": "Only customers can create this profile"},
                status=403
            )

        profile, _ = CustomerProfile.objects.get_or_create(user=request.user)

        serializer = CustomerProfileSerializer(
            profile, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "Customer profile saved successfully",
            "profile": serializer.data
        })


class ServicemanProfileAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=ServicemanProfileSerializer,
        responses={200: ServicemanProfileSerializer}
    )
    def post(self, request):
        if request.user.role != "SERVICEMAN":
            return Response(
                {"detail": "Only servicemen can create this profile"},
                status=403
            )

        profile, _ = ServicemanProfile.objects.get_or_create(
            user=request.user
        )

        serializer = ServicemanProfileSerializer(
            profile, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "Serviceman profile saved successfully",
            "profile": serializer.data
        })





class VendorProfileAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=VendorProfileSerializer,
        responses={200: VendorProfileSerializer}
    )
    def post(self, request):
        if request.user.role != "VENDOR":
            return Response(
                {"detail": "Only vendors can create this profile"},
                status=403
            )

        profile, _ = VendorProfile.objects.get_or_create(
            user=request.user
        )

        serializer = VendorProfileSerializer(
            profile, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "Vendor profile saved successfully",
            "profile": serializer.data
        })



class SaveProfileAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.role == "CUSTOMER":
            model = CustomerProfile
            serializer_class = CustomerProfileSerializer

        elif user.role == "SERVICEMAN":
            model = ServicemanProfile
            serializer_class = ServicemanProfileSerializer

        elif user.role == "VENDOR":
            model = VendorProfile
            serializer_class = VendorProfileSerializer

        else:
            return Response({"detail": "Invalid role"}, status=400)

        profile, _ = model.objects.get_or_create(user=user)

        serializer = serializer_class(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "Profile saved successfully",
            "profile": serializer.data
        })



class ProfileAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get logged-in user profile",
        responses={200: ProfileResponseSerializer}
    )
    def get(self, request):
        user = request.user
        user_data = UserProfileSerializer(user).data
        profile_data = None

        if user.role == "CUSTOMER":
            profile = CustomerProfile.objects.filter(user=user).first()
            if profile:
                profile_data = CustomerProfileSerializer(profile).data

        elif user.role == "SERVICEMAN":
            profile = ServicemanProfile.objects.filter(user=user).first()
            if profile:
                profile_data = ServicemanProfileSerializer(profile).data

        elif user.role == "VENDOR":
            profile = VendorProfile.objects.filter(user=user).first()
            if profile:
                profile_data = VendorProfileSerializer(profile).data

        return Response({
            "user": user_data,
            "profile": profile_data
        })





#=============Profile Update API =============#
class CustomerProfileUpdateAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=CustomerProfileSerializer,
        responses={200: CustomerProfileSerializer}
    )
    def put(self, request):

        if request.user.role != "CUSTOMER":
            return Response(
                {"detail": "Only CUSTOMER can update this profile"},
                status=403
            )

        profile, _ = CustomerProfile.objects.get_or_create(user=request.user)

        serializer = CustomerProfileSerializer(
            profile,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class ServicemanProfileUpdateAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=ServicemanProfileSerializer,
        responses={200: ServicemanProfileSerializer}
    )
    def put(self, request):

        if request.user.role != "SERVICEMAN":
            return Response(
                {"detail": "Only SERVICEMAN can update this profile"},
                status=403
            )

        profile, _ = ServicemanProfile.objects.get_or_create(user=request.user)

        serializer = ServicemanProfileSerializer(
            profile,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class VendorProfileUpdateAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=VendorProfileSerializer,
        responses={200: VendorProfileSerializer}
    )
    def put(self, request):

        if request.user.role != "VENDOR":
            return Response(
                {"detail": "Only VENDOR can update this profile"},
                status=403
            )

        profile, _ = VendorProfile.objects.get_or_create(user=request.user)

        serializer = VendorProfileSerializer(
            profile,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
