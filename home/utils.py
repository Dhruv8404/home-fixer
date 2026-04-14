import random
import requests
from datetime import timedelta
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
import logging
from math import radians, cos, sin, asin, sqrt
from decimal import Decimal

import razorpay
import stripe
import cloudinary.uploader

from .models import Booking, EmailOTP, MaterialOrder, Payment

# ================== CONFIG ==================
OTP_EXPIRY_MINUTES = 5

razorpay_client = razorpay.Client(auth=(
    settings.RAZORPAY_KEY_ID,
    settings.RAZORPAY_KEY_SECRET
))

stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)

# ================== STRIPE (✅ NEW CLEAN) ==================
def create_stripe_payment_intent(amount, booking_id, payment_type):
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(float(amount) * 100),
            currency="inr",
            metadata={
                "booking_id": str(booking_id),
                "payment_type": str(payment_type)
            },
            automatic_payment_methods={"enabled": True}
        )

        return {
            "success": True,
            "client_secret": intent["client_secret"],
            "payment_intent_id": intent["id"]
        }

    except Exception as e:
        logger.error(f"Stripe create error: {str(e)}")
        return {"success": False, "error": str(e)}


def verify_stripe_payment(payment_intent_id):
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        if intent.status == "succeeded":
            return {"success": True, "status": "PAID"}

        return {"success": False, "status": intent.status}

    except Exception as e:
        logger.error(f"Stripe verify error: {str(e)}")
        return {"success": False, "error": str(e)}


# ================== OTP ==================
def generate_otp():
    return str(random.randint(100000, 999999))


def _build_otp_html(otp):
    return f"<h2>Your OTP is {otp}</h2>"


def send_email_otp(email):
    otp = generate_otp()
    EmailOTP.objects.update_or_create(
        email=email,
        defaults={"otp": otp}
    )

    try:
        msg = EmailMultiAlternatives(
            subject="OTP",
            body=f"Your OTP is {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        msg.attach_alternative(_build_otp_html(otp), "text/html")
        msg.send()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def verify_email_otp(email, otp):
    return EmailOTP.objects.filter(email=email, otp=otp).exists()


# ================== DISTANCE ==================
def distance_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * asin(sqrt(a))


# ================== CLOUDINARY ==================
def delete_cloudinary_image(field):
    if field and getattr(field, "public_id", None):
        try:
            cloudinary.uploader.destroy(field.public_id)
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


# ================== PAYMENT VALIDATION ==================
def can_create_payment(booking, payment_type, user):

    if booking.customer.user != user:
        return False, "Unauthorized"

    if payment_type == "VISITING":
        if booking.payments.filter(status="PAID").exists():
            return False, "Already paid"

    if booking.status in ["CANCELLED", "COMPLETED"]:
        return False, "Invalid booking state"

    return True, None


# ================== MAIN PAYMENT ==================
def create_payment(booking, payment_type, gateway):

    payment = Payment.objects.create(
        booking=booking,
        customer=booking.customer,
        payment_type=payment_type,
        gateway=gateway,
        status="PENDING"
    )

    amount = payment.amount

    try:
        # ✅ RAZORPAY
        if gateway == "RAZORPAY":
            order = razorpay_client.order.create({
                "amount": int(float(amount) * 100),
                "currency": "INR",
                "payment_capture": 1
            })

            payment.gateway_order_id = order["id"]
            payment.save()

            return payment, order

        # ✅ STRIPE (CLEAN)
        elif gateway == "STRIPE":

            stripe_data = create_stripe_payment_intent(
                amount,
                booking.id,
                payment_type
            )

            if not stripe_data["success"]:
                return None, stripe_data["error"]

            payment.gateway_order_id = stripe_data["payment_intent_id"]
            payment.save()

            return payment, stripe_data

    except Exception as e:
        logger.error(f"Payment error: {str(e)}")
        return None, str(e)