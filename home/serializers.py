from email.mime import image
import cloudinary.uploader

from rest_framework import serializers
from .models import   User , CustomerProfile, ServicemanProfile, VendorProfile
import re
from django.contrib.auth import authenticate

class EmailPasswordLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid email or password")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")

        data["user"] = user
        return data




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
    profile_image = serializers.ImageField(required=False, write_only=True)
    profile_image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomerProfile
        fields = [
            "default_address",
            "default_lat",
            "default_long",
            "profile_image",
            "profile_image_url",
        ]

    def get_profile_image_url(self, obj):
        if obj.profile_image:
            return obj.profile_image.url
        return None
    def update(self, instance, validated_data):
        new_image = validated_data.get("profile_image", None)

        if new_image and instance.profile_image:
            try:
                public_id = instance.profile_image.public_id if instance.profile_image else None
                cloudinary.uploader.destroy(public_id)
            except Exception:
                pass

        return super().update(instance, validated_data)



class ServicemanProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user_id", read_only=True)
    name = serializers.CharField(source="user.name", read_only=True)        
    hourly_charges = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False
    )

    skills = serializers.CharField(
    required=False,
    help_text="Enter skills as comma separated values. Example: Plumbing,Electrician,AC Repair"
)
    profile_image = serializers.ImageField(required=False, write_only=True)
    profile_image_url = serializers.SerializerMethodField(read_only=True)

    kyc_document = serializers.ImageField(required=False, write_only=True)
    kyc_document_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ServicemanProfile
        fields = [
            "id",
            "name",  # 🔥 ADD THIS
            "is_online",
            "is_approved",
            "is_active",
            "current_lat",
            "current_long",
            "experience_years",
            "hourly_charges",     # ✅ NEW
            "skills",             # ✅ NEW
            "average_rating",
            "profile_image",
            "profile_image_url",
            "kyc_document",       # ✅ NEW
            "kyc_document_url",   # ✅ NEW
        ]
        read_only_fields = ["is_approved"]

    def get_profile_image_url(self, obj):
        if obj.profile_image:
            return obj.profile_image.url
        return None

    def get_kyc_document_url(self, obj):
        if obj.kyc_document:
            return obj.kyc_document.url
        return None
    def validate_skills(self, value):
        if value:
            return [skill.strip() for skill in value.split(",")]
        return []
    def update(self, instance, validated_data):
        file_fields = ["profile_image", "kyc_document"]

        for field in file_fields:
            new_file = validated_data.get(field, None)
            old_file = getattr(instance, field)

            if new_file and old_file:
                try:
                    cloudinary.uploader.destroy(old_file.public_id)
                except Exception:
                    pass

        return super().update(instance, validated_data)
    


class VendorProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user_id", read_only=True)    
    # ========= Image Upload =========
    profile_image = serializers.ImageField(required=False, write_only=True)
    profile_image_url = serializers.SerializerMethodField(read_only=True)

    # ========= Documents Upload =========
    gst_certificate = serializers.FileField(required=False, write_only=True)
    store_registration = serializers.FileField(required=False, write_only=True)
    id_proof = serializers.FileField(required=False, write_only=True)

    gst_certificate_url = serializers.SerializerMethodField(read_only=True)
    store_registration_url = serializers.SerializerMethodField(read_only=True)
    id_proof_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = VendorProfile
        fields = [
            "id",
            "is_approved",   # ✅ ADD THIS
            "is_active",   # ✅ ADD THIS
            # ================= BUSINESS =================
            "business_name",
            "gst_number",
            "contact_number",
            "business_email",
            "opening_time",
            "closing_time",
            "city",
            "state",
            "full_address",
            "store_lat",
            "store_long",

            # ================= BANK =================
            "account_holder_name",
            "bank_name",
            "account_number",
            "ifsc_code",
            "upi_id",

            # ================= IMAGE =================
            "profile_image",
            "profile_image_url",

            # ================= DOCUMENTS =================
            "gst_certificate",
            "store_registration",
            "id_proof",
            "gst_certificate_url",
            "store_registration_url",
            "id_proof_url",
        ]
        read_only_fields = ["is_approved","is_active"]  # 🔒 Only admin can change
    # ================= IMAGE URL =================
    def get_profile_image_url(self, obj):
        if obj.profile_image:
            return obj.profile_image.url
        return None

    # ================= DOCUMENT URLS =================
    def get_gst_certificate_url(self, obj):
        if obj.gst_certificate:
            return obj.gst_certificate.url
        return None

    def get_store_registration_url(self, obj):
        if obj.store_registration:
            return obj.store_registration.url
        return None

    def get_id_proof_url(self, obj):
        if obj.id_proof:
            return obj.id_proof.url
        return None

    # ================= SAFE UPDATE (Delete Old Cloudinary Files) =================
    def update(self, instance, validated_data):
        file_fields = [
            "profile_image",
            "gst_certificate",
            "store_registration",
            "id_proof",
        ]

        for field in file_fields:
            new_file = validated_data.get(field, None)
            old_file = getattr(instance, field)

            if new_file and old_file:
                try:
                    cloudinary.uploader.destroy(old_file.public_id)
                except Exception:
                    pass

        return super().update(instance, validated_data)




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


