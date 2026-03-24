from decimal import Decimal
from django.contrib.auth import get_user_model
from home.models import CustomerProfile, ServicemanProfile, VendorProfile, Category, Product

User = get_user_model()

BASE_LAT = 22.5645
BASE_LON = 72.9289

def offset(i):
    return BASE_LAT + (i * 0.01), BASE_LON + (i * 0.01)

# CLEAN OLD DATA
User.objects.filter(email="admin@test.com").delete()
User.objects.filter(email__startswith="serviceman").delete()
User.objects.filter(email__startswith="vendor").delete()

# ADMIN
admin = User.objects.create_superuser(
    email="admin@test.com",
    password="admin123",
    phone="9999999999"
)
admin.role = "ADMIN"
admin.save()

# CUSTOMER
customer, _ = User.objects.get_or_create(
    email="customer@test.com",
    defaults={"phone": "8888888888", "role": "CUSTOMER"}
)

CustomerProfile.objects.get_or_create(
    user=customer,
    defaults={
        "default_address": "Anand",
        "default_lat": BASE_LAT,
        "default_long": BASE_LON
    }
)

# SERVICEMEN
servicemen = []
for i in range(4):
    user = User.objects.create_user(
        email=f"serviceman{i}@test.com",
        password="123456",
        phone=f"77777777{i}",
        role="SERVICEMAN"
    )

    lat, lon = offset(i)

    profile = ServicemanProfile.objects.create(
        user=user,
        is_active=True,
        is_approved=True,
        current_lat=lat,
        current_long=lon,
        visiting_charge=Decimal("100.00"),
        skills=["Plumbing"]
    )

    servicemen.append(profile)

# VENDORS
vendors = []
for i in range(4):
    user = User.objects.create_user(
        email=f"vendor{i}@test.com",
        password="123456",
        phone=f"66666666{i}",
        role="VENDOR"
    )

    lat, lon = offset(i)

    profile = VendorProfile.objects.create(
        user=user,
        is_active=True,
        is_approved=True,
        business_name=f"Shop {i}",
        city="Anand",
        state="Gujarat",
        full_address="Main Road",
        store_lat=lat,
        store_long=lon
    )

    vendors.append(profile)

# CATEGORY (fix duplicate issue)
Category.objects.filter(name="Electrical").delete()

category = Category.objects.create(
    name="Electrical",
    category_type="PRODUCT"
)

# PRODUCTS
for i in range(10):
    vendor = vendors[i % 4]

    Product.objects.create(
        vendor=vendor,
        category=category,
        name=f"Product {i}",
        price=Decimal("50.00") + i,
        stock_quantity=100,
        min_stock_alert=10,
        description="Test product"
    )

print("✅ DATA INSERTED SUCCESSFULLY")