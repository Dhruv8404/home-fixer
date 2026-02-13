from rest_framework import serializers
from .models import   User , CustomerProfile, ServicemanProfile, VendorProfile
import re

#==========Logout Serializer ==========#
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


#==========Otp sent and verification serializers ==========#
class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

#===========Verify OTP Serializer ==========#
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

#===========Complete Registration Serializer ==========#


class CompleteRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    name = serializers.CharField(required=True, max_length=255)
    phone = serializers.CharField(
        required=True,
        min_length=10,
        max_length=10
    )
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(
        choices=["CUSTOMER", "SERVICEMAN", "VENDOR"],
        default="CUSTOMER"
    )

    def validate_phone(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(
            "Phone number must contain only digits"
        )

    # 🔥 ADD THIS PART
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError(
            "User with this phone number already exists"
        )

        return value


    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "User with this email already exists"
            )
        return value



#===========User Profile Serializer ==========#
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'name',
            'email',
            'phone',
            'role',
            'is_verified',
        ]


#===========Customer, Serviceman, Vendor Profile Serializers ==========#

class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = [
            "default_address",
            "default_lat",
            "default_long",
            "profile_pic_url",
        ]


class ServicemanProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicemanProfile
        fields = [
            "is_online",
            "current_lat",
            "current_long",
            "experience_years",
            "kyc_docs_url",
        ]


class VendorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorProfile
        fields = [
            "business_name",
            "gst_number",
            "store_address",
            "store_lat",
            "store_long",
            "opening_hours",
            "bank_account_details",
        ]


class ProfileResponseSerializer(serializers.Serializer):
    user = UserProfileSerializer()
    profile = serializers.DictField()



class UniversalProfileUpdateSerializer(serializers.Serializer):

    # ===== CUSTOMER =====
    default_address = serializers.CharField(required=False)
    default_lat = serializers.DecimalField(max_digits=10, decimal_places=8, required=False)
    default_long = serializers.DecimalField(max_digits=11, decimal_places=8, required=False)
    profile_pic_url = serializers.URLField(required=False)

    # ===== SERVICEMAN =====
    is_online = serializers.BooleanField(required=False)
    current_lat = serializers.DecimalField(max_digits=10, decimal_places=8, required=False)
    current_long = serializers.DecimalField(max_digits=11, decimal_places=8, required=False)
    experience_years = serializers.IntegerField(required=False)
    kyc_docs_url = serializers.URLField(required=False)

    # ===== VENDOR =====
    business_name = serializers.CharField(required=False)
    gst_number = serializers.CharField(required=False)
    store_address = serializers.CharField(required=False)
    store_lat = serializers.DecimalField(max_digits=10, decimal_places=8, required=False)
    store_long = serializers.DecimalField(max_digits=11, decimal_places=8, required=False)
    opening_hours = serializers.CharField(required=False)
    bank_account_details = serializers.CharField(required=False)
