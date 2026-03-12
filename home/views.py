import cloudinary
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Booking, BookingItem, User, CustomerProfile, ServicemanProfile, VendorProfile, EmailOTP,Category,Service,Product
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
    ServicemanSerializer
)
from .utils import send_email_otp, verify_email_otp
from rest_framework import request, status
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .permissions import IsAdminOrCustomer


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
        operation_summary="Create booking with images",
        manual_parameters=[
            openapi.Parameter(
                name="images",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                description="Upload multiple images",
                required=False,
            ),
        ],
        request_body=BookingCreateSerializer,
        consumes=["multipart/form-data"],
        tags=["Bookings"],
        security=[{"Bearer": []}],
    )

    def post(self, request):
        serializer = BookingCreateSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid(raise_exception=True):
            booking = serializer.save()

            # 🔥 Handle images here
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

            return Response(
                {
                    "message": "Booking created successfully",
                    "id": booking.id,
                    "price_breakdown": {
                    "service_charge": booking.serviceman.hourly_charges,
                    "platform_fee": round(booking.serviceman.hourly_charges * Decimal("0.10"), 2),
                    "total_cost": booking.serviceman.hourly_charges + round(booking.serviceman.hourly_charges * Decimal("0.10"), 2)
                    },
                    "image_urls": booking.image_urls,
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
# ================= SERVICE LIST API =================

from .models import Service
from .serializers import ServiceSerializer


class ServiceCreateAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        request_body=ServiceSerializer,
        responses={201: ServiceSerializer},
        security=[{"Bearer": []}],
        tags=["Services - Admin"]
    )
    def post(self, request):
        serializer = ServiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=201)

class ServiceListAPI(APIView):
    permission_classes = [IsAuthenticated]  # or AllowAny if public

    @swagger_auto_schema(
        operation_summary="Get All Active Services",
        responses={200: ServiceSerializer(many=True)},
        tags=["Services"]
    )
    def get(self, request):
        services = Service.objects.filter(is_active=True)
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)        
    

class ServiceUpdateAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        request_body=ServiceSerializer,
        responses={200: ServiceSerializer},
        security=[{"Bearer": []}],
        tags=["Services - Admin"]
    )
    def put(self, request, pk):
        service = get_object_or_404(Service, pk=pk)

        serializer = ServiceSerializer(
            service,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)    
    
from .permissions import IsAdminRole

class ServiceSoftDeleteAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]
    @swagger_auto_schema(
        operation_summary="Admin: Soft Delete Service",
        operation_description="Sets is_active=False for the service. Only ADMIN can perform this action.",
        responses={
            200: openapi.Response(
                description="Service soft deleted successfully",
                examples={
                    "application/json": {
                        "message": "Service soft deleted successfully"
                    }
                }
            ),
            404: "Service not found",
            403: "Admin access required"
        },
        security=[{"Bearer": []}],
        tags=["Services - Admin"]
    )
    def delete(self, request, pk):
        service = get_object_or_404(Service, pk=pk)
        service.is_active = False
        service.save()

        return Response({
            "message": "Service soft deleted successfully"
        })


from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Booking, ServicemanProfile


class ServicemanBookingActionAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Serviceman: Accept or Reject Booking",
        operation_description="""Serviceman can accept or reject a booking assigned to them.
        - Accepting sets status to ACCEPTED
        - Rejecting sets status to CANCELLED                
        Only the assigned serviceman can perform
        this action.""",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "action": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Action to perform: accept or reject"
                )
            },
            example={
                "action": "accept"
            }
        ),
        responses={
            200: openapi.Response(
                description="Booking status updated successfully",
                examples={
                    "application/json": {
                        "message": "Booking accepted successfully",
                        "status": "ACCEPTED"
                    }
                }
            ),
            400: "Invalid action",
            403: "Only assigned serviceman can perform this action",
            404: "Booking not found"
        },
        security=[{"Bearer": []}],
        tags=["Booking - Serviceman Actions"]
    )

    def patch(self, request, booking_id):

        if request.user.role != "SERVICEMAN":
            return Response(
            {"detail": "Only serviceman can perform this action"},
            status=403
        )

        booking = get_object_or_404(Booking, pk=booking_id)

        serviceman = get_object_or_404(
        ServicemanProfile,
        user=request.user
        )

        if booking.serviceman != serviceman:
            return Response(
            {"detail": "You are not assigned to this booking"},
            status=403
        )

    # ⭐ Only PENDING bookings can be acted on
        if booking.status != "PENDING":
            return Response(
            {"detail": "This booking cannot be modified anymore"},
            status=400
        )

        action = request.data.get("action")

        if action == "accept":
            booking.status = "ACCEPTED"

        elif action == "reject":
            booking.status = "CANCELLED"

        else:
            return Response(
            {"detail": "Invalid action. Use accept or reject"},
            status=400
        )

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
                return Response(
                    {"detail": "You can delete only your products"},
                    status=403
                )

        elif request.user.role != "ADMIN":
            return Response(
                {"detail": "Not allowed"},
                status=403
            )

        product.delete()

        return Response({
            "message": "Product deleted successfully"
        })    
    


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
        operation_summary="Get bookings assigned to logged-in serviceman",
        responses={200: BookingDetailSerializer(many=True)},
        security=[{"Bearer": []}],
        tags=["Serviceman Bookings"]
    )

    def get(self, request):

        # Only serviceman allowed
        if request.user.role != "SERVICEMAN":
            return Response(
                {"error": "Only serviceman can access this"},
                status=403
            )

        try:
            serviceman = ServicemanProfile.objects.get(user=request.user)
        except ServicemanProfile.DoesNotExist:
            return Response(
                {"error": "Serviceman profile not found"},
                status=404
            )

        # ⭐ ONLY BOOKINGS ASSIGNED TO THIS SERVICEMAN
        bookings = Booking.objects.filter(
            serviceman=serviceman
        ).order_by("-created_at")

        serializer = BookingDetailSerializer(bookings, many=True)

        return Response(serializer.data)