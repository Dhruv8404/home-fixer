from django.db import migrations
from django.contrib.auth.hashers import make_password

def create_default_users(apps, schema_editor):
    User = apps.get_model('home', 'User')

    users = [
    {
        "email": "admin@gmail.com",
        "password": make_password("Admin@123"),
        "role": "admin",
        "phone": "9000000001",
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "email": "customer@gmail.com",
        "password": make_password("Customer@123"),
        "role": "customer",
        "phone": "9000000002",
    },
    {
        "email": "serviceman@gmail.com",
        "password": make_password("Service@123"),
        "role": "serviceman",
        "phone": "9000000003",
    },
    {
        "email": "vendor@gmail.com",
        "password": make_password("Vendor@123"),
        "role": "vendor",
        "phone": "9000000004",
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
