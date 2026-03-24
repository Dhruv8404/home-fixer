from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from cloudinary.models import CloudinaryField
from rest_framework import serializers
#=============user model manager==================
class UserManager(BaseUserManager):
    def create_user(self, email, phone, password=None, role='CUSTOMER'):
        if not email:
            raise ValueError("Email is required")

        user = self.model(
            email=self.normalize_email(email),
            phone=phone,
            role=role,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone, password):
        user = self.create_user(email, phone, password, role='ADMIN')
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user



class EmailOTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - {self.otp}"





class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('CUSTOMER', 'Customer'),
        ('SERVICEMAN', 'Serviceman'),
        ('VENDOR', 'Vendor'),
        ('ADMIN', 'Admin'),
    ]

    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_verified = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone']

    def __str__(self):
        return self.email



class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    default_address = models.TextField(blank=True, null=True)
    default_lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    default_long = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)

    profile_image = CloudinaryField(
        'image',
        folder='home_fixer/customers/',
        null=True,
        blank=True
    )
#---------serviceman profile changes start here------------------#

class ServicemanProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    is_online = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    current_lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    current_long = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)

    # 🔵 LIVE LOCATION (NEW)
    live_lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    live_long = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    experience_years = models.IntegerField(default=0)

    # ✅ NEW: Visiting Charges
    visiting_charge = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    default=0
)

    # ✅ NEW: Skills (stored as JSON list)
    skills = models.JSONField(default=list, blank=True)

    average_rating = models.FloatField(default=0.0)

    # ✅ Profile Image
    profile_image = CloudinaryField(
        'image',
        folder='home_fixer/servicemen/',
        null=True,
        blank=True
    )

    # ✅ KYC Document Image Upload (Cloudinary Image)
    kyc_document = CloudinaryField(
        'image',
        folder='home_fixer/servicemen/kyc/',
        null=True,
        blank=True
    )

class VendorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    is_approved = models.BooleanField(default=False)  # ✅ NEW FIELD
    # ========================
    # BUSINESS DETAILS
    # ========================
    business_name = models.CharField(max_length=255)
    gst_number = models.CharField(max_length=50, blank=True, null=True)

    contact_number = models.CharField(max_length=20, blank=True, null=True)
    business_email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)   # ✅ ADD THIS
    opening_time = models.TimeField(blank=True, null=True)
    closing_time = models.TimeField(blank=True, null=True)

    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)

    full_address = models.TextField(blank=True, null=True)

    store_lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    store_long = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)

    # ========================
    # BANK DETAILS
    # ========================
    account_holder_name = models.CharField(max_length=255, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    upi_id = models.CharField(max_length=100, blank=True, null=True)

    # ========================
    # DOCUMENTS (Cloudinary)
    # ========================
    gst_certificate = CloudinaryField(
        'file',
        folder='home_fixer/vendor_documents/gst/',
        null=True,
        blank=True
    )

    store_registration = CloudinaryField(
        'file',
        folder='home_fixer/vendor_documents/store_registration/',
        null=True,
        blank=True
    )

    id_proof = CloudinaryField(
        'file',
        folder='home_fixer/vendor_documents/id_proof/',
        null=True,
        blank=True
    )

    # ========================
    # PROFILE IMAGE
    # ========================
    profile_image = CloudinaryField(
        'image',
        folder='home_fixer/vendors/',
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.business_name


class Category(models.Model):
    TYPE_CHOICES = (
        ("SERVICE", "Service"),
        ("PRODUCT", "Product"),
    )

    name = models.CharField(max_length=100)
    category_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES
    )

    def __str__(self):
        return f"{self.name} ({self.category_type})"





class Service(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    def __str__(self):
        return self.name

class Serviceman(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    is_active = models.BooleanField(default=True)
#End of Changes#



class ServicemanOffering(models.Model):
    serviceman = models.ForeignKey(ServicemanProfile, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    custom_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)




class Booking(models.Model):

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    serviceman = models.ForeignKey(
        ServicemanProfile, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # 👇 NEW FIELDS (Booking Form)
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    problem_title = models.CharField(max_length=255)
    problem_description = models.TextField()
    image_urls = models.JSONField(default=list, blank=True)

     # ⭐ PRICE SNAPSHOT (NEW)
    service_charge_at_booking = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

        # ✅ ADD THIS ABOVE payment_status
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
    ]

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING'
    )
    def __str__(self):
        return f"Booking #{self.id}"
    
    def update_total_cost(self):
        product_total = sum([
        item.get_total_price()
        for item in self.items.filter(is_approved=True)
    ])
        self.total_cost = self.service_charge_at_booking + product_total
        self.save()
    
class BookingImage(models.Model):

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="images"
    )

    image = CloudinaryField(
        'image',
        folder='home_fixer/bookings/',
        null=True,
        blank=True
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for Booking {self.booking.id}"





class Product(models.Model):
    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    min_stock_alert = models.IntegerField(default=5)
    image = CloudinaryField(
    'image',
    folder='home_fixer/products/',
    null=True,
    blank=True
)

    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class BookingItem(models.Model):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        null=True,  
        on_delete=models.PROTECT
    )

    quantity = models.PositiveIntegerField(default=1)
    price_at_booking = models.DecimalField(max_digits=10, decimal_places=2)

    is_approved = models.BooleanField(default=False)

    def get_total_price(self):
        return self.quantity * self.price_at_booking



class MaterialOrder(models.Model):
    STATUS_CHOICES = [('REQUESTED','Requested'),('APPROVED','Approved'),('REJECTED','Rejected'),('FULFILLED','Fulfilled')]
    URGENCY_CHOICES = [('HIGH','High'),('MEDIUM','Medium'),('LOW','Low')]

    booking = models.ForeignKey(Booking, null=True, blank=True, on_delete=models.SET_NULL)
    serviceman = models.ForeignKey(ServicemanProfile, on_delete=models.CASCADE)
    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED')
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='MEDIUM')
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



class MaterialOrderItem(models.Model):
    order = models.ForeignKey(MaterialOrder, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2)



class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)



class Transaction(models.Model):
    TYPE_CHOICES = [('CREDIT','Credit'),('DEBIT','Debit')]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    booking = models.ForeignKey(Booking, null=True, blank=True, on_delete=models.SET_NULL)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)



class Review(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    reviewer = models.ForeignKey(User, related_name='given_reviews', on_delete=models.CASCADE)
    reviewee = models.ForeignKey(User, related_name='received_reviews', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)