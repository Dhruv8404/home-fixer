import random
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
import logging
from math import radians, cos, sin, asin, sqrt
from decimal import Decimal

import razorpay
import stripe
import cloudinary.uploader

from .models import EmailOTP, MaterialOrder, Payment

# ================== CONFIG ==================
OTP_EXPIRY_MINUTES = 5

razorpay_client = razorpay.Client(auth=(
    settings.RAZORPAY_KEY_ID,
    settings.RAZORPAY_KEY_SECRET
))

stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)

# ================== OTP ==================
def generate_otp():
    return str(random.randint(100000, 999999))


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

    import requests
    print(f"📧 Email: {email} | OTP: {otp}")
    
    try:
        send_mail(
            subject=f'Your HomeFixer OTP: {otp}',
            message=f'Your OTP is: {otp}. Valid for 5 minutes.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        print(f"✅ Email sent to {email}")
        return {"success": True, "otp": otp}
    except Exception as e:
        print(f"❌ SMTP failed for {email}: {str(e)}")
        
        # Fallback Resend via requests
        resend_api_key = getattr(settings, 'RESEND_API_KEY', None)
        print("RESEND:", resend_api_key)
        if resend_api_key:
            try:
                response = requests.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {resend_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": "onboarding@resend.dev",
                        "to": [email],
                        "subject": "Your OTP Code",
                        "html": f"<strong>Your OTP is {otp}</strong>"
                    }
                )
                if response.status_code in [200, 201]:
                    print(f"✅ Resend delivered to {email}")
                    return {"success": True, "otp": otp}
                else:
                    err_msg = f"Resend API error: {response.text}"
                    print(err_msg)
                    return {"success": False, "error": err_msg}
            except Exception as resend_e:
                err_msg = f"Resend request failed: {str(resend_e)}"
                print(err_msg)
                return {"success": False, "error": err_msg}
        else:
            err_msg = "SMTP failed and RESEND_API_KEY is not set"
            print("ℹ️ Set RESEND_API_KEY for Railway emails")
            return {"success": False, "error": err_msg}


def verify_email_otp(email, otp):
    expiry_time = timezone.now() - timedelta(minutes=OTP_EXPIRY_MINUTES)

    record = EmailOTP.objects.filter(
        email=email,
        otp=otp,
        created_at__gte=expiry_time
    ).first()

    if not record:
        return False

    record.is_verified = True
    record.save()
    return True


# ================== DISTANCE ==================
def distance_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * asin(sqrt(a))


# ================== CLOUDINARY ==================
def delete_cloudinary_image(field):
    if not field:
        return

    try:
        public_id = getattr(field, "public_id", None)
        if public_id:
            cloudinary.uploader.destroy(public_id)
    except Exception as e:
        logger.warning(f"Cloudinary delete failed: {str(e)}")


# ================== BOOKING TOTAL ==================
def calculate_booking_total(booking):
    approved_total = Decimal("0.00")

    for item in booking.items.filter(approval_status="APPROVED"):
        approved_total += item.quantity * item.product_price

    booking.total_cost = (
        booking.visiting_charge +
        booking.service_charge +
        booking.platform_fee +
        approved_total
    )

    booking.save(update_fields=["total_cost"])
    return booking.total_cost


# ================== AUTO REJECT ==================
def auto_reject_orders():
    orders = MaterialOrder.objects.filter(status="REQUESTED")

    for order in orders:
        if timezone.now() - order.created_at >= timedelta(minutes=2):
            order.status = "AUTO_REJECTED"
            order.save()


# ================== PAYMENT (🔥 MAIN LOGIC) ==================
def create_payment(booking, payment_type, gateway):
    """
    payment_type: VISITING or FINAL
    gateway: RAZORPAY or STRIPE
    """

    # 🔥 CREATE PAYMENT (amount auto-calculated from model)
    payment = Payment.objects.create(
        booking=booking,
        customer=booking.customer,
        payment_type=payment_type,
        gateway=gateway,
        status="PENDING"
    )

    amount = payment.amount  # auto calculated

    try:
        # ================== RAZORPAY ==================
        if gateway == "RAZORPAY":
            try:
                order = razorpay_client.order.create({
                    "amount": int(float(amount) * 100),
                    "currency": "INR",
                    "payment_capture": 1,
                    "notes": {
                        "booking_id": str(booking.id),
                        "payment_type": str(payment_type)
                    }
                })
            except Exception as e:
                # 🔥 Fallback for Swagger Testing if real keys are locked/invalid
                logger.warning(f"Razorpay real API failed ({str(e)}), using MOCK order!")
                order = {
                    "id": f"order_mock_{booking.id}_{int(timezone.now().timestamp())}",
                    "amount": int(float(amount) * 100),
                    "currency": "INR"
                }

            payment.gateway_order_id = order["id"]
            payment.save(update_fields=["gateway_order_id"])

            return payment, order

        # ================== STRIPE ==================
        elif gateway == "STRIPE":
            intent = stripe.PaymentIntent.create(
                amount=int(float(amount) * 100),
                currency="inr",
                metadata={
                    "booking_id": booking.id,
                    "payment_type": payment_type
                },
                # 🔥 AUTO CONFIRM FOR SWAGGER TESTING
                payment_method="pm_card_visa",
                confirm=True,
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"}
            )

            payment.gateway_order_id = intent["id"]
            payment.save(update_fields=["gateway_order_id"])

            return payment, intent

    except Exception as e:
        logger.error(f"Payment error: {str(e)}")
        return None, str(e)