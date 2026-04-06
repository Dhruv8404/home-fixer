import profile
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from django.conf import settings
import stripe
import cloudinary
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Booking, BookingItem, Payment, User, CustomerProfile, ServicemanProfile, VendorProfile, EmailOTP,Category,Service,Product
from .serializers import (
    BookingCreateSerializer,
    SendOTPSerializer,
    VendorNearbySerializer,
    VerifyOTPSerializer,
    CompleteRegisterSerializer,
    UserProfileSerializer,
    LogoutSerializer,
    VendorProfileSerializer,
    ServicemanProfileSerializer,
    CustomerProfileSerializer,
    ProfileResponseSerializer,
    UniversalProfileUpdateSerializer,
    CategorySerializer,
    ServicemanSerializer,
    VerifyStripePaymentSerializer
)
from .utils import send_email_otp, verify_email_otp
from rest_framework import request, status
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .permissions import IsAdminOrCustomer
from .utils import delete_cloudinary_image

def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }

from .serializers import EmailPasswordLoginSerializer
from django.contrib.auth import authenticate

stripe.api_key = settings.STRIPE_SECRET_KEY
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

    @swagger_auto_schema(request_body=LogoutSerializer)
    def post(self, request):
        response = Response(
            {"success": True, "message": "Logged out successfully"}
        )

        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return response



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
    parser_classes = (MultiPartParser, FormParser)
    @swagger_auto_schema(
    request_body=CustomerProfileSerializer,
    consumes=["multipart/form-data"],
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
    parser_classes = (MultiPartParser, FormParser)    

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
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        request_body=VendorProfileSerializer,
        consumes=["multipart/form-data"],
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
    parser_classes = (MultiPartParser, FormParser)
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
    parser_classes = (MultiPartParser, FormParser)
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
    parser_classes = (MultiPartParser, FormParser)
    @swagger_auto_schema(
    request_body=CustomerProfileSerializer,
    consumes=["multipart/form-data"],
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
    parser_classes = (MultiPartParser, FormParser)
    @swagger_auto_schema(
        request_body=ServicemanProfileSerializer,
        consumes=["multipart/form-data"],
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
    parser_classes = (MultiPartParser, FormParser)
    @swagger_auto_schema(
        request_body=VendorProfileSerializer,
        consumes=["multipart/form-data"],
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



#=============Soft Delete APIs for Service and Product =============#
class ServiceSoftDeleteAPI(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, pk):
        service = get_object_or_404(Service, pk=pk)
        service.is_active = False
        service.save()
        return Response({"message": "Service soft deleted"})


class ProductSoftDeleteAPI(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.is_active = False
        product.save()
        return Response({"message": "Product soft deleted"})

#=============Nearby Servicemen API =============#
from rest_framework.exceptions import ValidationError
from .utils import distance_km
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Serviceman

class NearbyServicemanAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get All Servicemen Within 10km",
        manual_parameters=[
            openapi.Parameter("lat", openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True),
            openapi.Parameter("lon", openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True),
        ],
        responses={200: ServicemanProfileSerializer(many=True)},
        security=[{"Bearer": []}],
        tags=["Servicemen"]
    )
    def get(self, request):

        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")

        if not lat or not lon:
            raise ValidationError({"detail": "Latitude and longitude are required"})

        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            raise ValidationError({"detail": "Invalid latitude or longitude"})

        queryset = ServicemanProfile.objects.select_related("user").filter(
            is_active=True,
            is_approved=True,
            current_lat__isnull=False,
            current_long__isnull=False
        )

        nearby = []

        for profile in queryset:
            distance = distance_km(
                lat,
                lon,
                float(profile.current_lat),
                float(profile.current_long)
            )

            if distance <= 10:
                nearby.append(profile)

        serializer = ServicemanProfileSerializer(nearby, many=True)
        return Response(serializer.data)




class CategoryNearbyServicemanAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get Category Based Servicemen Within 10km",
        manual_parameters=[
            openapi.Parameter("lat", openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True),
            openapi.Parameter("lon", openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True),
            openapi.Parameter(
                "category",
                openapi.IN_QUERY,
                description="Category name (Example: Plumbing)",
                type=openapi.TYPE_STRING,
                required=True
            ),
        ],
        responses={200: ServicemanProfileSerializer(many=True)},
        security=[{"Bearer": []}],
        tags=["Servicemen"]
    )
    def get(self, request):

        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")
        category = request.query_params.get("category")

        if not lat or not lon or not category:
            raise ValidationError({"detail": "Latitude, longitude and category are required"})

        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            raise ValidationError({"detail": "Invalid latitude or longitude"})

        queryset = ServicemanProfile.objects.select_related("user").filter(
            is_active=True,
            is_approved=True,
            skills__contains=[category],   # 🔥 CATEGORY = SKILL
            current_lat__isnull=False,
            current_long__isnull=False
        )

        nearby = []

        for profile in queryset:
            distance = distance_km(
                lat,
                lon,
                float(profile.current_lat),
                float(profile.current_long)
            )

            if distance <= 10:
                nearby.append(profile)

        serializer = ServicemanProfileSerializer(nearby, many=True)
        return Response(serializer.data)



#----------------Servicemen List API-----------------

class ServicemenListAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrCustomer]

    @swagger_auto_schema(
        operation_summary="List Approved & Active Servicemen (within 10km)",
        manual_parameters=[
            openapi.Parameter(
                "lat",
                openapi.IN_QUERY,
                description="Latitude",
                type=openapi.TYPE_NUMBER,
                required=True,
            ),
            openapi.Parameter(
                "lon",
                openapi.IN_QUERY,
                description="Longitude",
                type=openapi.TYPE_NUMBER,
                required=True,
            ),
            openapi.Parameter(
                "category",
                openapi.IN_QUERY,
                description="Filter by category name",
                type=openapi.TYPE_STRING,
                required=False,
            )
        ],
        responses={200: ServicemanSerializer(many=True)},
        security=[{"Bearer": []}],
        tags=["Servicemen"]
    )
    def get(self, request):

        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")
        category = request.query_params.get("category")

        if not lat or not lon:
            raise ValidationError({"detail": "Latitude and longitude are required"})

        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            raise ValidationError({"detail": "Latitude and longitude must be numbers"})

        queryset = Serviceman.objects.filter(
            is_active=True,
            servicemanprofile__is_active=True,
            servicemanprofile__is_approved=True
        )

        if category:
            queryset = queryset.filter(category__name__iexact=category)

        nearby = []

        for serviceman in queryset:
            distance = distance_km(lat, lon, serviceman.latitude, serviceman.longitude)

            if distance <= 10:
                nearby.append(serviceman)

        serializer = ServicemanSerializer(nearby, many=True)
        return Response(serializer.data)
    
from .permissions import IsAdminRole
class AdminServicemanControlAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]
    @swagger_auto_schema(
    operation_summary="Admin: Approve / Deactivate Serviceman",
    operation_description="""
Admin can:

• Approve Serviceman (is_approved = true)
• Deactivate Serviceman (is_active = false)
• Reactivate Serviceman (is_active = true)

Only ADMIN role allowed.
""",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "is_approved": openapi.Schema(
                type=openapi.TYPE_BOOLEAN,
                description="Approve or reject serviceman"
            ),
            "is_active": openapi.Schema(
                type=openapi.TYPE_BOOLEAN,
                description="Activate or deactivate serviceman"
            ),
        },
        example={
            "is_approved": True,
            "is_active": True
        }
    ),
    responses={
        200: openapi.Response(
            description="Serviceman updated successfully",
            examples={
                "application/json": {
                    "id": 5,
                    "is_approved": True,
                    "is_active": True,
                    "message": "Serviceman updated successfully"
                }
            }
        ),
        404: "Serviceman not found",
        403: "Admin access required"
    },
    security=[{"Bearer": []}],
    tags=["Admin - Serviceman Control"]
)

    
    def patch(self, request, pk):
        profile = get_object_or_404(
            ServicemanProfile,
            pk=pk,

        )

        allowed_fields = ["is_approved", "is_active"]

        for field in allowed_fields:
            if field in request.data:
                setattr(profile, field, request.data[field])

        profile.save()

        return Response({
            "id": profile.pk,
            "is_approved": profile.is_approved,
            "is_active": profile.is_active,
            "message": "Serviceman updated successfully"
        })
    def delete(self, request, pk):
        profile = get_object_or_404(
            ServicemanProfile,
            pk=pk,
            is_active=True
        )

        profile.is_active = False
        profile.save()

        return Response({
            "id": profile.pk,
            "message": "Serviceman soft deleted successfully"
        })    

class AdminVendorControlAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
    operation_summary="Admin: Approve / Deactivate Vendor",
    operation_description="""
Admin can:

• Approve Vendor (is_approved = true)
• Deactivate Vendor (is_active = false)
• Reactivate Vendor (is_active = true)

Only ADMIN role allowed.
""",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "is_approved": openapi.Schema(
                type=openapi.TYPE_BOOLEAN,
                description="Approve or reject vendor"
            ),
            "is_active": openapi.Schema(
                type=openapi.TYPE_BOOLEAN,
                description="Activate or deactivate vendor"
            ),
        },
        example={
            "is_approved": True,
            "is_active": True
        }
    ),
    responses={
        200: openapi.Response(
            description="Vendor updated successfully",
            examples={
                "application/json": {
                    "id": 3,
                    "is_approved": True,
                    "is_active": True,
                    "message": "Vendor updated successfully"
                }
            }
        )
    },
    security=[{"Bearer": []}],
    tags=["Admin - Vendor Control"]
)
    def patch(self, request, pk):
        profile = get_object_or_404(
            VendorProfile,
            pk=pk,
            is_active=True
        )

        allowed_fields = ["is_approved", "is_active"]

        for field in allowed_fields:
            if field in request.data:
                setattr(profile, field, request.data[field])

        profile.save()

        return Response({
            "id": profile.pk,
            "is_approved": profile.is_approved,
            "is_active": profile.is_active,
            "message": "Vendor updated successfully"
        })

    def delete(self, request, pk):
        profile = get_object_or_404(
            VendorProfile,
            pk=pk,
            is_active=True
        )

        profile.is_active = False
        profile.save()

        return Response({
            "id": profile.pk,
            "message": "Vendor soft deleted successfully"
        })


class PendingVendorsAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
    operation_summary="Admin: List Pending Vendors",
    operation_description="""
Returns all vendors where:
- is_approved = False
- is_active = True
""",
    responses={
        200: VendorProfileSerializer(many=True)
    },
    security=[{"Bearer": []}],
    tags=["Admin - Approval"]
)
    def get(self, request):
        vendors = VendorProfile.objects.filter(
            is_approved=False,
            is_active=True
        )

        serializer = VendorProfileSerializer(vendors, many=True)
        return Response(serializer.data)
    
class PendingServicemenAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
    operation_summary="Admin: List Pending Servicemen",
    operation_description="""
Returns all servicemen where:
- is_approved = False
- is_active = True
""",
    responses={
        200: ServicemanProfileSerializer(many=True)
    },
    security=[{"Bearer": []}],
    tags=["Admin - Approval"]
)
    def get(self, request):
        servicemen = ServicemanProfile.objects.filter(
            is_approved=False,
            is_active=True
        )

        serializer = ServicemanProfileSerializer(servicemen, many=True)
        return Response(serializer.data)


class AdminCustomerListAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_summary="Admin: Get All Customers",
        operation_description="Returns all users with role CUSTOMER.",
        responses={200: UserProfileSerializer(many=True)},
        security=[{"Bearer": []}],
        tags=["Admin - Users"]
    )
    def get(self, request):
        customers = User.objects.filter(role="CUSTOMER")
        serializer = UserProfileSerializer(customers, many=True)
        return Response(serializer.data)



class AdminServicemanListAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_summary="Admin: Get All Servicemen",
        operation_description="Returns all servicemen with profile details.",
        responses={200: ServicemanProfileSerializer(many=True)},
        security=[{"Bearer": []}],
        tags=["Admin - Users"]
    )
    def get(self, request):
        servicemen = ServicemanProfile.objects.select_related("user")
        serializer = ServicemanProfileSerializer(servicemen, many=True)
        return Response(serializer.data)
    

class AdminVendorListAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_summary="Admin: Get All Vendors",
        operation_description="Returns all vendor profiles.",
        responses={200: VendorProfileSerializer(many=True)},
        security=[{"Bearer": []}],
        tags=["Admin - Users"]
    )
    def get(self, request):
        vendors = VendorProfile.objects.select_related("user")
        serializer = VendorProfileSerializer(vendors, many=True)
        return Response(serializer.data)    
    


class NearbyVendorAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get Nearby Vendors Within 10km",
        manual_parameters=[
            openapi.Parameter("lat", openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True),
            openapi.Parameter("lon", openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True),
        ],
        responses={200: VendorNearbySerializer(many=True)},
        security=[{"Bearer": []}],
        tags=["Vendors"]
    )
    def get(self, request):

        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")

        if not lat or not lon:
            raise ValidationError({"detail": "Latitude and longitude required"})

        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            raise ValidationError({"detail": "Invalid coordinates"})

        queryset = VendorProfile.objects.filter(
            is_active=True,
            is_approved=True,
            store_lat__isnull=False,
            store_long__isnull=False
        )

        nearby = []

        for vendor in queryset:
            distance = distance_km(
                lat,
                lon,
                float(vendor.store_lat),
                float(vendor.store_long)
            )

            if distance <= 10:
                nearby.append(vendor)

        serializer = VendorNearbySerializer(nearby, many=True)
        return Response(serializer.data)    
    

# ================= BOOKING APIs =================
#=============Booking Creation API =============#
from .serializers import BookingCreateSerializer, BookingDetailSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
import cloudinary.uploader
from decimal import Decimal

class BookingCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        operation_summary="Create Booking (Payment Required)",
        operation_description="""
Create booking → Payment required before activation.

Flow:
1. Booking created → PENDING_PAYMENT
2. Customer pays
3. Booking becomes ACTIVE
""",
        request_body=BookingCreateSerializer,
        consumes=["multipart/form-data"],
        manual_parameters=[
            openapi.Parameter(
                name="images",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                description="Upload multiple images",
                required=False,
            )
        ],
        responses={
            201: openapi.Response(
                description="Booking created",
                examples={
                    "application/json": {
                        "message": "Booking created. Please complete payment",
                        "booking_id": 1,
                        "booking_status": "PENDING_PAYMENT",
                        "payment_status": "PENDING",
                        "amount": 500
                    }
                }
            )
        },
        security=[{"Bearer": []}],
        tags=["Booking"]
    )
    def post(self, request):

        serializer = BookingCreateSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        booking = serializer.save()

        # 🔥 FORCE PAYMENT FIRST
        booking.status = "PENDING_PAYMENT"
        booking.payment_status = "PENDING"
        booking.save()

        # IMAGE UPLOAD
        files = request.FILES.getlist("images")
        image_urls = []

        for file in files:
            result = cloudinary.uploader.upload(
                file,
                folder=f"home_fixer/bookings/{booking.id}/"
            )
            image_urls.append(result.get("secure_url"))

        booking.image_urls = (booking.image_urls or []) + image_urls
        booking.save()

        return Response({
            "message": "Booking created. Please complete payment",
            "booking_id": booking.id,
            "booking_status": booking.status,
            "payment_status": booking.payment_status,
            "amount": booking.total_cost,
            "image_urls": booking.image_urls
        }, status=201)


class BookingDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get booking details",
        tags=["Bookings"],
        security=[{"Bearer": []}],
    )
    def get(self, request, booking_id):

        try:
            booking = Booking.objects.select_related(
                "serviceman",
                "customer"
            ).get(id=booking_id)

        except Booking.DoesNotExist:
            return Response(
                {"error": "Booking not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # CUSTOMER can see only their booking
        if request.user.role == "CUSTOMER":
            if booking.customer.user != request.user:
                return Response(
                    {"error": "You cannot view this booking"},
                    status=403
                )

        # SERVICEMAN can see only assigned booking
        if request.user.role == "SERVICEMAN":
            if booking.serviceman.user != request.user:
                return Response(
                    {"error": "You are not assigned to this booking"},
                    status=403
                )

        serializer = BookingDetailSerializer(booking)

        return Response(serializer.data)
# ================= SERVICE Booking =================

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Booking, ServicemanProfile

class ServicemanBookingActionAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Serviceman Accept / Reject Booking",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "action": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["accept", "reject"]
                )
            }
        ),
        responses={200: "Success"},
        security=[{"Bearer": []}],
        tags=["Booking"]
    )
    def patch(self, request, booking_id):

        if request.user.role != "SERVICEMAN":
            return Response({"error": "Only serviceman"}, status=403)

        booking = get_object_or_404(Booking, pk=booking_id)

        serviceman = get_object_or_404(
            ServicemanProfile,
            user=request.user
        )

        if booking.serviceman != serviceman:
            return Response({"error": "Not assigned"}, status=403)

        # 🔥 PAYMENT CHECK
        if booking.payment_status != "PAID":
            return Response({"error": "Payment not completed"}, status=400)

        if booking.status != "PENDING":
            return Response({"error": "Invalid booking state"}, status=400)

        action = request.data.get("action")

        if action == "accept":
            booking.status = "ACCEPTED"

        elif action == "reject":
            booking.status = "CANCELLED"

        else:
            return Response({"error": "Invalid action"}, status=400)

        booking.save()

        return Response({
            "message": f"Booking {action}ed successfully",
            "status": booking.status
        })


class CustomerCancelBookingAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Customer: Cancel Booking",
        operation_description="""Customer can cancel a booking.
        - Only bookings in PENDING status can be cancelled
        - Cancelling sets status to CANCELLED
        Only the booking owner can perform this action.""",
        responses={
            200: openapi.Response(
                description="Booking cancelled successfully",
                examples={
                    "application/json": {
                        "message": "Booking cancelled successfully",
                        "status": "CANCELLED"
                    }
                }
            ),
            400: "Booking cannot be cancelled",
            403: "Only booking owner can cancel this booking"
        },
        security=[{"Bearer": []}],
        tags=["Booking - Customer Actions"]
    )

    def patch(self, request, booking_id):

        if request.user.role != "CUSTOMER":
            return Response(
                {"detail": "Only customer can cancel booking"},
                status=403
            )

        booking = get_object_or_404(Booking, pk=booking_id)

        # check ownership
        if booking.customer.user != request.user:
            return Response(
                {"detail": "This booking does not belong to you"},
                status=403
            )

        # cancellation rules
        if booking.status in ["ONGOING", "COMPLETED", "CANCELLED"]:
            return Response(
                {"detail": "This booking cannot be cancelled"},
                status=400
            )

        booking.status = "CANCELLED"
        booking.save()

        return Response({
            "message": "Booking cancelled successfully",
            "status": booking.status
        })            



from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Product, VendorProfile
from .serializers import ProductSerializer


class ProductCreateAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser) 
    @swagger_auto_schema(
        request_body=ProductSerializer,
        responses={201: ProductSerializer},
        security=[{"Bearer": []}],
        tags=["Products - Admin & Vendor"]
    )
    def post(self, request):

        if request.user.role not in ["ADMIN", "VENDOR"]:
            return Response(
                {"detail": "Only admin or vendor can create product"},
                status=403
            )

        data = request.data.copy()

        # Vendor → auto assign vendor
        if request.user.role == "VENDOR":
            vendor = get_object_or_404(VendorProfile, user=request.user)
            data["vendor"] = vendor.pk

        # Admin → must provide vendor
        if request.user.role == "ADMIN" and "vendor" not in data:
            return Response(
                {"detail": "Admin must provide vendor id"},
                status=400
            )

        serializer = ProductSerializer(
    data=data,
    context={"request": request}
)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=201)
    
class ProductListAPI(APIView):
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        operation_summary="Get All Available Products",
        operation_description="Returns all products with stock_quantity > 0.",
        responses={200: ProductSerializer(many=True)},
        tags=["Products"]
    )

    def get(self, request):

        products = Product.objects.filter(stock_quantity__gt=0)

        serializer = ProductSerializer(products, many=True)

        return Response(serializer.data)


class ProductUpdateAPI(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        request_body=ProductSerializer,
        responses={200: ProductSerializer},
        security=[{"Bearer": []}],
        tags=["Products - Admin & Vendor"]
    )
    def put(self, request, pk):

        product = get_object_or_404(Product, pk=pk)

        # Only admin or owner vendor
        if request.user.role == "VENDOR":
            if product.vendor.user != request.user:
                return Response(
                    {"detail": "You can update only your products"},
                    status=403
                )

        elif request.user.role != "ADMIN":
            return Response(
                {"detail": "Not allowed"},
                status=403
            )

        serializer = ProductSerializer(
            product,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
    


class ProductDeleteAPI(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_summary="Delete Product (Admin or Owner Vendor)",
        operation_description="Deletes a product. Only the owning vendor or admin can delete.",
        responses={
            200: openapi.Response(
                description="Product deleted successfully",
                examples={
                    "application/json": {
                        "message": "Product deleted successfully"
                    }
                }
            ),
            403: "Not allowed to delete this product",
            404: "Product not found"
        },
        security=[{"Bearer": []}],
        tags=["Products - Admin & Vendor"]
    )
    def delete(self, request, pk):

        product = get_object_or_404(Product, pk=pk)

        if request.user.role == "VENDOR":
            if product.vendor.user != request.user:
                return Response({"detail": "You can delete only your products"}, status=403)

        elif request.user.role != "ADMIN":
            return Response({"detail": "Not allowed"}, status=403)

        # Delete image from Cloudinary
        if product.image:
            delete_cloudinary_image(product.image)
            try:
                if hasattr(product.image, "public_id"):
                    cloudinary.uploader.destroy(product.image.public_id)
            except Exception:
                pass

        product.delete()

        return Response({"message": "Product deleted successfully"})


class CategoryAPIView(APIView):

    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_summary="Get All Categories / Create Category",
        operation_description="GET returns all categories. POST creates a new category (Admin only).",
        request_body=CategorySerializer,
        responses={
            200: CategorySerializer(many=True),
            201: CategorySerializer,
            403: "Only admin can create category"
        },
        security=[{"Bearer": []}],
        tags=["Categories"]
    )
    def get(self, request):

        categories = Category.objects.all()

        serializer = CategorySerializer(categories, many=True)

        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Create Category (Admin only)",
        operation_description="Creates a new category. Only users with ADMIN role can perform this action.",
        request_body=CategorySerializer,
        responses={
            201: CategorySerializer,
            403: "Only admin can create category"
        },
        security=[{"Bearer": []}],
        tags=["Categories"]
    )
    def post(self, request):

        if request.user.role != "ADMIN":
            return Response(
                {"error": "Only admin can create category"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CategorySerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)      



from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Category
from .serializers import CategorySerializer
from .permissions import IsAdminRole
from rest_framework import status

class ProductCategoryAPI(APIView):

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Get all product categories",
        responses={200: CategorySerializer(many=True)},
        tags=["Product Categories"]
    )
    def get(self, request):

        categories = Category.objects.filter(category_type="PRODUCT")

        serializer = CategorySerializer(categories, many=True)

        return Response(serializer.data)


    @swagger_auto_schema(
        operation_summary="Create product category (Admin only)",
        request_body=CategorySerializer,
        responses={201: CategorySerializer},
        security=[{"Bearer": []}],
        tags=["Product Categories"]
    )
    def post(self, request):

        if request.user.role != "ADMIN":
            return Response(
                {"error": "Only admin can create category"},
                status=403
            )

        data = request.data.copy()
        data["category_type"] = "PRODUCT"

        serializer = CategorySerializer(data=data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=201)
    
class ProductCategoryDeleteAPI(APIView):

    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_summary="Delete product category (Admin only)",
        responses={200: "Category deleted"},
        security=[{"Bearer": []}],
        tags=["Product Categories"]
    )

    def delete(self, request, pk):

        category = get_object_or_404(
            Category,
            pk=pk,
            category_type="PRODUCT"
        )

        category.delete()

        return Response({
            "message": "Product category deleted successfully"
        })
#====================SERVICEMAN BOOKING LIST API =================
class ServicemanBookingRequestsAPI(APIView):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Serviceman: View ONLY PAID bookings",
        operation_description="""
🔒 Serviceman can only see bookings AFTER payment.

✔ Only bookings where:
- payment_status = PAID
- assigned to logged-in serviceman

❌ Hidden:
- PENDING_PAYMENT
- FAILED
""",
        responses={
            200: openapi.Response(
                description="List of paid bookings",
                examples={
                    "application/json": {
                        "count": 2,
                        "bookings": [
                            {
                                "id": 65,
                                "status": "PENDING",
                                "payment_status": "PAID",
                                "customer_name": "John Doe",
                                "problem_title": "AC not working"
                            }
                        ]
                    }
                }
            ),
            403: "Only serviceman allowed"
        },
        security=[{"Bearer": []}],
        tags=["Serviceman Bookings"]
    )
    def get(self, request):

        # =========================
        # 1. ROLE CHECK
        # =========================
        if request.user.role != "SERVICEMAN":
            return Response(
                {"error": "Only serviceman can access this"},
                status=403
            )

        # =========================
        # 2. GET SERVICEMAN PROFILE
        # =========================
        serviceman = get_object_or_404(
            ServicemanProfile,
            user=request.user
        )

        # =========================
        # 3. FILTER BOOKINGS (🔥 FIX)
        # =========================
        bookings = Booking.objects.select_related(
            "customer__user",
            "serviceman__user"
        ).filter(
            serviceman=serviceman,
            payment_status="PAID"   # 🔥 ONLY PAID BOOKINGS
        ).order_by("-created_at")

        # =========================
        # 4. SERIALIZE RESPONSE
        # =========================
        response_data = []

        for booking in bookings:
            response_data.append({
                "booking_id": booking.id,
                "status": booking.status,
                "payment_status": booking.payment_status,
                "scheduled_date": booking.scheduled_date,
                "scheduled_time": booking.scheduled_time,
                "problem_title": booking.problem_title,
                "problem_description": booking.problem_description,
                "total_cost": booking.total_cost,
                "created_at": booking.created_at,

                "customer": {
                    "name": booking.customer.user.name,
                    "phone": booking.customer.user.phone,
                }
            })

        # =========================
        # 5. RESPONSE
        # =========================
        return Response({
            "count": len(response_data),
            "bookings": response_data
        })


#=============Booking Tracking API =============#

from .serializers import BookingTrackingSerializer


def get_status_text(status):

    status_map = {
        "PENDING": "Waiting for serviceman to accept",
        "ACCEPTED": "Serviceman accepted your booking",
        "REJECTED": "Serviceman rejected the booking",
        "ONGOING": "Service is currently in progress",
        "COMPLETED": "Service completed successfully",
        "CANCELLED": "Booking was cancelled"
    }

    return status_map.get(status, status)

class BookingTrackingAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Track Booking (Only After Serviceman Accepts)",
        operation_description="""
🚫 Tracking NOT allowed until serviceman accepts booking.

✔ Allowed:
- ACCEPTED
- ONGOING
- COMPLETED

❌ Blocked:
- PENDING (not accepted yet)
- PENDING_PAYMENT
""",
        responses={
            200: openapi.Response(
                description="Tracking data",
                examples={
                    "application/json": {
                        "booking_id": 65,
                        "status": "ONGOING",
                        "status_text": "Service is currently in progress",
                        "serviceman_name": "John",
                        "distance_km": 2.5,
                        "eta_minutes": 5
                    }
                }
            ),
            400: "Tracking not available",
            403: "Unauthorized"
        },
        security=[{"Bearer": []}],
        tags=["Booking Tracking"]
    )
    def get(self, request, booking_id):

        # =========================
        # 1. GET BOOKING
        # =========================
        try:
            booking = Booking.objects.select_related(
                "serviceman__user",
                "customer__user"
            ).get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=404)

        # =========================
        # 2. ACCESS CONTROL
        # =========================
        if request.user.role == "CUSTOMER":
            if booking.customer.user != request.user:
                return Response({"error": "Unauthorized"}, status=403)

        elif request.user.role == "SERVICEMAN":
            if booking.serviceman.user != request.user:
                return Response({"error": "Unauthorized"}, status=403)

        else:
            return Response({"error": "Access not allowed"}, status=403)

        # =========================
        # 🔥 3. PAYMENT CHECK
        # =========================
        if booking.payment_status != "PAID":
            return Response({
                "error": "Tracking not available until payment completed"
            }, status=400)

        # =========================
        # 🔥 4. ACCEPT CHECK (IMPORTANT FIX)
        # =========================
        if booking.status == "PENDING":
            return Response({
                "error": "Tracking not available until serviceman accepts booking"
            }, status=400)

        # =========================
        # 5. SERVICEMAN CHECK
        # =========================
        if not booking.serviceman:
            return Response({"error": "No serviceman assigned yet"}, status=400)

        serviceman = booking.serviceman

        if not (serviceman.live_lat or serviceman.current_lat):
            return Response({"error": "Serviceman location not available"}, status=400)

        if not booking.customer.default_lat or not booking.customer.default_long:
            return Response({"error": "Customer location not available"}, status=400)

        # =========================
        # 6. CALCULATE DISTANCE
        # =========================
        serviceman_lat = float(serviceman.live_lat or serviceman.current_lat)
        serviceman_long = float(serviceman.live_long or serviceman.current_long)

        dist_km = distance_km(
            float(booking.customer.default_lat),
            float(booking.customer.default_long),
            serviceman_lat,
            serviceman_long
        )

        # =========================
        # 7. AUTO ONGOING (ARRIVAL)
        # =========================
        if dist_km < 0.1 and booking.status == "ACCEPTED":
            booking.status = "ONGOING"
            booking.save()

        eta_minutes = round((dist_km / 30) * 60)
        if eta_minutes < 1:
            eta_minutes = 1

        # =========================
        # 8. RESPONSE
        # =========================
        data = {
            "booking_id": booking.id,
            "status": booking.status,
            "status_text": get_status_text(booking.status),
            "serviceman_name": serviceman.user.name or serviceman.user.email,
            "serviceman_rating": float(serviceman.average_rating or 0),
            "serviceman_lat": serviceman.live_lat or serviceman.current_lat,
            "serviceman_long": serviceman.live_long or serviceman.current_long,
            "customer_name": booking.customer.user.name,
            "customer_image": (
                booking.customer.profile_image.url
                if booking.customer.profile_image else None
            ),
            "customer_lat": booking.customer.default_lat,
            "customer_long": booking.customer.default_long,
            "customer_address": booking.customer.default_address or "",
            "distance_km": round(dist_km, 2),
            "eta_minutes": eta_minutes,
            "image_urls": booking.image_urls or []
        }

        serializer = BookingTrackingSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)
    

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class ServicemanLocationUpdateAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Serviceman: Update Live Location",
        operation_description="""
Update real-time location of serviceman.

• Updates `live_lat` and `live_long`
• Used for tracking and ETA
• Does NOT affect base location (current_lat, current_long)
""",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["lat", "lon"],
            properties={
                "lat": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    format=openapi.FORMAT_FLOAT,
                    example=21.7051,
                    description="Latitude"
                ),
                "lon": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    format=openapi.FORMAT_FLOAT,
                    example=72.9959,
                    description="Longitude"
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Live location updated successfully",
                examples={
                    "application/json": {
                        "message": "Live location updated successfully",
                        "live_lat": 21.7051,
                        "live_long": 72.9959
                    }
                }
            ),
            400: "Invalid input",
            403: "Only serviceman allowed"
        },
        security=[{"Bearer": []}],
        tags=["Serviceman Location"]
    )
    def patch(self, request):

        if request.user.role != "SERVICEMAN":
            return Response(
                {"detail": "Only serviceman can update location"},
                status=403
            )

        lat = request.data.get("lat")
        lon = request.data.get("lon")

        if lat is None or lon is None:
            return Response(
                {"detail": "Latitude and longitude required"},
                status=400
            )

        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            return Response(
                {"detail": "Invalid coordinates"},
                status=400
            )

        profile = get_object_or_404(
            ServicemanProfile,
            user=request.user
        )

        # 🔥 Update LIVE location
        profile.live_lat = lat
        profile.live_long = lon
        profile.is_online = True
        profile.save()

        return Response({
            "message": "Live location updated successfully",
            "live_lat": lat,
            "live_long": lon
        })
    
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import (
    Booking, BookingItem,
    Product, VendorProfile,
    MaterialOrder, MaterialOrderItem
)
from .serializers import ProductSerializer
from .utils import distance_km


# =========================================
# 🔹 1. NEARBY PRODUCTS API
# =========================================
from .models import Product, VendorProfile
from .serializers import ProductSerializer
from .utils import distance_km


class NearbyProductAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get nearby products (within 10km)",
        manual_parameters=[
            openapi.Parameter("lat", openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True),
            openapi.Parameter("lon", openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True),
        ],
        responses={200: ProductSerializer(many=True)},
        tags=["Products"]
    )
    def get(self, request):

        # =========================
        # 1. GET LAT / LON
        # =========================
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")

        if not lat or not lon:
            raise ValidationError({"error": "lat & lon required"})

        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            raise ValidationError({"error": "Invalid coordinates"})

        # =========================
        # 2. FILTER VALID VENDORS
        # =========================
        vendors = VendorProfile.objects.filter(
            is_active=True,
            is_approved=True,
            store_lat__isnull=False,
            store_long__isnull=False
        )

        products = []

        # =========================
        # 3. LOOP VENDORS SAFELY
        # =========================
        for vendor in vendors:

            # extra safety (VERY IMPORTANT)
            if not vendor.store_lat or not vendor.store_long:
                continue

            try:
                distance = distance_km(
                    lat,
                    lon,
                    float(vendor.store_lat),
                    float(vendor.store_long)
                )
            except Exception:
                continue  # skip invalid vendor

            # =========================
            # 4. DISTANCE FILTER
            # =========================
            if distance <= 10:   # you can increase to 20 for testing

                vendor_products = Product.objects.filter(
                    vendor=vendor,
                    stock_quantity__gt=0
                )

                products.extend(vendor_products)

        # =========================
        # 5. REMOVE DUPLICATES
        # =========================
        unique_products = list(set(products))

        # =========================
        # 6. RESPONSE
        # =========================
        serializer = ProductSerializer(unique_products, many=True)

        return Response({
            "count": len(unique_products),
            "products": serializer.data
        })


# =========================================
# 🔹 3. BOOKING SUMMARY (CUSTOMER VIEW)
# =========================================
class BookingSummaryAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get booking total (service + approved products)",
        responses={200: openapi.Response("Booking Summary")},
        tags=["Booking"]
    )
    def get(self, request, booking_id):

        booking = get_object_or_404(Booking, id=booking_id)

        items = booking.items.all()

        product_total = sum([
            item.get_total_price()
            for item in items
            if item.approval_status == "APPROVED"
        ])

        total = booking.service_charge_at_booking + product_total

        return Response({
            "booking_id": booking.id,
            "service_charge": booking.service_charge_at_booking,
            "product_total": product_total,
            "total_amount": total,

            "items": [
                {
                    "item_id": item.id,
                    "product_name": item.product_name,
                    "product_price": item.product_price,
                    "product_image": item.product_image,
                    "quantity": item.quantity,
                    "total_price": item.get_total_price(),
                    "status": item.approval_status   # ✅ shows PENDING
                }
                for item in items
            ]
        })
    

# =========================================
# 🔹 4. CUSTOMER APPROVES PRODUCTS
# =========================================
class ApproveProductsAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Customer Approve / Reject Products (Multi-stage)",
        operation_description="""
Customer approves or rejects pending products in a booking.

🔥 FEATURES:
✔ Supports multi-stage approval  
✔ Only NEW approved items are sent to vendor  
✔ Prevents duplicate orders  
✔ Groups products by vendor  

FLOW:
1. Serviceman adds products → PENDING  
2. Customer approves → order created  
3. Serviceman adds more → again PENDING  
4. Customer approves → ONLY new items processed  

STATUS:
✔ APPROVED → sent to vendor  
❌ REJECTED → ignored  
""",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["status"],
            properties={
                "status": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["APPROVED", "REJECTED"],
                    example="APPROVED"
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Products processed successfully",
                examples={
                    "application/json": {
                        "message": "New items approved and sent to vendor",
                        "orders_created": [12, 13],
                        "total_cost": 1500
                    }
                }
            ),
            400: "Invalid request / No pending items",
            403: "Only customer allowed"
        },
        security=[{"Bearer": []}],
        tags=["Booking - Product Approval"]
    )
    def patch(self, request, booking_id):

        # =========================
        # 1. CHECK CUSTOMER
        # =========================
        if request.user.role != "CUSTOMER":
            return Response({"error": "Only customer allowed"}, status=403)

        booking = get_object_or_404(Booking, id=booking_id)

        if booking.customer.user != request.user:
            return Response({"error": "Not your booking"}, status=403)

        status_value = request.data.get("status")

        if status_value not in ["APPROVED", "REJECTED"]:
            return Response({"error": "Invalid status"}, status=400)

        # =========================
        # 2. GET PENDING ITEMS
        # =========================
        items = booking.items.filter(approval_status="PENDING")

        if not items.exists():
            return Response({"message": "No pending items"}, status=400)

        # =========================
        # 3. UPDATE ITEMS
        # =========================
        for item in items:
            item.approval_status = status_value
            item.save()

        # =========================
        # 4. IF REJECTED
        # =========================
        if status_value == "REJECTED":
            booking.update_total_cost()
            return Response({"message": "Items rejected"})

        # =========================
        # 5. ONLY NEW APPROVED ITEMS
        # =========================
        approved_items = booking.items.filter(
            approval_status="APPROVED",
            is_ordered=False
        )

        if not approved_items.exists():
            return Response({"message": "No new items to order"})

        # =========================
        # 6. GROUP BY VENDOR
        # =========================
        vendor_map = {}

        for item in approved_items:
            vendor = item.product.vendor

            if vendor not in vendor_map:
                vendor_map[vendor] = []

            vendor_map[vendor].append(item)

        orders = []

        # =========================
        # 7. CREATE ORDERS
        # =========================
        for vendor, items_list in vendor_map.items():

            order = MaterialOrder.objects.create(
                booking=booking,
                serviceman=booking.serviceman,
                vendor=vendor,
                status="REQUESTED",
                customer_approve=True
            )

            total = 0

            for item in items_list:

                MaterialOrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price_at_order=item.product_price
                )

                total += item.get_total_price()

                # 🔥 IMPORTANT
                item.is_ordered = True
                item.save()

            order.total_cost = total
            order.save()

            orders.append(order.id)

        booking.update_total_cost()

        return Response({
            "message": "New items approved and sent to vendor",
            "orders_created": orders,
            "total_cost": booking.total_cost
        })
        

class VendorOrderListAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Vendor: View ONLY approved product orders",
        responses={200: "Vendor Orders"},
        tags=["Vendor Orders"]
    )
    def get(self, request):

        if request.user.role != "VENDOR":
            return Response({"error": "Only vendor allowed"}, status=403)

        vendor = get_object_or_404(VendorProfile, user=request.user)

        orders = MaterialOrder.objects.filter(
            vendor=vendor,
            customer_approve=True
        ).order_by("-created_at")

        data = []

        for order in orders:

            # 🔥 AUTO REJECT
            if order.status == "REQUESTED":
                if timezone.now() - order.created_at >= timedelta(minutes=2):
                    order.status = "AUTO_REJECTED"
                    order.save()

            data.append({
                "order_id": order.id,
                "status": order.status,
                "total_cost": order.total_cost,
                "created_at": order.created_at,
            })

        return Response({
            "count": len(data),
            "orders": data
        })
        

# =========================================
# 🔹 MERGED API → ADD PRODUCT + SERVICE CHARGE
# =========================================

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Booking, BookingItem, Product, ServicemanProfile


class AddProductAndServiceChargeAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Serviceman adds product + updates service charge",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["product_id", "quantity", "service_charge"],
            properties={
                "product_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                "quantity": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                "service_charge": openapi.Schema(type=openapi.TYPE_NUMBER, example=200)
            }
        ),
        responses={200: "Product added + service charge updated"},
        tags=["Booking"]
    )

    def post(self, request, booking_id):

        if request.user.role != "SERVICEMAN":
            return Response({"error": "Only serviceman allowed"}, status=403)

        serviceman = get_object_or_404(
            ServicemanProfile,
            user=request.user
        )

        booking = get_object_or_404(
            Booking,
            id=booking_id,
            serviceman=serviceman
        )

        if booking.status not in ["ACCEPTED", "ONGOING"]:
            return Response({"error": "Booking not active"}, status=400)

        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))
        service_charge = request.data.get("service_charge")

        if not product_id:
            return Response({"error": "product_id required"}, status=400)

        if service_charge is None:
            return Response({"error": "service_charge required"}, status=400)

        product = get_object_or_404(Product, id=product_id)

        # ✅ ADD / UPDATE PRODUCT
        item, created = BookingItem.objects.get_or_create(
            booking=booking,
            product=product,
            defaults={
                "quantity": quantity,
                "product_name": product.name,
                "product_price": product.price,
                "product_image": product.image.url if product.image else None,

                # 🔥 IMPORTANT
                "approval_status": "PENDING",

                "product_data": {
                    "id": product.id,
                    "name": product.name,
                    "price": str(product.price),
                    "image": product.image.url if product.image else None,
                }
            }
        )

        if not created:
            item.quantity += quantity

            # 🔥 RESET TO PENDING
            item.approval_status = "PENDING"

            item.save()

        booking.service_charge_at_booking = service_charge
        booking.status = "ONGOING"
        booking.save()

        return Response({
            "message": "Product added successfully",
            "product": product.name,
            "quantity": item.quantity,
            "status": item.approval_status
        })


class UpdateProductAndServiceChargeAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Serviceman updates product quantity + service charge (ONLY HIS BOOKING)",
        operation_description="""
✔ Update:
- Product quantity
- Service charge

❌ Restrictions:
- Only assigned serviceman
- Only his booking
- Booking must be ACCEPTED or ONGOING
""",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["product_id"],
            properties={
                "product_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    example=5
                ),
                "quantity": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    example=3,
                    description="New quantity (0 = remove product)"
                ),
                "service_charge": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    example=250
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Updated successfully",
                examples={
                    "application/json": {
                        "message": "Booking updated successfully",
                        "booking_id": 12,
                        "product": "Pipe",
                        "quantity": 3,
                        "service_charge": 250,
                        "status": "ONGOING"
                    }
                }
            ),
            400: "Bad request",
            403: "Forbidden",
            404: "Not found"
        },
        security=[{"Bearer": []}],
        tags=["Booking"]
    )
    def patch(self, request, booking_id):

        # =========================
        # 1. ROLE CHECK
        # =========================
        if request.user.role != "SERVICEMAN":
            return Response({"error": "Only serviceman allowed"}, status=403)

        # =========================
        # 2. GET SERVICEMAN
        # =========================
        serviceman = get_object_or_404(
            ServicemanProfile,
            user=request.user
        )

        # =========================
        # 3. ONLY HIS BOOKING
        # =========================
        booking = get_object_or_404(
            Booking,
            id=booking_id,
            serviceman=serviceman
        )

        # =========================
        # 4. STATUS CHECK
        # =========================
        if booking.status not in ["ACCEPTED", "ONGOING"]:
            return Response({
                "error": "Booking not editable"
            }, status=400)

        # =========================
        # 5. GET DATA
        # =========================
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity")
        service_charge = request.data.get("service_charge")

        if not product_id:
            return Response({"error": "product_id required"}, status=400)

        product = get_object_or_404(Product, id=product_id)

        item = get_object_or_404(
            BookingItem,
            booking=booking,
            product=product
        )

        # =========================
        # 6. UPDATE PRODUCT
        # =========================
        if quantity is not None:
            quantity = int(quantity)

            if quantity <= 0:
                item.delete()
            else:
                item.quantity = quantity
                item.save()

        # =========================
        # 7. UPDATE SERVICE CHARGE
        # =========================
        if service_charge is not None:
            booking.service_charge_at_booking = service_charge

        booking.save()

        # =========================
        # 8. RESPONSE
        # =========================
        return Response({
            "message": "Booking updated successfully",
            "booking_id": booking.id,
            "product": product.name,
            "quantity": quantity,
            "service_charge": booking.service_charge_at_booking,
            "status": booking.status
        })        




class CreatePaymentIntentAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Create Payment Intent",
        operation_description="Create Stripe payment for booking",
        security=[{"Bearer": []}],
        tags=["Payment"]
    )
    def post(self, request, booking_id):

        # =========================
        # 1. ROLE CHECK
        # =========================
        if request.user.role != "CUSTOMER":
            return Response({"error": "Only customer can pay"}, status=403)

        # =========================
        # 2. GET BOOKING
        # =========================
        booking = get_object_or_404(Booking, id=booking_id)

        if booking.customer.user != request.user:
            return Response({"error": "Unauthorized"}, status=403)

        # =========================
        # 3. VALIDATION
        # =========================
        if booking.status != "PENDING_PAYMENT":
            return Response({"error": "Invalid booking state"}, status=400)

        if booking.payment_status == "PAID":
            return Response({"error": "Booking already paid"}, status=400)

        if booking.total_cost <= 0:
            return Response({"error": "Invalid booking amount"}, status=400)

        # =========================
        # 4. STRIPE AMOUNT
        # =========================
        amount = int(booking.total_cost * 100)  # INR → paise

        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency="inr",
                metadata={
                    "booking_id": str(booking.id),
                    "customer_id": str(request.user.id)
                }
            )
        except Exception as e:
            return Response({
                "error": "Stripe error",
                "details": str(e)
            }, status=500)

        # =========================
        # 5. SAVE PAYMENT RECORD
        # =========================
        Payment.objects.create(
            booking=booking,
            customer=booking.customer,
            amount=booking.total_cost,
            status="PENDING",
            gateway_order_id=intent.id
        )

        # =========================
        # 6. RESPONSE
        # =========================
        return Response({
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
            "amount": amount,
            "currency": "INR",
            "public_key": settings.STRIPE_PUBLIC_KEY
        })


class VerifyStripePaymentAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Verify Stripe Payment (Swagger Test Mode)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["payment_intent_id"],
            properties={
                "payment_intent_id": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example="pi_3Nxxxxxxx"
                ),
                "force_success": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    example=True,
                    description="FOR TESTING ONLY (Swagger)"
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Payment success",
                examples={
                    "application/json": {
                        "message": "Payment successful",
                        "booking_id": 65,
                        "booking_status": "PENDING",
                        "payment_status": "PAID"
                    }
                }
            )
        },
        security=[{"Bearer": []}],
        tags=["Payment"]
    )
    def post(self, request, booking_id):

        payment_intent_id = request.data.get("payment_intent_id")
        force_success = request.data.get("force_success", False)

        if not payment_intent_id:
            return Response({"error": "payment_intent_id required"}, status=400)

        booking = get_object_or_404(Booking, id=booking_id)

        if booking.customer.user != request.user:
            return Response({"error": "Unauthorized"}, status=403)

        # 🔥 FIXED QUERY (NO status filter)
        payment = Payment.objects.filter(
            booking=booking,
            gateway_order_id=payment_intent_id
        ).first()

        if not payment:
            return Response({"error": "Payment not found"}, status=404)

        # =========================
        # 🔥 SWAGGER FORCE MODE
        # =========================
        if force_success:

            payment.status = "PAID"
            payment.gateway_payment_id = payment_intent_id
            payment.paid_at = timezone.now()
            payment.save()

            booking.payment_status = "PAID"
            booking.status = "PENDING"
            booking.save()

            return Response({
                "message": "Payment successful (TEST MODE)",
                "booking_id": booking.id,
                "booking_status": booking.status,
                "payment_status": booking.payment_status
            })

        # =========================
        # REAL STRIPE VERIFY
        # =========================
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        except Exception as e:
            return Response({
                "error": "Stripe error",
                "details": str(e)
            }, status=500)

        if intent.status == "succeeded":

            payment.status = "PAID"
            payment.gateway_payment_id = payment_intent_id
            payment.paid_at = timezone.now()
            payment.save()

            booking.payment_status = "PAID"
            booking.status = "PENDING"
            booking.save()

            return Response({
                "message": "Payment successful",
                "booking_id": booking.id,
                "booking_status": booking.status,
                "payment_status": booking.payment_status
            })

        return Response({
            "error": "Payment not completed",
            "stripe_status": intent.status
        }, status=400)        

class BookingPaymentDetailAPI(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_summary="Get booking payment details",
        responses={
            200: openapi.Response(
                description="Booking Payment Details",
                examples={
                    "application/json": {
                        "booking_id": 12,
                        "payment_status": "PAID"
                    }
                }
            ),
            404: "Booking not found"
        },
        security=[{"Bearer": []}],
        tags=["Payment"]
    )
    def get(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
            return Response({
                "booking_id": booking.id,
                "payment_status": booking.payment_status,
            }, status=200)
        except Booking.DoesNotExist:

            return Response({"detail": "Booking not found"}, status=404)





class VendorTrackingAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Step-by-Step Vendor Tracking",
        operation_description="""
🔥 FLOW:

1. Customer approves all products
2. Vendors accept orders
3. Tracking starts

✔ Behavior:
- Shows ONLY NEXT nearest vendor
- After collection → next vendor shown
- AUTO_REJECTED → ignored
- PENDING → blocks tracking

📍 Result:
- Step-by-step vendor pickup
""",
        manual_parameters=[
            openapi.Parameter(
                'booking_id',
                openapi.IN_PATH,
                description="Booking ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Next Vendor",
                examples={
                    "application/json": {
                        "booking_id": 101,
                        "status": "COLLECTION_IN_PROGRESS",
                        "next_vendor": {
                            "order_id": 12,
                            "vendor_id": 5,
                            "vendor_name": "ABC Hardware",
                            "distance_km": 1.2
                        }
                    }
                }
            ),
            400: "Tracking not allowed",
            403: "Unauthorized"
        },
        security=[{"Bearer": []}],
        tags=["Vendor Tracking"]
    )
    def get(self, request, booking_id):

        # =========================
        # 🔹 GET BOOKING
        # =========================
        booking = get_object_or_404(
            Booking.objects.select_related(
                "customer__user",
                "serviceman__user"
            ),
            id=booking_id
        )

        # =========================
        # 🔒 ACCESS CONTROL
        # =========================
        if request.user.role == "CUSTOMER":
            if booking.customer.user != request.user:
                return Response({"error": "Unauthorized"}, status=403)

        elif request.user.role == "SERVICEMAN":
            if booking.serviceman.user != request.user:
                return Response({"error": "Unauthorized"}, status=403)

        else:
            return Response({"error": "Access not allowed"}, status=403)

        # =========================
        # 🔹 PRODUCT APPROVAL CHECK
        # =========================
        items = booking.items.all()

        if items.filter(approval_status="PENDING").exists():
            return Response({
                "error": "All products must be approved first"
            }, status=400)

        # =========================
        # 🔹 GET ORDERS
        # =========================
        orders = booking.material_orders.all()

        if not orders.exists():
            return Response({
                "error": "No vendor orders found"
            }, status=400)

        accepted_orders = []

        for order in orders:

            # 🔥 AUTO REJECT AFTER 2 MIN
            if order.status == "PENDING":
                if timezone.now() - order.created_at >= timedelta(minutes=2):
                    order.status = "AUTO_REJECTED"
                    order.save()

            # ❌ BLOCK IF STILL PENDING
            if order.status == "PENDING":
                return Response({
                    "error": "Waiting for vendor response"
                }, status=400)

            # ✅ ONLY ACCEPTED
            if order.status == "VENDOR_ACCEPTED":
                accepted_orders.append(order)

        # =========================
        # 🔹 FILTER NOT COLLECTED
        # =========================
        active_orders = [
            order for order in accepted_orders if not order.is_collected
        ]

        # =========================
        # 🔹 ALL DONE
        # =========================
        if not active_orders:
            return Response({
                "booking_id": booking.id,
                "status": "ALL_COLLECTED",
                "message": "All vendor items collected"
            })

        # =========================
        # 🔹 CUSTOMER LOCATION
        # =========================
        if not booking.customer.default_lat or not booking.customer.default_long:
            return Response({
                "error": "Customer location missing"
            }, status=400)

        customer_lat = float(booking.customer.default_lat)
        customer_lon = float(booking.customer.default_long)

        # =========================
        # 🔹 FIND NEAREST VENDOR
        # =========================
        nearest_vendor = None
        min_distance = float("inf")

        for order in active_orders:
            vendor = order.vendor

            if not vendor.store_lat or not vendor.store_long:
                continue

            dist = distance_km(
                customer_lat,
                customer_lon,
                float(vendor.store_lat),
                float(vendor.store_long)
            )

            if dist < min_distance:
                min_distance = dist
                nearest_vendor = {
                    "order_id": order.id,
                    "vendor_id": vendor.user.id,
                    "vendor_name": vendor.business_name,
                    "vendor_lat": vendor.store_lat,
                    "vendor_long": vendor.store_long,
                    "distance_km": round(dist, 2)
                }

        # =========================
        # 🔹 FINAL RESPONSE
        # =========================
        return Response({
            "booking_id": booking.id,
            "status": "COLLECTION_IN_PROGRESS",
            "next_vendor": nearest_vendor
        })

class MarkVendorCollectedAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Mark Vendor Items as Collected",
        manual_parameters=[
            openapi.Parameter(
                'order_id',
                openapi.IN_PATH,
                description="Material Order ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        tags=["Vendor Tracking"]
    )
    def patch(self, request, order_id):

        if request.user.role != "SERVICEMAN":
            return Response({"error": "Only serviceman allowed"}, status=403)

        order = get_object_or_404(MaterialOrder, id=order_id)

        if order.status != "VENDOR_ACCEPTED":
            return Response({
                "error": "Order not accepted"
            }, status=400)

        if order.is_collected:
            return Response({
                "message": "Already collected"
            })

        order.is_collected = True
        order.save()

        return Response({
            "message": "Vendor items collected successfully",
            "order_id": order.id
        })



class VendorAcceptOrderAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Vendor Accept Order (Auto Reject after 2 min)",
        operation_description="""
✔ Vendor can ONLY ACCEPT  
❌ No manual reject  

⏱ If vendor does not accept within 2 minutes → AUTO_REJECT  

Rules:
- After auto reject → cannot accept
- Only REQUESTED orders can be accepted
""",
        responses={
            200: openapi.Response(
                description="Order accepted",
                examples={
                    "application/json": {
                        "message": "Order accepted successfully",
                        "order_id": 10,
                        "status": "VENDOR_ACCEPTED"
                    }
                }
            ),
            400: "Expired or invalid order",
            403: "Unauthorized"
        },
        tags=["Vendor Orders"]
    )
    def patch(self, request, order_id):

        # =========================
        # 🔒 ROLE CHECK
        # =========================
        if request.user.role != "VENDOR":
            return Response({"error": "Only vendor allowed"}, status=403)

        vendor = get_object_or_404(VendorProfile, user=request.user)

        order = get_object_or_404(MaterialOrder, id=order_id, vendor=vendor)

        # =========================
        # 🔥 AUTO REJECT CHECK
        # =========================
        if order.status == "REQUESTED":
            if timezone.now() - order.created_at >= timedelta(minutes=2):
                order.status = "AUTO_REJECTED"
                order.save()

        # =========================
        # ❌ BLOCK AFTER AUTO REJECT
        # =========================
        if order.status == "AUTO_REJECTED":
            return Response({
                "error": "Order auto rejected (time expired)"
            }, status=400)

        # =========================
        # ❌ BLOCK IF ALREADY ACCEPTED
        # =========================
        if order.status == "VENDOR_ACCEPTED":
            return Response({
                "error": "Order already accepted"
            }, status=400)

        # =========================
        # ✅ ACCEPT ORDER
        # =========================
        if order.status != "REQUESTED":
            return Response({
                "error": "Invalid order state"
            }, status=400)

        order.status = "VENDOR_ACCEPTED"
        order.save()

        # =========================
        # 🔥 UPDATE BOOKING TOTAL
        # =========================
        if order.booking:
            order.booking.update_total_cost()

        return Response({
            "message": "Order accepted successfully",
            "order_id": order.id,
            "status": order.status
        })
