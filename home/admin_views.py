from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.db.models import Prefetch
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import User, Category, Booking, ServicemanProfile
from .serializers import (
    UserProfileSerializer, 
    CategorySerializer, 
    BookingHistorySerializer,
    AdminServicemanBookingSerializer
)
from .permissions import IsAdminRole
from rest_framework.permissions import AllowAny

# ===============================
# 🔥 ADMIN USER MANAGEMENT
# ===============================

class AdminUserManagementAPI(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_summary="Admin: Get all users",
        tags=["Admin - Users"],
        security=[{"Bearer": []}]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Admin: Create new user",
        request_body=UserProfileSerializer,
        tags=["Admin - Users"],
        security=[{"Bearer": []}]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AdminUserDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_summary="Admin: Get single user",
        tags=["Admin - Users"],
        security=[{"Bearer": []}]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Admin: Update user",
        request_body=UserProfileSerializer,
        tags=["Admin - Users"],
        security=[{"Bearer": []}]
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Admin: Delete user",
        tags=["Admin - Users"],
        security=[{"Bearer": []}]
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)





# ==========================================
# 🔥 PUBLIC CATEGORY LIST (GET for all)
# ==========================================

class CategoryListAPI(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Get all categories (Public)",
        tags=["Categories"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ==========================================
# 🔐 ADMIN CATEGORY CREATE
# ==========================================

class CategoryCreateAPI(generics.CreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_summary="Admin: Create category",
        tags=["Admin - Categories"],
        security=[{"Bearer": []}]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


# ==========================================
# 🔐 ADMIN CATEGORY UPDATE & DELETE
# ==========================================

class CategoryDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_summary="Admin: Get category",
        tags=["Admin - Categories"],
        security=[{"Bearer": []}]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Admin: Update category",
        tags=["Admin - Categories"],
        security=[{"Bearer": []}]
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Admin: Delete category",
        tags=["Admin - Categories"],
        security=[{"Bearer": []}]
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

from rest_framework.views import APIView
from rest_framework.response import Response
from .models import PlatformSettings
from .serializers import PlatformSettingsSerializer

class AdminPlatformSettingsAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_summary="Admin: Get Platform Settings",
        tags=["Admin - Settings"],
        security=[{"Bearer": []}]
    )
    def get(self, request):
        settings, _ = PlatformSettings.objects.get_or_create(id=1)
        serializer = PlatformSettingsSerializer(settings)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Admin: Update Platform Settings",
        request_body=PlatformSettingsSerializer,
        tags=["Admin - Settings"],
        security=[{"Bearer": []}]
    )
    def patch(self, request):
        settings, _ = PlatformSettings.objects.get_or_create(id=1)
        serializer = PlatformSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
        
    @swagger_auto_schema(
        operation_summary="Admin: Update Platform Settings Post",
        request_body=PlatformSettingsSerializer,
        tags=["Admin - Settings"],
        security=[{"Bearer": []}]
    )
    def post(self, request):
        return self.patch(request)

# ==========================================
# 🔐 ADMIN BOOKING MANAGEMENT
# ==========================================

class AdminAllBookingsAPI(generics.ListAPIView):
    queryset = Booking.objects.all().order_by("-created_at")
    serializer_class = BookingHistorySerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_summary="Admin: Get all bookings",
        tags=["Admin - Bookings"],
        security=[{"Bearer": []}]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class AdminServicemanBookingAPI(generics.ListAPIView):
    queryset = ServicemanProfile.objects.select_related('user').prefetch_related(
        Prefetch(
            'booking_set',
            queryset=Booking.objects.select_related('customer__user').prefetch_related('items__product').order_by('-created_at'),
            to_attr='prefetched_bookings'
        )
    )
    serializer_class = AdminServicemanBookingSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_summary="Admin: Get all servicemen with their bookings",
        tags=["Admin - Bookings"],
        security=[{"Bearer": []}]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)