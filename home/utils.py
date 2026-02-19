import random
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
import logging
from .models import EmailOTP

OTP_EXPIRY_MINUTES = 5


def generate_otp():
    return str(random.randint(100000, 999999))


logger = logging.getLogger(__name__)

def send_email_otp(email):
    now = timezone.now()
    expiry_time = now - timedelta(minutes=OTP_EXPIRY_MINUTES)

    existing_otp = EmailOTP.objects.filter(
        email=email,
        created_at__gte=expiry_time
    ).first()

    if existing_otp:
        otp = existing_otp.otp
    else:
        EmailOTP.objects.filter(email=email).delete()
        otp = generate_otp()
        EmailOTP.objects.create(email=email, otp=otp)

    print("====================================")
    print(f"📧 Email : {email}")
    print(f"🔢 OTP   : {otp}")
    print("====================================")


    return otp


def verify_email_otp(email, otp):
    expiry_time = timezone.now() - timedelta(minutes=OTP_EXPIRY_MINUTES)

    record = EmailOTP.objects.filter(
        email=email,
        otp=otp,
        created_at__gte=expiry_time
    ).first()

    if not record:
        return False

    # ✅ Mark as verified instead of deleting
    record.is_verified = True
    record.save()

    return True