#Added Serializers for Category, Service and Product models#
from .models import Category, Service, Product

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"





class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"

# Serviceman
from .models import Serviceman
 
class ServicemanSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name")

    class Meta:
        model = Serviceman
        fields = ["id", "name", "category", "latitude", "longitude"]


class VendorNearbySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user_id", read_only=True)
    user_name = serializers.CharField(source="user.name", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = VendorProfile
        fields = [
            "id",
            "user_name",
            "phone",
            "business_name",
            "city",
            "state",
            "full_address",
            "store_lat",
            "store_long",
            "profile_image_url",
        ]

    def get_profile_image_url(self, obj):
        if obj.profile_image:
            return obj.profile_image.url
        return None


#--------Booking-serializer---------------------
# ================= BOOKING SERIALIZERS =================
from .models import Booking
from rest_framework import serializers
from datetime import datetime
from django.utils import timezone


class BookingCreateSerializer(serializers.Serializer):
    serviceman_id = serializers.IntegerField()

    scheduled_date = serializers.DateField()
    scheduled_time = serializers.TimeField()

    problem_title = serializers.CharField(max_length=255)
    problem_description = serializers.CharField()

    job_location_address = serializers.CharField()
    job_lat = serializers.DecimalField(max_digits=10, decimal_places=8)
    job_long = serializers.DecimalField(max_digits=11, decimal_places=8)

    # 🔥 IMPORTANT FIX
    images = serializers.ImageField(
        required=False,
        write_only=True
    )

    def validate(self, data):
        scheduled_at = datetime.combine(
        data["scheduled_date"],
        data["scheduled_time"]
    )

    # Convert to timezone-aware datetime
        scheduled_at = timezone.make_aware(
        scheduled_at,
        timezone.get_current_timezone()
    )

        if scheduled_at < timezone.now():
            raise serializers.ValidationError(
            "Scheduled time must be in future"
        )

        data["scheduled_at"] = scheduled_at
        return data 

class BookingResponseSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.user.name")
    serviceman_name = serializers.CharField(source="serviceman.user.name")

    class Meta:
        model = Booking
        fields = [
            "id",
            "customer_name",
            "serviceman_name",
            "scheduled_at",
            "problem_title",
            "problem_description",
            "total_labor_cost",
            "total_material_cost",
            "platform_fee",
            "grand_total",
            "status",
            "job_location_address",
        ]


# ================= SERVICE SERIALIZERS =================

from .models import Service, Category
from rest_framework import serializers


class ServiceSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )

    class Meta:
        model = Service
        fields = [
            "id",
            "category",
            "category_name",
            "name",
            "description",
            "base_price",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_base_price(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Base price must be greater than zero"
            )
        return value

    def validate_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Service name must be at least 3 characters"
            )
        return value