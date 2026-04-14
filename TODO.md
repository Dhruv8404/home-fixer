# Payment Integration TODO

## Current Progress: ✅ Steps 1-4 Complete

```
✅ Step 1: Serializers - home/serializers.py
✅ Step 2: Utils - home/utils.py  
✅ Step 3: Views - home/views.py
✅ Step 4: URLs - home/urls.py
```

## Remaining Steps:

### Step 5: [ ] Test Endpoints Locally
```bash
# 1. Check payment status
GET /booking/1/payment/status/

# 2. Pre-flight validation  
POST /booking/1/payment/can-create/ {"payment_type": "VISITING"}

# 3. Create Stripe payment (test mode)
POST /booking/1/payment/create/ 
{
  "payment_type": "VISITING", 
  "gateway": "STRIPE"
}

# 4. Verify payment (after Stripe Elements)
POST /payment/stripe/verify/ {"payment_intent_id": "pi_xxx"}
```

### Step 6: [ ] Production Webhooks
```
Stripe Dashboard → Add Endpoint:
POST /payment/stripe/webhook/

Razorpay Dashboard → Webhook URL:
POST /payment/razorpay/webhook/
```

## 🎉 Endpoints Ready:

```
✅ POST /booking/{id}/payment/create/ - Create payment
✅ POST /payment/stripe/verify/ - Verify Stripe  
✅ POST /payment/razorpay/verify/ - Verify Razorpay
✅ GET /booking/{id}/payment/status/ - Check status
✅ POST /booking/{id}/payment/can-create/ - Pre-flight
```

**Next Action:** Test endpoints (Step 5)
