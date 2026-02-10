import random
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import EmailOTP


def generate_otp():
    return str(random.randint(100000, 999999))


def send_email_otp(email):
    otp = generate_otp()

    EmailOTP.objects.create(
        email=email,
        otp=otp
    )

    # 🔥 ALWAYS PRINT OTP (DEV + PRODUCTION)
    print("====================================")
    print(f"🔐 OTP GENERATED")
    print(f"📧 Email : {email}")
    print(f"🔢 OTP   : {otp}")
    print("====================================")

    try:
        send_mail(
            subject="Your HomeFixer OTP",
            message=f"Your OTP is {otp}. It is valid for 5 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,  # ✅ FIX
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        # 🔥 prevents 500 and shows real issue
        print("❌ EMAIL SEND ERROR:", str(e))

def verify_email_otp(email, otp):
    expiry_time = timezone.now() - timedelta(minutes=5)

    record = EmailOTP.objects.filter(
        email=email,
        otp=otp,
        is_verified=False,
        created_at__gte=expiry_time
    ).first()

    if not record:
        return False

    record.is_verified = True
    record.save()
    return True