import profile
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from django.conf import settings
import stripe
import cloudinary
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Booking, BookingItem, Payment, User, CustomerProfile, ServicemanProfile, VendorProfile, EmailOTP,Category,Service,Product
from .serializers import (
    BookingCreateSerializer,
    SendOTPSerializer,
    VendorNearbySerializer,
    VerifyOTPSerializer,
    CompleteRegisterSerializer,
    UserProfileSerializer,
    LogoutSerializer,
    VendorProfileSerializer,
    ServicemanProfileSerializer,
    CustomerProfileSerializer,
    ProfileResponseSerializer,
    UniversalProfileUpdateSerializer,
    CategorySerializer,
    ServicemanSerializer,
    VerifyStripePaymentSerializer
)
from .utils import send_email_otp, verify_email_otp
from rest_framework import request, status
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .permissions import IsAdminOrCustomer
from .utils import delete_cloudinary_image

def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }

from .serializers import EmailPasswordLoginSerializer
from django.contrib.auth import authenticate

stripe.api_key = settings.STRIPE_SECRET_KEY
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

    @swagger_auto_schema(request_body=LogoutSerializer)
    def post(self, request):
        response = Response(
            {"success": True, "message": "Logged out successfully"}
        )

        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return response



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
    parser_classes = (MultiPartParser, FormParser)
    @swagger_auto_schema(
    request_body=CustomerProfileSerializer,
    consumes=["multipart/form-data"],
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
    parser_classes = (MultiPartParser, FormParser)    

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
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        request_body=VendorProfileSerializer,
        consumes=["multipart/form-data"],
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
    parser_classes = (MultiPartParser, FormParser)
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
    parser_classes = (MultiPartParser, FormParser)
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
    parser_classes = (MultiPartParser, FormParser)
    @swagger_auto_schema(
    request_body=CustomerProfileSerializer,
    consumes=["multipart/form-data"],
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
    parser_classes = (MultiPartParser, FormParser)
    @swagger_auto_schema(
        request_body=ServicemanProfileSerializer,
        consumes=["multipart/form-data"],
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
    parser_classes = (MultiPartParser, FormParser)
    @swagger_auto_schema(
        request_body=VendorProfileSerializer,
        consumes=["multipart/form-data"],
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



#=============Soft Delete APIs for Service and Product =============#
class ServiceSoftDeleteAPI(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, pk):
        service = get_object_or_404(Service, pk=pk)
        service.is_active = False
        service.save()
        return Response({"message": "Service soft deleted"})


class ProductSoftDeleteAPI(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.is_active = False
        product.save()
        return Response({"message": "Product soft deleted"})

#=============Nearby Servicemen API =============#
from rest_framework.exceptions import ValidationError
from .utils import distance_km
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Serviceman

class NearbyServicemanAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get All Servicemen Within 10km",
        manual_parameters=[
            openapi.Parameter("lat", openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True),
            openapi.Parameter("lon", openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True),
        ],
        responses={200: ServicemanProfileSerializer(many=True)},
        security=[{"Bearer": []}],
        tags=["Servicemen"]
    )
    def get(self, request):

        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")

        if not lat or not lon:
            raise ValidationError({"detail": "Latitude and longitude are required"})

        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            raise ValidationError({"detail": "Invalid latitude or longitude"})

        queryset = ServicemanProfile.objects.select_related("user").filter(
            is_active=True,
            is_approved=True,
            current_lat__isnull=False,
            current_long__isnull=False
        )

        nearby = []

        for profile in queryset:
            distance = distance_km(
                lat,
                lon,
                float(profile.current_lat),
                float(profile.current_long)
            )

            if distance <= 10:
                nearby.append(profile)

        serializer = ServicemanProfileSerializer(nearby, many=True)
        return Response(serializer.data)




class CategoryNearbyServicemanAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get Category Based Servicemen Within 10km",
        manual_parameters=[
            openapi.Parameter("lat", openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True),
            openapi.Parameter("lon", openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True),
            openapi.Parameter(
                "category",
                openapi.IN_QUERY,
                description="Category name (Example: Plumbing)",
                type=openapi.TYPE_STRING,
                required=True
            ),
        ],
        responses={200: ServicemanProfileSerializer(many=True)},
        security=[{"Bearer": []}],
        tags=["Servicemen"]
    )
    def get(self, request):

        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")
        category = request.query_params.get("category")

        if not lat or not lon or not category:
            raise ValidationError({"detail": "Latitude, longitude and category are required"})

        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            raise ValidationError({"detail": "Invalid latitude or longitude"})

        queryset = ServicemanProfile.objects.select_related("user").filter(
            is_active=True,
            is_approved=True,
            skills__contains=[category],   # 🔥 CATEGORY = SKILL
            current_lat__isnull=False,
            current_long__isnull=False
        )

        nearby = []

        for profile in queryset:
            distance = distance_km(
                lat,
                lon,
                float(profile.current_lat),
                float(profile.current_long)
            )

            if distance <= 10:
                nearby.append(profile)

        serializer = ServicemanProfileSerializer(nearby, many=True)
        return Response(serializer.data)



#----------------Servicemen List API-----------------

class ServicemenListAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrCustomer]

    @swagger_auto_schema(
        operation_summary="List Approved & Active Servicemen (within 10km)",
        manual_parameters=[
            openapi.Parameter(
                "lat",
                openapi.IN_QUERY,
                description="Latitude",
                type=openapi.TYPE_NUMBER,
                required=True,
            ),
            openapi.Parameter(
                "lon",
                openapi.IN_QUERY,
                description="Longitude",
                type=openapi.TYPE_NUMBER,
                required=True,
            ),
            openapi.Parameter(
                "category",
                openapi.IN_QUERY,
                description="Filter by category name",
                type=openapi.TYPE_STRING,
                required=False,
            )
        ],
        responses={200: ServicemanSerializer(many=True)},
        security=[{"Bearer": []}],
        tags=["Servicemen"]
    )
    def get(self, request):

        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")
        category = request.query_params.get("category")

        if not lat or not lon:
            raise ValidationError({"detail": "Latitude and longitude are required"})

        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            raise ValidationError({"detail": "Latitude and longitude must be numbers"})

        queryset = Serviceman.objects.filter(
            is_active=True,
            servicemanprofile__is_active=True,
            servicemanprofile__is_approved=True
        )

        if category:
            queryset = queryset.filter(category__name__iexact=category)

        nearby = []

        for serviceman in queryset:
            distance = distance_km(lat, lon, serviceman.latitude, serviceman.longitude)

            if distance <= 10:
                nearby.append(serviceman)

        serializer = ServicemanSerializer(nearby, many=True)
        return Response(serializer.data)
    
from .permissions import IsAdminRole
class AdminServicemanControlAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]
    @swagger_auto_schema(
    operation_summary="Admin: Approve / Deactivate Serviceman",
    operation_description="""
Admin can:

• Approve Serviceman (is_approved = true)
• Deactivate Serviceman (is_active = false)
• Reactivate Serviceman (is_active = true)

Only ADMIN role allowed.
""",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "is_approved": openapi.Schema(
                type=openapi.TYPE_BOOLEAN,
                description="Approve or reject serviceman"
            ),
            "is_active": openapi.Schema(
                type=openapi.TYPE_BOOLEAN,
                description="Activate or deactivate serviceman"
            ),
        },
        example={
            "is_approved": True,
            "is_active": True
        }
    ),
    responses={
        200: openapi.Response(
            description="Serviceman updated successfully",
            examples={
                "application/json": {
                    "id": 5,
                    "is_approved": True,
                    "is_active": True,
                    "message": "Serviceman updated successfully"
                }
            }
        ),
        404: "Serviceman not found",
        403: "Admin access required"
    },
    security=[{"Bearer": []}],
    tags=["Admin - Serviceman Control"]
)

    
    def patch(self, request, pk):
        profile = get_object_or_404(
            ServicemanProfile,
            pk=pk,

        )

        allowed_fields = ["is_approved", "is_active"]

        for field in allowed_fields:
            if field in request.data:
                setattr(profile, field, request.data[field])

        profile.save()

        return Response({
            "id": profile.pk,
            "is_approved": profile.is_approved,
            "is_active": profile.is_active,
            "message": "Serviceman updated successfully"
        })
    def delete(self, request, pk):
        profile = get_object_or_404(
            ServicemanProfile,
            pk=pk,
            is_active=True
        )

        profile.is_active = False
        profile.save()

        return Response({
            "id": profile.pk,
            "message": "Serviceman soft deleted successfully"
        })    

class AdminVendorControlAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
    operation_summary="Admin: Approve / Deactivate Vendor",
    operation_description="""
Admin can:

• Approve Vendor (is_approved = true)
• Deactivate Vendor (is_active = false)
• Reactivate Vendor (is_active = true)

Only ADMIN role allowed.
""",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "is_approved": openapi.Schema(
                type=openapi.TYPE_BOOLEAN,
                description="Approve or reject vendor"
            ),
            "is_active": openapi.Schema(
                type=openapi.TYPE_BOOLEAN,
                description="Activate or deactivate vendor"
            ),
        },
        example={
            "is_approved": True,
            "is_active": True
        }
    ),
    responses={
        200: openapi.Response(
            description="Vendor updated successfully",
            examples={
                "application/json": {
                    "id": 3,
                    "is_approved": True,
                    "is_active": True,
                    "message": "Vendor updated successfully"
                }
            }
        )
    },
    security=[{"Bearer": []}],
    tags=["Admin - Vendor Control"]
)
    def patch(self, request, pk):
        profile = get_object_or_404(
            VendorProfile,
            pk=pk,
            is_active=True
        )

        allowed_fields = ["is_approved", "is_active"]

        for field in allowed_fields:
            if field in request.data:
                setattr(profile, field, request.data[field])

        profile.save()

        return Response({
            "id": profile.pk,
            "is_approved": profile.is_approved,
            "is_active": profile.is_active,
            "message": "Vendor updated successfully"
        })

    def delete(self, request, pk):
        profile = get_object_or_404(
            VendorProfile,
            pk=pk,
            is_active=True
        )

        profile.is_active = False
        profile.save()

        return Response({
            "id": profile.pk,
            "message": "Vendor soft deleted successfully"
        })


class PendingVendorsAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
    operation_summary="Admin: List Pending Vendors",
    operation_description="""
Returns all vendors where:
- is_approved = False
- is_active = True
""",
    responses={
        200: VendorProfileSerializer(many=True)
    },
    security=[{"Bearer": []}],
    tags=["Admin - Approval"]
)
    def get(self, request):
        vendors = VendorProfile.objects.filter(
            is_approved=False,
            is_active=True
        )

        serializer = VendorProfileSerializer(vendors, many=True)
        return Response(serializer.data)
    
class PendingServicemenAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
    operation_summary="Admin: List Pending Servicemen",
    operation_description="""
Returns all servicemen where:
- is_approved = False
- is_active = True
""",
    responses={
        200: ServicemanProfileSerializer(many=True)
    },
    security=[{"Bearer": []}],
    tags=["Admin - Approval"]
)
    def get(self, request):
        servicemen = ServicemanProfile.objects.filter(
            is_approved=False,
            is_active=True
        )

        serializer = ServicemanProfileSerializer(servicemen, many=True)
        return Response(serializer.data)


class AdminCustomerListAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_summary="Admin: Get All Customers",
        operation_description="Returns all users with role CUSTOMER.",
        responses={200: UserProfileSerializer(many=True)},
        security=[{"Bearer": []}],
        tags=["Admin - Users"]
    )
    def get(self, request):
        customers = User.objects.filter(role="CUSTOMER")
        serializer = UserProfileSerializer(customers, many=True)
        return Response(serializer.data)



class AdminServicemanListAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_summary="Admin: Get All Servicemen",
        operation_description="Returns all servicemen with profile details.",
        responses={200: ServicemanProfileSerializer(many=True)},
        security=[{"Bearer": []}],
        tags=["Admin - Users"]
    )
    def get(self, request):
        servicemen = ServicemanProfile.objects.select_related("user")
        serializer = ServicemanProfileSerializer(servicemen, many=True)
        return Response(serializer.data)
    

class AdminVendorListAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_summary="Admin: Get All Vendors",
        operation_description="Returns all vendor profiles.",
        responses={200: VendorProfileSerializer(many=True)},
        security=[{"Bearer": []}],
        tags=["Admin - Users"]
    )
    def get(self, request):
        vendors = VendorProfile.objects.select_related("user")
        serializer = VendorProfileSerializer(vendors, many=True)
        return Response(serializer.data)    
    


class NearbyVendorAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get Nearby Vendors Within 10km",
        manual_parameters=[
            openapi.Parameter("lat", openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True),
            openapi.Parameter("lon", openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True),
        ],
        responses={200: VendorNearbySerializer(many=True)},
        security=[{"Bearer": []}],
        tags=["Vendors"]
    )
    def get(self, request):

        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")

        if not lat or not lon:
            raise ValidationError({"detail": "Latitude and longitude required"})

        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            raise ValidationError({"detail": "Invalid coordinates"})

        queryset = VendorProfile.objects.filter(
            is_active=True,
            is_approved=True,
            store_lat__isnull=False,
            store_long__isnull=False
        )

        nearby = []

        for vendor in queryset:
            distance = distance_km(
                lat,
                lon,
                float(vendor.store_lat),
                float(vendor.store_long)
            )

            if distance <= 10:
                nearby.append(vendor)

        serializer = VendorNearbySerializer(nearby, many=True)
        return Response(serializer.data)    
    

# ================= BOOKING APIs =================
#=============Booking Creation API =============#
from .serializers import BookingCreateSerializer, BookingDetailSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
import cloudinary.uploader
from decimal import Decimal

class BookingCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        operation_summary="Create Booking (Payment Required)",
        operation_description="""
Create booking → Payment required before activation.

Flow:
1. Booking created → PENDING_PAYMENT
2. Customer pays
3. Booking becomes ACTIVE
""",
        request_body=BookingCreateSerializer,
        consumes=["multipart/form-data"],
        manual_parameters=[
            openapi.Parameter(
                name="images",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                description="Upload multiple images",
                required=False,
            )
        ],
        responses={
            201: openapi.Response(
                description="Booking created",
                examples={
                    "application/json": {
                        "message": "Booking created. Please complete payment",
                        "booking_id": 1,
                        "booking_status": "PENDING_PAYMENT",
                        "payment_status": "PENDING",
                        "amount": 500
                    }
                }
            )
        },
        security=[{"Bearer": []}],
        tags=["Booking"]
    )
    def post(self, request):

        serializer = BookingCreateSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        booking = serializer.save()

        # 🔥 FORCE PAYMENT FIRST
        booking.status = "PENDING_PAYMENT"
        booking.payment_status = "PENDING"
        booking.save()

        # IMAGE UPLOAD
        files = request.FILES.getlist("images")
        image_urls = []

        for file in files:
            result = cloudinary.uploader.upload(
                file,
                folder=f"home_fixer/bookings/{booking.id}/"
            )
            image_urls.append(result.get("secure_url"))

        booking.image_urls = (booking.image_urls or []) + image_urls
        booking.save()

        return Response({
            "message": "Booking created. Please complete payment",
            "booking_id": booking.id,
            "booking_status": booking.status,
            "payment_status": booking.payment_status,
            "amount": booking.total_cost,
            "image_urls": booking.image_urls
        }, status=201)


class BookingDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get booking details",
        tags=["Bookings"],
        security=[{"Bearer": []}],
    )
    def get(self, request, booking_id):

        try:
            booking = Booking.objects.select_related(
                "serviceman",
                "customer"
            ).get(id=booking_id)

        except Booking.DoesNotExist:
            return Response(
                {"error": "Booking not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # CUSTOMER can see only their booking
        if request.user.role == "CUSTOMER":
            if booking.customer.user != request.user:
                return Response(
                    {"error": "You cannot view this booking"},
                    status=403
                )

        # SERVICEMAN can see only assigned booking
        if request.user.role == "SERVICEMAN":
            if booking.serviceman.user != request.user:
                return Response(
                    {"error": "You are not assigned to this booking"},
                    status=403
                )

        serializer = BookingDetailSerializer(booking)

        return Response(serializer.data)
# ================= SERVICE Booking =================

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Booking, ServicemanProfile

class ServicemanBookingActionAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Serviceman Accept / Reject Booking",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "action": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["accept", "reject"]
                )
            }
        ),
        responses={200: "Success"},
        security=[{"Bearer": []}],
        tags=["Booking"]
    )
    def patch(self, request, booking_id):

        if request.user.role != "SERVICEMAN":
            return Response({"error": "Only serviceman"}, status=403)

        booking = get_object_or_404(Booking, pk=booking_id)

        serviceman = get_object_or_404(
            ServicemanProfile,
            user=request.user
        )

        if booking.serviceman != serviceman:
            return Response({"error": "Not assigned"}, status=403)

        # 🔥 PAYMENT CHECK
        if booking.payment_status != "PAID":
            return Response({"error": "Payment not completed"}, status=400)

        if booking.status != "PENDING":
            return Response({"error": "Invalid booking state"}, status=400)

        action = request.data.get("action")

        if action == "accept":
            booking.status = "ACCEPTED"

        elif action == "reject":
            booking.status = "CANCELLED"

        else:
            return Response({"error": "Invalid action"}, status=400)

        booking.save()

        return Response({
            "message": f"Booking {action}ed successfully",
            "status": booking.status
        })


class CustomerCancelBookingAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Customer: Cancel Booking",
        operation_description="""Customer can cancel a booking.
        - Only bookings in PENDING status can be cancelled
        - Cancelling sets status to CANCELLED
        Only the booking owner can perform this action.""",
        responses={
            200: openapi.Response(
                description="Booking cancelled successfully",
                examples={
                    "application/json": {
                        "message": "Booking cancelled successfully",
                        "status": "CANCELLED"
                    }
                }
            ),
            400: "Booking cannot be cancelled",
            403: "Only booking owner can cancel this booking"
        },
        security=[{"Bearer": []}],
        tags=["Booking - Customer Actions"]
    )

    def patch(self, request, booking_id):

        if request.user.role != "CUSTOMER":
            return Response(
                {"detail": "Only customer can cancel booking"},
                status=403
            )

        booking = get_object_or_404(Booking, pk=booking_id)

        # check ownership
        if booking.customer.user != request.user:
            return Response(
                {"detail": "This booking does not belong to you"},
                status=403
            )

        # cancellation rules
        if booking.status in ["ONGOING", "COMPLETED", "CANCELLED"]:
            return Response(
                {"detail": "This booking cannot be cancelled"},
                status=400
            )

        booking.status = "CANCELLED"
        booking.save()

        return Response({
            "message": "Booking cancelled successfully",
            "status": booking.status
        })            



from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Product, VendorProfile
from .serializers import ProductSerializer


class ProductCreateAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser) 
    @swagger_auto_schema(
        request_body=ProductSerializer,
        responses={201: ProductSerializer},
        security=[{"Bearer": []}],
        tags=["Products - Admin & Vendor"]
    )
    def post(self, request):

        if request.user.role not in ["ADMIN", "VENDOR"]:
            return Response(
                {"detail": "Only admin or vendor can create product"},
                status=403
            )

        data = request.data.copy()

        # Vendor → auto assign vendor
        if request.user.role == "VENDOR":
            vendor = get_object_or_404(VendorProfile, user=request.user)
            data["vendor"] = vendor.pk

        # Admin → must provide vendor
        if request.user.role == "ADMIN" and "vendor" not in data:
            return Response(
                {"detail": "Admin must provide vendor id"},
                status=400
            )

        serializer = ProductSerializer(
    data=data,
    context={"request": request}
)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=201)
    
class ProductListAPI(APIView):
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        operation_summary="Get All Available Products",
        operation_description="Returns all products with stock_quantity > 0.",
        responses={200: ProductSerializer(many=True)},
        tags=["Products"]
    )

    def get(self, request):

        products = Product.objects.filter(stock_quantity__gt=0)

        serializer = ProductSerializer(products, many=True)

        return Response(serializer.data)


class ProductUpdateAPI(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        request_body=ProductSerializer,
        responses={200: ProductSerializer},
        security=[{"Bearer": []}],
        tags=["Products - Admin & Vendor"]
    )
    def put(self, request, pk):

        product = get_object_or_404(Product, pk=pk)

        # Only admin or owner vendor
        if request.user.role == "VENDOR":
            if product.vendor.user != request.user:
                return Response(
                    {"detail": "You can update only your products"},
                    status=403
                )

        elif request.user.role != "ADMIN":
            return Response(
                {"detail": "Not allowed"},
                status=403
            )

        serializer = ProductSerializer(
            product,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
    


class ProductDeleteAPI(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_summary="Delete Product (Admin or Owner Vendor)",
        operation_description="Deletes a product. Only the owning vendor or admin can delete.",
        responses={
            200: openapi.Response(
                description="Product deleted successfully",
                examples={
                    "application/json": {
                        "message": "Product deleted successfully"
                    }
                }
            ),
            403: "Not allowed to delete this product",
            404: "Product not found"
        },
        security=[{"Bearer": []}],
        tags=["Products - Admin & Vendor"]
    )
    def delete(self, request, pk):

        product = get_object_or_404(Product, pk=pk)

        if request.user.role == "VENDOR":
            if product.vendor.user != request.user:
                return Response({"detail": "You can delete only your products"}, status=403)

        elif request.user.role != "ADMIN":
            return Response({"detail": "Not allowed"}, status=403)

        # Delete image from Cloudinary
        if product.image:
            delete_cloudinary_image(product.image)
            try:
                if hasattr(product.image, "public_id"):
                    cloudinary.uploader.destroy(product.image.public_id)
            except Exception:
                pass

        product.delete()

        return Response({"message": "Product deleted successfully"})


class CategoryAPIView(APIView):

    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_summary="Get All Categories / Create Category",
        operation_description="GET returns all categories. POST creates a new category (Admin only).",
        request_body=CategorySerializer,
        responses={
            200: CategorySerializer(many=True),
            201: CategorySerializer,
            403: "Only admin can create category"
        },
        security=[{"Bearer": []}],
        tags=["Categories"]
    )
    def get(self, request):

        categories = Category.objects.all()

        serializer = CategorySerializer(categories, many=True)

        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Create Category (Admin only)",
        operation_description="Creates a new category. Only users with ADMIN role can perform this action.",
        request_body=CategorySerializer,
        responses={
            201: CategorySerializer,
            403: "Only admin can create category"
        },
        security=[{"Bearer": []}],
        tags=["Categories"]
    )
    def post(self, request):

        if request.user.role != "ADMIN":
            return Response(
                {"error": "Only admin can create category"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CategorySerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)      



from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Category
from .serializers import CategorySerializer
from .permissions import IsAdminRole
from rest_framework import status

class ProductCategoryAPI(APIView):

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Get all product categories",
        responses={200: CategorySerializer(many=True)},
        tags=["Product Categories"]
    )
    def get(self, request):

        categories = Category.objects.filter(category_type="PRODUCT")

        serializer = CategorySerializer(categories, many=True)

        return Response(serializer.data)


    @swagger_auto_schema(
        operation_summary="Create product category (Admin only)",
        request_body=CategorySerializer,
        responses={201: CategorySerializer},
        security=[{"Bearer": []}],
        tags=["Product Categories"]
    )
    def post(self, request):

        if request.user.role != "ADMIN":
            return Response(
                {"error": "Only admin can create category"},
                status=403
            )

        data = request.data.copy()
        data["category_type"] = "PRODUCT"

        serializer = CategorySerializer(data=data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=201)
    
class ProductCategoryDeleteAPI(APIView):

    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_summary="Delete product category (Admin only)",
        responses={200: "Category deleted"},
        security=[{"Bearer": []}],
        tags=["Product Categories"]
    )

    def delete(self, request, pk):

        category = get_object_or_404(
            Category,
            pk=pk,
            category_type="PRODUCT"
        )

        category.delete()

        return Response({
            "message": "Product category deleted successfully"
        })
#====================SERVICEMAN BOOKING LIST API =================
class ServicemanBookingRequestsAPI(APIView):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Serviceman: View ONLY PAID bookings",
        operation_description="""
🔒 Serviceman can only see bookings AFTER payment.

✔ Only bookings where:
- payment_status = PAID
- assigned to logged-in serviceman

❌ Hidden:
- PENDING_PAYMENT
- FAILED
""",
        responses={
            200: openapi.Response(
                description="List of paid bookings",
                examples={
                    "application/json": {
                        "count": 2,
                        "bookings": [
                            {
                                "id": 65,
                                "status": "PENDING",
                                "payment_status": "PAID",
                                "customer_name": "John Doe",
                                "problem_title": "AC not working"
                            }
                        ]
                    }
                }
            ),
            403: "Only serviceman allowed"
        },
        security=[{"Bearer": []}],
        tags=["Serviceman Bookings"]
    )
    def get(self, request):

        # =========================
        # 1. ROLE CHECK
        # =========================
        if request.user.role != "SERVICEMAN":
            return Response(
                {"error": "Only serviceman can access this"},
                status=403
            )

        # =========================
        # 2. GET SERVICEMAN PROFILE
        # =========================
        serviceman = get_object_or_404(
            ServicemanProfile,
            user=request.user
        )

        # =========================
        # 3. FILTER BOOKINGS (🔥 FIX)
        # =========================
        bookings = Booking.objects.select_related(
            "customer__user",
            "serviceman__user"
        ).filter(
            serviceman=serviceman,
            payment_status="PAID"   # 🔥 ONLY PAID BOOKINGS
        ).order_by("-created_at")

        # =========================
        # 4. SERIALIZE RESPONSE
        # =========================
        response_data = []

        for booking in bookings:
            response_data.append({
                "booking_id": booking.id,
                "status": booking.status,
                "payment_status": booking.payment_status,
                "scheduled_date": booking.scheduled_date,
                "scheduled_time": booking.scheduled_time,
                "problem_title": booking.problem_title,
                "problem_description": booking.problem_description,
                "total_cost": booking.total_cost,
                "created_at": booking.created_at,

                "customer": {
                    "name": booking.customer.user.name,
                    "phone": booking.customer.user.phone,
                }
            })

        # =========================
        # 5. RESPONSE
        # =========================
        return Response({
            "count": len(response_data),
            "bookings": response_data
        })


#=============Booking Tracking API =============#

from .serializers import BookingTrackingSerializer


def get_status_text(status):

    status_map = {
        "PENDING": "Waiting for serviceman to accept",
        "ACCEPTED": "Serviceman accepted your booking",
        "REJECTED": "Serviceman rejected the booking",
        "ONGOING": "Service is currently in progress",
        "COMPLETED": "Service completed successfully",
        "CANCELLED": "Booking was cancelled"
    }

    return status_map.get(status, status)

class BookingTrackingAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Track Booking (Only After Serviceman Accepts)",
        operation_description="""
🚫 Tracking NOT allowed until serviceman accepts booking.

✔ Allowed:
- ACCEPTED
- ONGOING
- COMPLETED

❌ Blocked:
- PENDING (not accepted yet)
- PENDING_PAYMENT
""",
        responses={
            200: openapi.Response(
                description="Tracking data",
                examples={
                    "application/json": {
                        "booking_id": 65,
                        "status": "ONGOING",
                        "status_text": "Service is currently in progress",
                        "serviceman_name": "John",
                        "distance_km": 2.5,
                        "eta_minutes": 5
                    }
                }
            ),
            400: "Tracking not available",
            403: "Unauthorized"
        },
        security=[{"Bearer": []}],
        tags=["Booking Tracking"]
    )
    def get(self, request, booking_id):

        # =========================
        # 1. GET BOOKING
        # =========================
        try:
            booking = Booking.objects.select_related(
                "serviceman__user",
                "customer__user"
            ).get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=404)

        # =========================
        # 2. ACCESS CONTROL
        # =========================
        if request.user.role == "CUSTOMER":
            if booking.customer.user != request.user:
                return Response({"error": "Unauthorized"}, status=403)

        elif request.user.role == "SERVICEMAN":
            if booking.serviceman.user != request.user:
                return Response({"error": "Unauthorized"}, status=403)

        else:
            return Response({"error": "Access not allowed"}, status=403)

        # =========================
        # 🔥 3. PAYMENT CHECK
        # =========================
        if booking.payment_status != "PAID":
            return Response({
                "error": "Tracking not available until payment completed"
            }, status=400)

        # =========================
        # 🔥 4. ACCEPT CHECK (IMPORTANT FIX)
        # =========================
        if booking.status == "PENDING":
            return Response({
                "error": "Tracking not available until serviceman accepts booking"
            }, status=400)

        # =========================
        # 5. SERVICEMAN CHECK
        # =========================
        if not booking.serviceman:
            return Response({"error": "No serviceman assigned yet"}, status=400)

        serviceman = booking.serviceman

        if not (serviceman.live_lat or serviceman.current_lat):
            return Response({"error": "Serviceman location not available"}, status=400)

        if not booking.customer.default_lat or not booking.customer.default_long:
            return Response({"error": "Customer location not available"}, status=400)

        # =========================
        # 6. CALCULATE DISTANCE
        # =========================
        serviceman_lat = float(serviceman.live_lat or serviceman.current_lat)
        serviceman_long = float(serviceman.live_long or serviceman.current_long)

        dist_km = distance_km(
            float(booking.customer.default_lat),
            float(booking.customer.default_long),
            serviceman_lat,
            serviceman_long
        )

        # =========================
        # 7. AUTO ONGOING (ARRIVAL)
        # =========================
        if dist_km < 0.1 and booking.status == "ACCEPTED":
            booking.status = "ONGOING"
            booking.save()

        eta_minutes = round((dist_km / 30) * 60)
        if eta_minutes < 1:
            eta_minutes = 1

        # =========================
        # 8. RESPONSE
        # =========================
        data = {
            "booking_id": booking.id,
            "status": booking.status,
            "status_text": get_status_text(booking.status),
            "serviceman_name": serviceman.user.name or serviceman.user.email,
            "serviceman_rating": float(serviceman.average_rating or 0),
            "serviceman_lat": serviceman.live_lat or serviceman.current_lat,
            "serviceman_long": serviceman.live_long or serviceman.current_long,
            "customer_name": booking.customer.user.name,
            "customer_image": (
                booking.customer.profile_image.url
                if booking.customer.profile_image else None
            ),
            "customer_lat": booking.customer.default_lat,
            "customer_long": booking.customer.default_long,
            "customer_address": booking.customer.default_address or "",
            "distance_km": round(dist_km, 2),
            "eta_minutes": eta_minutes,
            "image_urls": booking.image_urls or []
        }

        serializer = BookingTrackingSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)
    

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class ServicemanLocationUpdateAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Serviceman: Update Live Location",
        operation_description="""
Update real-time location of serviceman.

• Updates `live_lat` and `live_long`
• Used for tracking and ETA
• Does NOT affect base location (current_lat, current_long)
""",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["lat", "lon"],
            properties={
                "lat": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    format=openapi.FORMAT_FLOAT,
                    example=21.7051,
                    description="Latitude"
                ),
                "lon": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    format=openapi.FORMAT_FLOAT,
                    example=72.9959,
                    description="Longitude"
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Live location updated successfully",
                examples={
                    "application/json": {
                        "message": "Live location updated successfully",
                        "live_lat": 21.7051,
                        "live_long": 72.9959
                    }
                }
            ),
            400: "Invalid input",
            403: "Only serviceman allowed"
        },
        security=[{"Bearer": []}],
        tags=["Serviceman Location"]
    )
    def patch(self, request):

        if request.user.role != "SERVICEMAN":
            return Response(
                {"detail": "Only serviceman can update location"},
                status=403
            )

        lat = request.data.get("lat")
        lon = request.data.get("lon")

        if lat is None or lon is None:
            return Response(
                {"detail": "Latitude and longitude required"},
                status=400
            )

        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            return Response(
                {"detail": "Invalid coordinates"},
                status=400
            )

        profile = get_object_or_404(
            ServicemanProfile,
            user=request.user
        )

        # 🔥 Update LIVE location
        profile.live_lat = lat
        profile.live_long = lon
        profile.is_online = True
        profile.save()

        return Response({
            "message": "Live location updated successfully",
            "live_lat": lat,
            "live_long": lon
        })
    
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import (
    Booking, BookingItem,
    Product, VendorProfile,
    MaterialOrder, MaterialOrderItem
)
from .serializers import ProductSerializer
from .utils import distance_km


# =========================================
# 🔹 1. NEARBY PRODUCTS API
# =========================================
from .models import Product, VendorProfile
from .serializers import ProductSerializer
from .utils import distance_km


class NearbyProductAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get nearby products (within 10km)",
        manual_parameters=[
            openapi.Parameter("lat", openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True),
            openapi.Parameter("lon", openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True),
        ],
        responses={200: ProductSerializer(many=True)},
        tags=["Products"]
    )
    def get(self, request):

        # =========================
        # 1. GET LAT / LON
        # =========================
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")

        if not lat or not lon:
            raise ValidationError({"error": "lat & lon required"})

        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            raise ValidationError({"error": "Invalid coordinates"})

        # =========================
        # 2. FILTER VALID VENDORS
        # =========================
        vendors = VendorProfile.objects.filter(
            is_active=True,
            is_approved=True,
            store_lat__isnull=False,
            store_long__isnull=False
        )

        products = []

        # =========================
        # 3. LOOP VENDORS SAFELY
        # =========================
        for vendor in vendors:

            # extra safety (VERY IMPORTANT)
            if not vendor.store_lat or not vendor.store_long:
                continue

            try:
                distance = distance_km(
                    lat,
                    lon,
                    float(vendor.store_lat),
                    float(vendor.store_long)
                )
            except Exception:
                continue  # skip invalid vendor

            # =========================
            # 4. DISTANCE FILTER
            # =========================
            if distance <= 10:   # you can increase to 20 for testing

                vendor_products = Product.objects.filter(
                    vendor=vendor,
                    stock_quantity__gt=0
                )

                products.extend(vendor_products)

        # =========================
        # 5. REMOVE DUPLICATES
        # =========================
        unique_products = list(set(products))

        # =========================
        # 6. RESPONSE
        # =========================
        serializer = ProductSerializer(unique_products, many=True)

        return Response({
            "count": len(unique_products),
            "products": serializer.data
        })


# =========================================
# 🔹 3. BOOKING SUMMARY (CUSTOMER VIEW)
# =========================================
class BookingSummaryAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get booking total (service + approved products)",
        responses={200: openapi.Response("Booking Summary")},
        tags=["Booking"]
    )
    def get(self, request, booking_id):

        booking = get_object_or_404(Booking, id=booking_id)

        items = booking.items.all()

        product_total = sum([
            item.get_total_price()
            for item in items
            if item.approval_status == "APPROVED"
        ])

        total = booking.service_charge_at_booking + product_total

        return Response({
            "booking_id": booking.id,
            "service_charge": booking.service_charge_at_booking,
            "product_total": product_total,
            "total_amount": total,

            "items": [
                {
                    "item_id": item.id,
                    "product_name": item.product_name,
                    "product_price": item.product_price,
                    "product_image": item.product_image,
                    "quantity": item.quantity,
                    "total_price": item.get_total_price(),
                    "status": item.approval_status   # ✅ shows PENDING
                }
                for item in items
            ]
        })
    

# =========================================
# 🔹 4. CUSTOMER APPROVES PRODUCTS
# =========================================
class ApproveProductsAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Customer Approve / Reject Products (Multi-stage)",
        operation_description="""
Customer approves or rejects pending products in a booking.

🔥 FEATURES:
✔ Supports multi-stage approval  
✔ Only NEW approved items are sent to vendor  
✔ Prevents duplicate orders  
✔ Groups products by vendor  

FLOW:
1. Serviceman adds products → PENDING  
2. Customer approves → order created  
3. Serviceman adds more → again PENDING  
4. Customer approves → ONLY new items processed  

STATUS:
✔ APPROVED → sent to vendor  
❌ REJECTED → ignored  
""",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["status"],
            properties={
                "status": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["APPROVED", "REJECTED"],
                    example="APPROVED"
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Products processed successfully",
                examples={
                    "application/json": {
                        "message": "New items approved and sent to vendor",
                        "orders_created": [12, 13],
                        "total_cost": 1500
                    }
                }
            ),
            400: "Invalid request / No pending items",
            403: "Only customer allowed"
        },
        security=[{"Bearer": []}],
        tags=["Booking - Product Approval"]
    )
    def patch(self, request, booking_id):

        # =========================
        # 1. CHECK CUSTOMER
        # =========================
        if request.user.role != "CUSTOMER":
            return Response({"error": "Only customer allowed"}, status=403)

        booking = get_object_or_404(Booking, id=booking_id)

        if booking.customer.user != request.user:
            return Response({"error": "Not your booking"}, status=403)

        status_value = request.data.get("status")

        if status_value not in ["APPROVED", "REJECTED"]:
            return Response({"error": "Invalid status"}, status=400)

        # =========================
        # 2. GET PENDING ITEMS
        # =========================
        items = booking.items.filter(approval_status="PENDING")

        if not items.exists():
            return Response({"message": "No pending items"}, status=400)

        # =========================
        # 3. UPDATE ITEMS
        # =========================
        for item in items:
            item.approval_status = status_value
            item.save()

        # =========================
        # 4. IF REJECTED
        # =========================
        if status_value == "REJECTED":
            booking.update_total_cost()
            return Response({"message": "Items rejected"})

        # =========================
        # 5. ONLY NEW APPROVED ITEMS
        # =========================
        approved_items = booking.items.filter(
            approval_status="APPROVED",
            is_ordered=False
        )

        if not approved_items.exists():
            return Response({"message": "No new items to order"})

        # =========================
        # 6. GROUP BY VENDOR
        # =========================
        vendor_map = {}

        for item in approved_items:
            vendor = item.product.vendor

            if vendor not in vendor_map:
                vendor_map[vendor] = []

            vendor_map[vendor].append(item)

        orders = []

        # =========================
        # 7. CREATE ORDERS
        # =========================
        for vendor, items_list in vendor_map.items():

            order = MaterialOrder.objects.create(
                booking=booking,
                serviceman=booking.serviceman,
                vendor=vendor,
                status="REQUESTED",
                customer_approve=True
            )

            total = 0

            for item in items_list:

                MaterialOrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price_at_order=item.product_price
                )

                total += item.get_total_price()

                # 🔥 IMPORTANT
                item.is_ordered = True
                item.save()

            order.total_cost = total
            order.save()

            orders.append(order.id)

        booking.update_total_cost()

        return Response({
            "message": "New items approved and sent to vendor",
            "orders_created": orders,
            "total_cost": booking.total_cost
        })
        

class VendorOrderListAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Vendor: View ONLY approved product orders",
        responses={200: "Vendor Orders"},
        tags=["Vendor Orders"]
    )
    def get(self, request):

        if request.user.role != "VENDOR":
            return Response({"error": "Only vendor allowed"}, status=403)

        vendor = get_object_or_404(VendorProfile, user=request.user)

        orders = MaterialOrder.objects.filter(
            vendor=vendor,
            customer_approve=True
        ).order_by("-created_at")

        data = []

        for order in orders:

            # 🔥 AUTO REJECT
            if order.status == "REQUESTED":
                if timezone.now() - order.created_at >= timedelta(minutes=2):
                    order.status = "AUTO_REJECTED"
                    order.save()

            data.append({
                "order_id": order.id,
                "status": order.status,
                "total_cost": order.total_cost,
                "created_at": order.created_at,
            })

        return Response({
            "count": len(data),
            "orders": data
        })
        

# =========================================
# 🔹 MERGED API → ADD PRODUCT + SERVICE CHARGE
# =========================================

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Booking, BookingItem, Product, ServicemanProfile


class AddProductAndServiceChargeAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Serviceman adds product + updates service charge",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["product_id", "quantity", "service_charge"],
            properties={
                "product_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                "quantity": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                "service_charge": openapi.Schema(type=openapi.TYPE_NUMBER, example=200)
            }
        ),
        responses={200: "Product added + service charge updated"},
        tags=["Booking"]
    )

    def post(self, request, booking_id):

        if request.user.role != "SERVICEMAN":
            return Response({"error": "Only serviceman allowed"}, status=403)

        serviceman = get_object_or_404(
            ServicemanProfile,
            user=request.user
        )

        booking = get_object_or_404(
            Booking,
            id=booking_id,
            serviceman=serviceman
        )

        if booking.status not in ["ACCEPTED", "ONGOING"]:
            return Response({"error": "Booking not active"}, status=400)

        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))
        service_charge = request.data.get("service_charge")

        if not product_id:
            return Response({"error": "product_id required"}, status=400)

        if service_charge is None:
            return Response({"error": "service_charge required"}, status=400)

        product = get_object_or_404(Product, id=product_id)

        # ✅ ADD / UPDATE PRODUCT
        item, created = BookingItem.objects.get_or_create(
            booking=booking,
            product=product,
            defaults={
                "quantity": quantity,
                "product_name": product.name,
                "product_price": product.price,
                "product_image": product.image.url if product.image else None,

                # 🔥 IMPORTANT
                "approval_status": "PENDING",

                "product_data": {
                    "id": product.id,
                    "name": product.name,
                    "price": str(product.price),
                    "image": product.image.url if product.image else None,
                }
            }
        )

        if not created:
            item.quantity += quantity

            # 🔥 RESET TO PENDING
            item.approval_status = "PENDING"

            item.save()

        booking.service_charge_at_booking = service_charge
        booking.status = "ONGOING"
        booking.save()

        return Response({
            "message": "Product added successfully",
            "product": product.name,
            "quantity": item.quantity,
            "status": item.approval_status
        })


class UpdateProductAndServiceChargeAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Serviceman updates product quantity + service charge (ONLY HIS BOOKING)",
        operation_description="""
✔ Update:
- Product quantity
- Service charge

❌ Restrictions:
- Only assigned serviceman
- Only his booking
- Booking must be ACCEPTED or ONGOING
""",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["product_id"],
            properties={
                "product_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    example=5
                ),
                "quantity": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    example=3,
                    description="New quantity (0 = remove product)"
                ),
                "service_charge": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    example=250
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Updated successfully",
                examples={
                    "application/json": {
                        "message": "Booking updated successfully",
                        "booking_id": 12,
                        "product": "Pipe",
                        "quantity": 3,
                        "service_charge": 250,
                        "status": "ONGOING"
                    }
                }
            ),
            400: "Bad request",
            403: "Forbidden",
            404: "Not found"
        },
        security=[{"Bearer": []}],
        tags=["Booking"]
    )
    def patch(self, request, booking_id):

        # =========================
        # 1. ROLE CHECK
        # =========================
        if request.user.role != "SERVICEMAN":
            return Response({"error": "Only serviceman allowed"}, status=403)

        # =========================
        # 2. GET SERVICEMAN
        # =========================
        serviceman = get_object_or_404(
            ServicemanProfile,
            user=request.user
        )

        # =========================
        # 3. ONLY HIS BOOKING
        # =========================
        booking = get_object_or_404(
            Booking,
            id=booking_id,
            serviceman=serviceman
        )

        # =========================
        # 4. STATUS CHECK
        # =========================
        if booking.status not in ["ACCEPTED", "ONGOING"]:
            return Response({
                "error": "Booking not editable"
            }, status=400)

        # =========================
        # 5. GET DATA
        # =========================
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity")
        service_charge = request.data.get("service_charge")

        if not product_id:
            return Response({"error": "product_id required"}, status=400)

        product = get_object_or_404(Product, id=product_id)

        item = get_object_or_404(
            BookingItem,
            booking=booking,
            product=product
        )

        # =========================
        # 6. UPDATE PRODUCT
        # =========================
        if quantity is not None:
            quantity = int(quantity)

            if quantity <= 0:
                item.delete()
            else:
                item.quantity = quantity
                item.save()

        # =========================
        # 7. UPDATE SERVICE CHARGE
        # =========================
        if service_charge is not None:
            booking.service_charge_at_booking = service_charge

        booking.save()

        # =========================
        # 8. RESPONSE
        # =========================
        return Response({
            "message": "Booking updated successfully",
            "booking_id": booking.id,
            "product": product.name,
            "quantity": quantity,
            "service_charge": booking.service_charge_at_booking,
            "status": booking.status
        })        




class CreatePaymentIntentAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Create Payment Intent",
        operation_description="Create Stripe payment for booking",
        security=[{"Bearer": []}],
        tags=["Payment"]
    )
    def post(self, request, booking_id):

        # =========================
        # 1. ROLE CHECK
        # =========================
        if request.user.role != "CUSTOMER":
            return Response({"error": "Only customer can pay"}, status=403)

        # =========================
        # 2. GET BOOKING
        # =========================
        booking = get_object_or_404(Booking, id=booking_id)

        if booking.customer.user != request.user:
            return Response({"error": "Unauthorized"}, status=403)

        # =========================
        # 3. VALIDATION
        # =========================
        if booking.status != "PENDING_PAYMENT":
            return Response({"error": "Invalid booking state"}, status=400)

        if booking.payment_status == "PAID":
            return Response({"error": "Booking already paid"}, status=400)

        if booking.total_cost <= 0:
            return Response({"error": "Invalid booking amount"}, status=400)

        # =========================
        # 4. STRIPE AMOUNT
        # =========================
        amount = int(booking.total_cost * 100)  # INR → paise

        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency="inr",
                metadata={
                    "booking_id": str(booking.id),
                    "customer_id": str(request.user.id)
                }
            )
        except Exception as e:
            return Response({
                "error": "Stripe error",
                "details": str(e)
            }, status=500)

        # =========================
        # 5. SAVE PAYMENT RECORD
        # =========================
        Payment.objects.create(
            booking=booking,
            customer=booking.customer,
            amount=booking.total_cost,
            status="PENDING",
            gateway_order_id=intent.id
        )

        # =========================
        # 6. RESPONSE
        # =========================
        return Response({
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
            "amount": amount,
            "currency": "INR",
            "public_key": settings.STRIPE_PUBLIC_KEY
        })


class VerifyStripePaymentAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Verify Stripe Payment (Swagger Test Mode)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["payment_intent_id"],
            properties={
                "payment_intent_id": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example="pi_3Nxxxxxxx"
                ),
                "force_success": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    example=True,
                    description="FOR TESTING ONLY (Swagger)"
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Payment success",
                examples={
                    "application/json": {
                        "message": "Payment successful",
                        "booking_id": 65,
                        "booking_status": "PENDING",
                        "payment_status": "PAID"
                    }
                }
            )
        },
        security=[{"Bearer": []}],
        tags=["Payment"]
    )
    def post(self, request, booking_id):

        payment_intent_id = request.data.get("payment_intent_id")
        force_success = request.data.get("force_success", False)

        if not payment_intent_id:
            return Response({"error": "payment_intent_id required"}, status=400)

        booking = get_object_or_404(Booking, id=booking_id)

        if booking.customer.user != request.user:
            return Response({"error": "Unauthorized"}, status=403)

        # 🔥 FIXED QUERY (NO status filter)
        payment = Payment.objects.filter(
            booking=booking,
            gateway_order_id=payment_intent_id
        ).first()

        if not payment:
            return Response({"error": "Payment not found"}, status=404)

        # =========================
        # 🔥 SWAGGER FORCE MODE
        # =========================
        if force_success:

            payment.status = "PAID"
            payment.gateway_payment_id = payment_intent_id
            payment.paid_at = timezone.now()
            payment.save()

            booking.payment_status = "PAID"
            booking.status = "PENDING"
            booking.save()

            return Response({
                "message": "Payment successful (TEST MODE)",
                "booking_id": booking.id,
                "booking_status": booking.status,
                "payment_status": booking.payment_status
            })

        # =========================
        # REAL STRIPE VERIFY
        # =========================
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        except Exception as e:
            return Response({
                "error": "Stripe error",
                "details": str(e)
            }, status=500)

        if intent.status == "succeeded":

            payment.status = "PAID"
            payment.gateway_payment_id = payment_intent_id
            payment.paid_at = timezone.now()
            payment.save()

            booking.payment_status = "PAID"
            booking.status = "PENDING"
            booking.save()

            return Response({
                "message": "Payment successful",
                "booking_id": booking.id,
                "booking_status": booking.status,
                "payment_status": booking.payment_status
            })

        return Response({
            "error": "Payment not completed",
            "stripe_status": intent.status
        }, status=400)        

class BookingPaymentDetailAPI(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_summary="Get booking payment details",
        responses={
            200: openapi.Response(
                description="Booking Payment Details",
                examples={
                    "application/json": {
                        "booking_id": 12,
                        "payment_status": "PAID"
                    }
                }
            ),
            404: "Booking not found"
        },
        security=[{"Bearer": []}],
        tags=["Payment"]
    )
    def get(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
            return Response({
                "booking_id": booking.id,
                "payment_status": booking.payment_status,
            }, status=200)
        except Booking.DoesNotExist:

            return Response({"detail": "Booking not found"}, status=404)





class VendorTrackingAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Step-by-Step Vendor Tracking",
        operation_description="""
🔥 FLOW:

1. Customer approves all products
2. Vendors accept orders
3. Tracking starts

✔ Behavior:
- Shows ONLY NEXT nearest vendor
- After collection → next vendor shown
- AUTO_REJECTED → ignored
- PENDING → blocks tracking

📍 Result:
- Step-by-step vendor pickup
""",
        manual_parameters=[
            openapi.Parameter(
                'booking_id',
                openapi.IN_PATH,
                description="Booking ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Next Vendor",
                examples={
                    "application/json": {
                        "booking_id": 101,
                        "status": "COLLECTION_IN_PROGRESS",
                        "next_vendor": {
                            "order_id": 12,
                            "vendor_id": 5,
                            "vendor_name": "ABC Hardware",
                            "distance_km": 1.2
                        }
                    }
                }
            ),
            400: "Tracking not allowed",
            403: "Unauthorized"
        },
        security=[{"Bearer": []}],
        tags=["Vendor Tracking"]
    )
    def get(self, request, booking_id):

        # =========================
        # 🔹 GET BOOKING
        # =========================
        booking = get_object_or_404(
            Booking.objects.select_related(
                "customer__user",
                "serviceman__user"
            ),
            id=booking_id
        )

        # =========================
        # 🔒 ACCESS CONTROL
        # =========================
        if request.user.role == "CUSTOMER":
            if booking.customer.user != request.user:
                return Response({"error": "Unauthorized"}, status=403)

        elif request.user.role == "SERVICEMAN":
            if booking.serviceman.user != request.user:
                return Response({"error": "Unauthorized"}, status=403)

        else:
            return Response({"error": "Access not allowed"}, status=403)

        # =========================
        # 🔹 PRODUCT APPROVAL CHECK
        # =========================
        items = booking.items.all()

        if items.filter(approval_status="PENDING").exists():
            return Response({
                "error": "All products must be approved first"
            }, status=400)

        # =========================
        # 🔹 GET ORDERS
        # =========================
        orders = booking.material_orders.all()

        if not orders.exists():
            return Response({
                "error": "No vendor orders found"
            }, status=400)

        accepted_orders = []

        for order in orders:

            # 🔥 AUTO REJECT AFTER 2 MIN
            if order.status == "PENDING":
                if timezone.now() - order.created_at >= timedelta(minutes=2):
                    order.status = "AUTO_REJECTED"
                    order.save()

            # ❌ BLOCK IF STILL PENDING
            if order.status == "PENDING":
                return Response({
                    "error": "Waiting for vendor response"
                }, status=400)

            # ✅ ONLY ACCEPTED
            if order.status == "VENDOR_ACCEPTED":
                accepted_orders.append(order)

        # =========================
        # 🔹 FILTER NOT COLLECTED
        # =========================
        active_orders = [
            order for order in accepted_orders if not order.is_collected
        ]

        # =========================
        # 🔹 ALL DONE
        # =========================
        if not active_orders:
            return Response({
                "booking_id": booking.id,
                "status": "ALL_COLLECTED",
                "message": "All vendor items collected"
            })

        # =========================
        # 🔹 CUSTOMER LOCATION
        # =========================
        if not booking.customer.default_lat or not booking.customer.default_long:
            return Response({
                "error": "Customer location missing"
            }, status=400)

        customer_lat = float(booking.customer.default_lat)
        customer_lon = float(booking.customer.default_long)

        # =========================
        # 🔹 FIND NEAREST VENDOR
        # =========================
        nearest_vendor = None
        min_distance = float("inf")

        for order in active_orders:
            vendor = order.vendor

            if not vendor.store_lat or not vendor.store_long:
                continue

            dist = distance_km(
                customer_lat,
                customer_lon,
                float(vendor.store_lat),
                float(vendor.store_long)
            )

            if dist < min_distance:
                min_distance = dist
                nearest_vendor = {
                    "order_id": order.id,
                    "vendor_id": vendor.user.id,
                    "vendor_name": vendor.business_name,
                    "vendor_lat": vendor.store_lat,
                    "vendor_long": vendor.store_long,
                    "distance_km": round(dist, 2)
                }

        # =========================
        # 🔹 FINAL RESPONSE
        # =========================
        return Response({
            "booking_id": booking.id,
            "status": "COLLECTION_IN_PROGRESS",
            "next_vendor": nearest_vendor
        })

class MarkVendorCollectedAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Mark Vendor Items as Collected",
        manual_parameters=[
            openapi.Parameter(
                'order_id',
                openapi.IN_PATH,
                description="Material Order ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        tags=["Vendor Tracking"]
    )
    def patch(self, request, order_id):

        if request.user.role != "SERVICEMAN":
            return Response({"error": "Only serviceman allowed"}, status=403)

        order = get_object_or_404(MaterialOrder, id=order_id)

        if order.status != "VENDOR_ACCEPTED":
            return Response({
                "error": "Order not accepted"
            }, status=400)

        if order.is_collected:
            return Response({
                "message": "Already collected"
            })

        order.is_collected = True
        order.save()

        return Response({
            "message": "Vendor items collected successfully",
            "order_id": order.id
        })


class VendorDeliverOrderAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Vendor Mark Order as Delivered",
        operation_description="""
✔ Only accepted orders can be delivered  
✔ Cannot deliver if auto rejected  
✔ After delivery → status becomes DELIVERED  
""",
        responses={
            200: openapi.Response(
                description="Order delivered",
                examples={
                    "application/json": {
                        "message": "Order delivered successfully",
                        "order_id": 10,
                        "status": "DELIVERED"
                    }
                }
            ),
            400: "Invalid state",
            403: "Unauthorized"
        },
        tags=["Vendor Orders"]
    )
    def patch(self, request, order_id):

        # =========================
        # 🔒 ROLE CHECK
        # =========================
        if request.user.role != "VENDOR":
            return Response({"error": "Only vendor allowed"}, status=403)

        vendor = get_object_or_404(VendorProfile, user=request.user)

        order = get_object_or_404(MaterialOrder, id=order_id, vendor=vendor)

        # =========================
        # ❌ BLOCK INVALID STATES
        # =========================
        if order.status == "AUTO_REJECTED":
            return Response({"error": "Order auto rejected"}, status=400)

        if order.status != "VENDOR_ACCEPTED":
            return Response({
                "error": "Order must be accepted before delivery"
            }, status=400)

        # =========================
        # ✅ MARK DELIVERED
        # =========================
        order.status = "DELIVERED"
        order.save()

        return Response({
            "message": "Order delivered successfully",
            "order_id": order.id,
            "status": order.status
        })