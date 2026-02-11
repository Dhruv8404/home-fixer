import random
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import EmailOTP

OTP_EXPIRY_MINUTES = 5


def generate_otp():
    return str(random.randint(100000, 999999))


def send_email_otp(email):
    now = timezone.now()
    expiry_time = now - timedelta(minutes=OTP_EXPIRY_MINUTES)

    # 🔍 Check existing valid OTP
    existing_otp = EmailOTP.objects.filter(
        email=email,
        created_at__gte=expiry_time
    ).first()

    if existing_otp:
        otp = existing_otp.otp  # reuse same OTP
    else:
        # ❌ Delete all old expired OTPs
        EmailOTP.objects.filter(email=email).delete()

        otp = generate_otp()
        EmailOTP.objects.create(
            email=email,
            otp=otp
        )

    # 🔥 Always print
    print("====================================")
    print(f"🔐 OTP GENERATED")
    print(f"📧 Email : {email}")
    print(f"🔢 OTP   : {otp}")
    print("====================================")

    try:
        send_mail(
            subject="Your HomeFixer OTP",
            message=f"Your OTP is {otp}. It is valid for {OTP_EXPIRY_MINUTES} minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        print("❌ EMAIL SEND ERROR:", str(e))


def verify_email_otp(email, otp):
    expiry_time = timezone.now() - timedelta(minutes=OTP_EXPIRY_MINUTES)

    record = EmailOTP.objects.filter(
        email=email,
        otp=otp,
        created_at__gte=expiry_time
    ).first()

    if not record:
        return False

    # ✅ OTP valid → delete it (IMPORTANT)
    record.delete()

    return True
