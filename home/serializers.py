from decimal import Decimal
import cloudinary.uploader
from .utils import delete_cloudinary_image
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

        new_image = validated_data.get("profile_image")

        if new_image and instance.profile_image:
            delete_cloudinary_image(instance.profile_image)

        return super().update(instance, validated_data)


class ServicemanProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user_id", read_only=True)
    name = serializers.CharField(source="user.name", read_only=True)        
    visiting_charge = serializers.DecimalField(
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
            "visiting_charge",     # ✅ NEW
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
            new_file = validated_data.get(field)
            old_file = getattr(instance, field)

            if new_file and old_file:
                delete_cloudinary_image(old_file)

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
            new_file = validated_data.get(field)
            old_file = getattr(instance, field)

            if new_file and old_file:
                delete_cloudinary_image(old_file)

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



from rest_framework import serializers
from .models import Product, VendorProfile

class ProductSerializer(serializers.ModelSerializer):

    vendor = serializers.PrimaryKeyRelatedField(
        queryset=VendorProfile.objects.all(),
        required=False
    )

    image = serializers.ImageField(required=False)
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "vendor",
            "category",
            "name",
            "price",
            "stock_quantity",
            "min_stock_alert",
            "image",
            "image_url",
            "description",
            "created_at",
            "updated_at",
        ]

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


    def update(self, instance, validated_data):

        new_image = validated_data.get("image")

        if new_image and instance.image:
            delete_cloudinary_image(instance.image)

        return super().update(instance, validated_data)

    def create(self, validated_data):

        request = self.context["request"]

        if request.user.role == "VENDOR":
            vendor = VendorProfile.objects.get(user=request.user)
            validated_data["vendor"] = vendor

        return Product.objects.create(**validated_data)
    


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


    #Booking Serializer
from rest_framework.exceptions import ValidationError
from .models import ServicemanProfile,Booking
from .utils import distance_km
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from datetime import datetime

class BookingCreateSerializer(serializers.ModelSerializer):
    scheduled_time = serializers.CharField()

    class Meta:
        model = Booking
        fields = [
            "serviceman",
            "scheduled_date",
            "scheduled_time",
            "problem_title",
            "problem_description",
        ]

        
    def validate_scheduled_time(self, value):
        try:
            time_obj = datetime.strptime(value, "%I:%M %p").time()
            return time_obj
        except ValueError:
            raise serializers.ValidationError(
                "Time must be in format HH:MM AM/PM (e.g. 10:30 AM)"
            )

    def validate(self, attrs):
        request = self.context["request"]
        serviceman = attrs.get("serviceman")

        try:
            customer_profile = request.user.customerprofile
        except CustomerProfile.DoesNotExist:
            raise serializers.ValidationError("Customer profile not found")

        # Location checks
        if not customer_profile.default_lat or not customer_profile.default_long:
            raise serializers.ValidationError("Customer location not available")

        if not serviceman.current_lat or not serviceman.current_long:
            raise serializers.ValidationError("Serviceman location not available")

        if not serviceman.is_active:
            raise serializers.ValidationError("Serviceman is not active")

        if not serviceman.is_approved:
            raise serializers.ValidationError("Serviceman is not approved")

        dist = distance_km(
            float(customer_profile.default_lat),
            float(customer_profile.default_long),
            float(serviceman.current_lat),
            float(serviceman.current_long),
        )

        if dist > 10:
            raise serializers.ValidationError(
                f"Serviceman is {round(dist,2)} km away. Must be within 10 km."
            )

        return attrs

    def validate_images(self, images):

        if len(images) > 4:
            raise serializers.ValidationError("Maximum 4 images allowed.")

        for image in images:
            if image.size > 5 * 1024 * 1024:   # 5MB
                raise serializers.ValidationError(
                    "Each image must be smaller than 5MB."
                )
        return images

    def upload_to_cloudinary(image):
        image.seek(0)

        result = cloudinary.uploader.upload(
            image,
            folder="homefixer/bookings/"
            )
        return result["secure_url"]

    def create(self, validated_data):
        request = self.context["request"]
        customer_profile = request.user.customerprofile
        serviceman = validated_data["serviceman"]

        images = validated_data.pop("images", [])

        # ⭐ DEFINE PRICE
        service_charge = serviceman.visiting_charge
        platform_fee = Decimal("20.00")
        total_cost = service_charge + platform_fee

        uploaded_urls = []

        if images:
            with ThreadPoolExecutor(max_workers=4) as executor:
                uploaded_urls = list(
                    executor.map(self.upload_to_cloudinary, images)
                )

        booking = Booking.objects.create(
            customer=customer_profile,
            image_urls=uploaded_urls if uploaded_urls else [],
            service_charge_at_booking=service_charge,
            platform_fee=platform_fee,
            total_cost=total_cost,
            **validated_data
        )

        return booking

class BookingDetailSerializer(serializers.ModelSerializer):

    serviceman_name = serializers.CharField(
        source="serviceman.user.name",
        read_only=True
    )

    serviceman_skills = serializers.SerializerMethodField()

    service_charge = serializers.SerializerMethodField()
    platform_fee = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()

    customer_address = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id",
            "status",
            "scheduled_date",
            "scheduled_time",
            "problem_title",
            "problem_description",
            "image_urls",
            "serviceman_name",
            "serviceman_skills",
            "customer_address",
            "service_charge",
            "platform_fee",
            "total_amount",
            "created_at",
        ]

    def get_serviceman_skills(self, obj):
        if obj.serviceman:
            return obj.serviceman.skills
        return []

    # ✅ FIXED
    def get_service_charge(self, obj):
        return obj.service_charge_at_booking

    def get_platform_fee(self, obj):
        return obj.platform_fee

    def get_total_amount(self, obj):
        return obj.total_cost

    def get_customer_address(self, obj):
        customer = obj.customer
        if not customer:
            return None

        return {
            "address": getattr(customer, "default_address", None),
            "lat": getattr(customer, "default_lat", None),
            "long": getattr(customer, "default_long", None),
        }
        
    #Booking tracking response serializer
class BookingTrackingSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    status = serializers.CharField()
    status_text = serializers.CharField()
    serviceman_name = serializers.CharField()
    serviceman_rating = serializers.FloatField()
    serviceman_lat = serializers.DecimalField(max_digits=10, decimal_places=8)
    serviceman_long = serializers.DecimalField(max_digits=11, decimal_places=8)
    customer_lat = serializers.DecimalField(max_digits=10, decimal_places=8)
    customer_long = serializers.DecimalField(max_digits=11, decimal_places=8)
    customer_address = serializers.CharField()
    distance_km = serializers.FloatField()
    eta_minutes = serializers.IntegerField()
    image_urls = serializers.ListField(
        child=serializers.URLField(),
        required=False
    )


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