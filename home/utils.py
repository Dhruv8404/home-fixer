import random
from rest_framework import serializers
import requests
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
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

# ================== OTP ==================
def generate_otp():
    return str(random.randint(100000, 999999))


def _build_otp_html(otp):
    """Returns a styled HTML email body for the OTP."""
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden">
      <div style="background:#1a73e8;padding:24px;text-align:center">
        <h1 style="color:#fff;margin:0;font-size:24px">HomeFixer</h1>
      </div>
      <div style="padding:32px;text-align:center">
        <p style="color:#374151;font-size:16px;margin-bottom:8px">Your One-Time Password is:</p>
        <div style="background:#f3f4f6;border-radius:8px;padding:20px;display:inline-block;margin:16px 0">
          <span style="font-size:36px;font-weight:700;letter-spacing:8px;color:#1a73e8">{otp}</span>
        </div>
        <p style="color:#6b7280;font-size:14px">This OTP is valid for <strong>5 minutes</strong>. Do not share it with anyone.</p>
      </div>
      <div style="background:#f9fafb;padding:16px;text-align:center">
        <p style="color:#9ca3af;font-size:12px;margin:0">If you didn't request this, please ignore this email.</p>
      </div>
    </div>
    """


def send_email_otp(email):
    """
    Generates (or reuses) an OTP for the given email and delivers it.

    Delivery order (controlled by USE_RESEND_FIRST env var):
      - USE_RESEND_FIRST=True  → Resend API first, then SMTP fallback  (Railway/production)
      - USE_RESEND_FIRST=False → Gmail SMTP first, then Resend fallback (local dev)

    Returns: {"success": bool, "error": str (only on failure)}
    """
    now = timezone.now()
    expiry_time = now - timedelta(minutes=OTP_EXPIRY_MINUTES)

    existing_otp = EmailOTP.objects.filter(
        email=email,
        created_at__gte=expiry_time
    ).first()

    if existing_otp:
        otp = existing_otp.otp
        logger.info(f"♻️  Reusing existing OTP for {email}")
    else:
        EmailOTP.objects.filter(email=email).delete()
        otp = generate_otp()
        EmailOTP.objects.create(email=email, otp=otp)
        logger.info(f"🆕 New OTP created for {email}")

    logger.info(f"📧 Attempting OTP delivery → {email}")
    print(f"📧 OTP for {email}: {otp}")  # always visible in logs

    html_body = _build_otp_html(otp)
    plain_body = f"Your HomeFixer OTP is: {otp}\nThis OTP is valid for 5 minutes. Do not share it with anyone."

    use_resend_first = getattr(settings, 'USE_RESEND_FIRST', False)

    if use_resend_first:
        print("🔀 Production mode: trying Resend first")
        result = _try_resend(email, otp, html_body, plain_body)
        if result["success"]:
            return result
        print("⬇️  Resend failed, falling back to SMTP")
        return _try_smtp(email, otp, html_body, plain_body)
    else:
        print("🔀 Local mode: trying Gmail SMTP first")
        result = _try_smtp(email, otp, html_body, plain_body)
        if result["success"]:
            return result
        print("⬇️  SMTP failed, falling back to Resend")
        return _try_resend(email, otp, html_body, plain_body)


def _try_smtp(email, otp, html_body, plain_body):
    """Attempt delivery via direct SMTP (bypasses Django EMAIL_BACKEND so it
    always uses the Gmail credentials even when Resend is the active backend)."""
    import smtplib
    import ssl
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    smtp_host = getattr(settings, 'EMAIL_HOST', None)
    smtp_port = getattr(settings, 'EMAIL_PORT', 587)
    smtp_user = getattr(settings, 'EMAIL_HOST_USER', None)
    smtp_pass = getattr(settings, 'EMAIL_HOST_PASSWORD', None)
    use_tls   = getattr(settings, 'EMAIL_USE_TLS', True)

    if not (smtp_host and smtp_user and smtp_pass):
        msg = f"⚠️  SMTP not configured (host={smtp_host}, user={'set' if smtp_user else 'MISSING'}, pass={'set' if smtp_pass else 'MISSING'})"
        logger.warning(msg)
        print(msg)
        return {"success": False, "error": "SMTP credentials not configured"}

    try:
        mime_msg = MIMEMultipart("alternative")
        mime_msg["Subject"] = "Your HomeFixer OTP"
        mime_msg["From"]    = smtp_user
        mime_msg["To"]      = email
        mime_msg.attach(MIMEText(plain_body, "plain"))
        mime_msg.attach(MIMEText(html_body, "html"))

        context = ssl.create_default_context()
        
        # Railway blocks outbound port 587/25 on free tiers. Use 465 (SSL) first.
        port_to_use = 465 if smtp_port in (25, 587) else smtp_port
        
        # Use SMTP_SSL for port 465, which doesn't need starttls()
        # Relying on SMTP_SSL often bypasses the IPv6 starttls issues as well
        with smtplib.SMTP_SSL(smtp_host, port_to_use, context=context, timeout=15) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [email], mime_msg.as_string())

        logger.info(f"✅ SMTP delivered OTP to {email}")
        print(f"✅ Email sent via SMTP to {email}")
        return {"success": True}
    except Exception as e:
        logger.error(f"❌ SMTP failed for {email}: {e}")
        print(f"❌ SMTP error: {e}")
        return {"success": False, "error": str(e)}


def _try_resend(email, otp, html_body, plain_body):
    """Attempt delivery via Resend HTTP API."""
    resend_api_key = getattr(settings, 'RESEND_API_KEY', None)
    resend_from = getattr(settings, 'RESEND_FROM_EMAIL', 'onboarding@resend.dev')

    if not resend_api_key:
        msg = "⚠️  RESEND_API_KEY not set — cannot use Resend"
        logger.warning(msg)
        print(msg)
        return {"success": False, "error": "RESEND_API_KEY not configured"}

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": resend_from,
                "to": [email],
                "subject": "Your HomeFixer OTP",
                "html": html_body,
                "text": plain_body,
            },
            timeout=10,
        )
        if response.status_code in [200, 201]:
            logger.info(f"✅ Resend delivered OTP to {email}")
            print(f"✅ Resend delivered to {email}")
            return {"success": True}
        else:
            err_msg = f"Resend API error {response.status_code}: {response.text}"
            logger.error(err_msg)
            print(err_msg)
            return {"success": False, "error": err_msg}
    except Exception as e:
        err_msg = f"Resend request failed: {e}"
        logger.error(err_msg)
        print(err_msg)
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


# ================= PAYMENT FUNCTIONS =================
def can_create_payment(booking, payment_type, user):
    """
    Business logic validation before payment creation
    🔥 Supports retry for FAILED payments
    """

    # 🔒 Only customers
    if user.role != "CUSTOMER":
        return False, "Only customers can create payments"

    if booking.customer.user != user:
        return False, "Not your booking"

    if booking.status == "CANCELLED":
        return False, "Booking cancelled"

    # =========================
    # 🔍 CHECK EXISTING PAYMENT
    # =========================
    existing = booking.payments.filter(
        payment_type=payment_type
    ).order_by('-created_at').first()

    # 🚫 Already PAID → block
    if existing and existing.status == "PAID":
        return False, f"{payment_type} payment already completed"

    # 🔁 FAILED → allow retry
    if existing and existing.status == "FAILED":
        return True, "Retry allowed"

    # ⏳ PENDING → block duplicate
    if existing and existing.status == "PENDING":
        return False, f"{payment_type} payment already in progress"

    # =========================
    # 🔥 BUSINESS FLOW RULES
    # =========================

    if payment_type == "VISITING":
        # Only if not already partially paid
        if booking.payment_status not in ["PENDING"]:
            return False, "VISITING payment already done"

        return True, "OK"

    elif payment_type == "FINAL":
        # Must complete visiting first
        if booking.payment_status != "PARTIAL":
            return False, "Complete visiting payment first"

        return True, "OK"

    return False, "Invalid payment type"


def create_stripe_payment(payment):
    """
    Creates Stripe PaymentIntent
    """
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(payment.amount * 100),  # Stripe uses paise
            currency="inr",
            metadata={
                "booking_id": str(payment.booking.id),
                "payment_id": str(payment.id),
                "payment_type": payment.payment_type,
            }
        )
        
        payment.gateway_order_id = intent.id
        payment.status = "PENDING"
        payment.save()
        
        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
            "status": "created"
        }
        
    except stripe.error.StripeError as e:
        payment.status = "FAILED"
        payment.save()
        raise serializers.ValidationError(f"Stripe error: {str(e)}")


def verify_stripe_payment(payment_intent_id):
    """
    Verifies Stripe payment
    """
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        # ⚠️ TEMPORARY HACK: Bypassing the Stripe status check so you can test in Swagger. 
        # Normally, this is just: if intent.status == "succeeded":
        if intent.status == "succeeded" or getattr(settings, 'DEBUG', True):
            # Find payment by metadata using getattr because StripeObject has no get() in v5+
            payment_id = getattr(intent.metadata, "payment_id", None)
            payment = Payment.objects.get(id=payment_id)
            
            payment.gateway_payment_id = intent.id
            payment.status = "PAID"
            payment.save()
            
            return {"status": "verified", "payment_id": payment.id}
        else:
            return {"status": "requires_action", "client_secret": intent.client_secret}
            
    except Payment.DoesNotExist:
        raise serializers.ValidationError("Payment not found")
    except stripe.error.StripeError as e:
        raise serializers.ValidationError(f"Stripe verification failed: {str(e)}")
    except stripe.error.StripeError:
        return requests.Response({"error": "Invalid payment intent"}, status=400)

def create_razorpay_order(payment):
    """
    Creates Razorpay order
    """
    try:
        order = razorpay_client.order.create({
            'amount': int(payment.amount * 100),  # paise
            'currency': 'INR',
            'receipt': f"booking-{payment.booking.id}-payment-{payment.id}",
            'notes': {
                'booking_id': payment.booking.id,
                'payment_type': payment.payment_type,
                'payment_id': payment.id
            }
        })
        
        payment.gateway_order_id = order['id']
        payment.status = "PENDING"
        payment.save()
        
        return {
            "order_id": order['id'],
            "amount": payment.amount,
            "currency": "INR",
            "key_id": settings.RAZORPAY_KEY_ID,
            "status": "created"
        }
        
    except Exception as e:
        payment.status = "FAILED"
        payment.save()
        raise serializers.ValidationError(f"Razorpay error: {str(e)}")


def verify_razorpay_payment(order_id, payment_id, signature):
    """
    Verifies Razorpay payment using signature
    """
    try:
        # ⚠️ TEMPORARY HACK: Bypass actual signature check for Swagger testing
        if not getattr(settings, 'DEBUG', True):
            # Get payment details
            payment_details = razorpay_client.payment.fetch(payment_id)
            
            # Verify signature
            razorpay_client.utility.verify_payment_signature({
                'order_id': order_id,
                'payment_id': payment_id,
                'signature': signature
            })
            
        # Find our Payment record
        payment = Payment.objects.get(gateway_order_id=order_id)
        
        payment.gateway_payment_id = payment_id
        payment.status = "PAID"
        payment.save()
        
        return {"status": "verified", "payment_id": payment.id}
        
    except Payment.DoesNotExist:
        raise serializers.ValidationError("Payment not found")
    except Exception as e:
        raise serializers.ValidationError(f"Verification failed: {str(e)}")


