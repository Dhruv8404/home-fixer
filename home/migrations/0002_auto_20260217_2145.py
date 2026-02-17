from django.db import migrations
from django.contrib.auth.hashers import make_password

def create_default_users(apps, schema_editor):
    User = apps.get_model('home', 'User')

    users = [
    {
        "email": "admin@gmail.com",
        "phone": "9000000001",
        "password": make_password("Admin@123"),
        "role": "ADMIN",
        "name": "Admin User",
        "is_staff": True,
        "is_superuser": True,
        "is_verified": True,
    },
    {
        "email": "customer@gmail.com",
        "phone": "9000000002",
        "password": make_password("Customer@123"),
        "role": "CUSTOMER",
        "name": "Customer User",
        "is_verified": True,
    },
    {
        "email": "serviceman@gmail.com",
        "phone": "9000000003",
        "password": make_password("Service@123"),
        "role": "SERVICEMAN",
        "name": "Serviceman User",
        "is_verified": True,
    },
    {
        "email": "vendor@gmail.com",
        "phone": "9000000004",
        "password": make_password("Vendor@123"),
        "role": "VENDOR",
        "name": "Vendor User",
        "is_verified": True,
    },
]



    for user in users:
        User.objects.update_or_create(
            email=user["email"],
            defaults=user
        )

class Migration(migrations.Migration):

    dependencies = [
    ('home', '0001_initial'),
]


    operations = [
        migrations.RunPython(create_default_users),
    ]
