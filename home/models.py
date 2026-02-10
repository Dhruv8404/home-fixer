from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


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
    profile_pic_url = models.URLField(max_length=2048, null=True, blank=True)




class ServicemanProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    is_online = models.BooleanField(default=False)
    current_lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    current_long = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    experience_years = models.IntegerField(default=0)
    kyc_docs_url = models.URLField(max_length=2048, null=True, blank=True)
    average_rating = models.FloatField(default=0.0)



class VendorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    business_name = models.CharField(max_length=255)
    gst_number = models.CharField(max_length=50, blank=True, null=True)
    store_address = models.TextField(blank=True, null=True)
    store_lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    store_long = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    opening_hours = models.CharField(max_length=100, blank=True, null=True)
    bank_account_details = models.TextField(blank=True, null=True)




class Category(models.Model):
    TYPE_CHOICES = [('SERVICE', 'Service'), ('PRODUCT', 'Product')]

    name = models.CharField(max_length=100)
    icon_url = models.URLField(max_length=2048, null=True, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)



class Service(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)



class ServicemanOffering(models.Model):
    serviceman = models.ForeignKey(ServicemanProfile, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    custom_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)




class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE)
    serviceman = models.ForeignKey(ServicemanProfile, on_delete=models.CASCADE)
    scheduled_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    total_labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_material_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    job_location_address = models.TextField(null=True, blank=True)
    job_lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    job_long = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



class BookingItem(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    price_at_booking = models.DecimalField(max_digits=10, decimal_places=2)



class Product(models.Model):
    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    min_stock_alert = models.IntegerField(default=5)
    image_url = models.URLField(max_length=2048, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)




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
