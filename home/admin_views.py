from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import User, Category
from .serializers import UserProfileSerializer, CategorySerializer
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