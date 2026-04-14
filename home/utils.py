import random
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
    """Attempt delivery via Django's configured SMTP backend."""
    smtp_host = getattr(settings, 'EMAIL_HOST', None)
    smtp_user = getattr(settings, 'EMAIL_HOST_USER', None)
    smtp_pass = getattr(settings, 'EMAIL_HOST_PASSWORD', None)

    if not (smtp_host and smtp_user and smtp_pass):
        msg = f"⚠️  SMTP not configured (host={smtp_host}, user={'set' if smtp_user else 'MISSING'}, pass={'set' if smtp_pass else 'MISSING'})"
        logger.warning(msg)
        print(msg)
        return {"success": False, "error": "SMTP credentials not configured"}

    try:
        msg = EmailMultiAlternatives(
            subject="Your HomeFixer OTP",
            body=plain_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
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


# ================== PAYMENT VALIDATION (NEW) ==================
def can_create_payment(booking, payment_type, user):
    """
    Centralized validation for 2-step payment system:
    1. Customer ownership check
    2. No duplicate VISITING payment
    3. FINAL only after VISITING paid
    4. No duplicate FINAL payment
    """
    # 1. Customer ownership
    if booking.customer.user != user:
        return False, "This booking does not belong to you"
    
    # 2. VISITING: Prevent duplicate
    if payment_type == "VISITING":
        if booking.payments.filter(
            payment_type__in=["VISITING", "VISITING_SERVICE"], 
            status="PAID"
        ).exists():
            return False, "Visiting payment already completed"
    
    # 3. FINAL: Must have visiting paid first
    elif payment_type == "FINAL":
        # Check visiting paid
        if not booking.payments.filter(
            payment_type__in=["VISITING", "VISITING_SERVICE"], 
            status="PAID"
        ).exists():
            return False, "Complete visiting payment first"
        
        # Prevent duplicate final
        if booking.payments.filter(
            payment_type="FINAL", 
            status="PAID"
        ).exists():
            return False, "Final payment already completed"
    
    # 4. Booking must be in valid state
    if booking.status in ["CANCELLED", "COMPLETED"]:
        return False, "Booking cannot accept payments"
    
    return True, None


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
                
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"}
            )

            payment.gateway_order_id = intent["id"]
            payment.save(update_fields=["gateway_order_id"])

            return payment,{"client_secret": intent.client_secret}

    except Exception as e:
        logger.error(f"Payment error: {str(e)}")
        return None, str(e)