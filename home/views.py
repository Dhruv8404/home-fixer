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

        queryset = ServicemanProfile.objects.filter(
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

        queryset = ServicemanProfile.objects.filter(
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
from decimal import Decimal
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Booking, BookingImage

class CreateBookingAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        operation_summary="Create Booking (Customer Only)",
        operation_description="""
Customer books a serviceman.

• Prevents double booking  
• Calculates 10% platform fee  
• Supports multiple image upload  
""",
        request_body=BookingCreateSerializer,
        consumes=["multipart/form-data"],
        responses={
            201: openapi.Response(
                description="Booking Created Successfully"
            ),
            400: "Validation Error",
            403: "Only customers can create bookings"
        },
        security=[{"Bearer": []}],
        tags=["Booking"]
    )
    def post(self, request):

        if request.user.role != "CUSTOMER":
            return Response(
                {"detail": "Only customers can create bookings"},
                status=403
            )

        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        customer, _ = CustomerProfile.objects.get_or_create(
        user=request.user
)
        serviceman = get_object_or_404(
            ServicemanProfile,
            pk=data["serviceman_id"],
            is_active=True,
            is_approved=True
        )

        scheduled_at = data["scheduled_at"]

        # Prevent double booking
        if Booking.objects.filter(
            serviceman=serviceman,
            scheduled_at=scheduled_at,
            status__in=["PENDING", "ACCEPTED", "ONGOING"]
        ).exists():
            return Response(
                {"detail": "Serviceman already booked at this time"},
                status=400
            )

        # Price Calculation
        labor_cost = serviceman.hourly_charges
        material_cost = Decimal("0.00")
        platform_fee = labor_cost * Decimal("0.10")
        grand_total = labor_cost + material_cost + platform_fee

        # Create booking
        booking = Booking.objects.create(
            customer=customer,
            serviceman=serviceman,
            scheduled_at=scheduled_at,
            problem_title=data["problem_title"],
            problem_description=data["problem_description"],
            job_location_address=data["job_location_address"],
            job_lat=data["job_lat"],
            job_long=data["job_long"],
            total_labor_cost=labor_cost,
            total_material_cost=material_cost,
            platform_fee=platform_fee,
            grand_total=grand_total,
        )

        # Multiple Image Upload (still works)
        images = request.FILES.getlist("images")
        for img in images:
            BookingImage.objects.create(
                booking=booking,
                image=img
            )

        return Response({
            "message": "Booking Confirmed",
            "booking_id": booking.id,
            "price_breakdown": {
                "labor_cost": labor_cost,
                "material_cost": material_cost,
                "platform_fee": platform_fee,
                "grand_total": grand_total
            }
        }, status=201)

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