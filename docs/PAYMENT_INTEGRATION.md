# Payment Integration Documentation

## Overview

Oropendola AI uses a comprehensive payment system with support for multiple payment gateways. The system handles subscription payments, abandoned payment recovery, and retry logic.

## Payment Flow States

### Subscription Status Flow
```
Signup with Plan
    ↓
【Pending】→ Awaiting payment
    ↓ (Payment initiated)
【Processing】→ User redirected to gateway
    ↓
    ├─→ Success → 【Active】
    ├─→ Failed → 【Past Due】→ Can retry (3 attempts)
    ├─→ Abandoned (30min timeout) → 【Abandoned】→ Can retry (3 attempts)
    └─→ Time passes → 【Expired】→ Can renew
```

### Invoice Status Flow
```
【Draft】→ Initial creation (not used currently)
    ↓
【Pending】→ Awaiting payment initiation
    ↓
【Processing】→ User redirected to payment gateway
    ↓
    ├─→ Payment Success → 【Paid】
    ├─→ Payment Failed → 【Failed】→ Retry (max 3)
    ├─→ No response 30min → 【Abandoned】→ Retry (max 3)
    ├─→ User action → 【Cancelled】
    └─→ Refund → 【Refunded】
```

## Payment State Transitions

### 1. Pending → Processing
**Trigger:** User initiates payment
**API:** `POST /api/method/oropendola_ai.oropendola_ai.api.payment.initiate_payment`
**Action:** Invoice marked as Processing, user redirected to gateway

### 2. Processing → Paid
**Trigger:** PayU success callback
**API:** `POST /api/method/oropendola_ai.oropendola_ai.api.payment.payu_success`
**Action:**
- Invoice marked as Paid
- Subscription activated
- Daily quota set to full
- Email notification sent

### 3. Processing → Failed
**Trigger:** PayU failure callback
**API:** `POST /api/method/oropendola_ai.oropendola_ai.api.payment.payu_failure`
**Action:**
- Invoice marked as Failed
- Subscription set to Past Due
- User can retry (max 3 attempts)

### 4. Processing → Abandoned
**Trigger:** 30-minute timeout (background job)
**Function:** `check_abandoned_payments()`
**Action:**
- Invoice marked as Abandoned
- User notified to retry
- Retry count preserved

### 5. Failed/Abandoned → Pending (Retry)
**Trigger:** User clicks retry
**API:** `POST /api/method/oropendola_ai.oropendola_ai.api.payment.retry_payment`
**Action:**
- Retry counter incremented
- Status reset to Pending
- New payment initiation

## API Endpoints

### 1. Get Available Payment Gateways
```http
GET /api/method/oropendola_ai.oropendola_ai.api.payment.get_available_gateways
```

**Response:**
```json
{
  "success": true,
  "gateways": [
    {
      "id": "payu",
      "name": "PayU",
      "available": true,
      "recommended": true,
      "methods": ["upi", "cards", "netbanking", "wallets"]
    }
  ],
  "default": "payu"
}
```

### 2. Create Subscription and Invoice
```http
POST /api/method/oropendola_ai.oropendola_ai.api.payment.create_subscription_and_invoice
Content-Type: application/json

{
  "plan_id": "1-month-unlimited"
}
```

**Response:**
```json
{
  "success": true,
  "is_free": false,
  "subscription_id": "SUB-2025-00001",
  "invoice_id": "INV-2025-00001",
  "amount": 2500.0,
  "currency": "INR"
}
```

### 3. Initiate Payment
```http
POST /api/method/oropendola_ai.oropendola_ai.api.payment.initiate_payment
Content-Type: application/json

{
  "invoice_id": "INV-2025-00001",
  "gateway": "payu"
}
```

**Response:**
```json
{
  "success": true,
  "payment_url": "https://test.payu.in/_payment",
  "payment_data": {
    "key": "Er62CB",
    "txnid": "OROINV202500001",
    "amount": "2500.00",
    "productinfo": "1 Month Unlimited Subscription",
    "firstname": "John",
    "email": "john@example.com",
    "phone": "9876543210",
    "surl": "https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.payment.payu_success",
    "furl": "https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.payment.payu_failure",
    "hash": "..."
  }
}
```

### 4. Retry Failed/Abandoned Payment
```http
POST /api/method/oropendola_ai.oropendola_ai.api.payment.retry_payment
Content-Type: application/json

{
  "invoice_id": "INV-2025-00001",
  "gateway": "payu"
}
```

**Response:**
```json
{
  "success": true,
  "payment_url": "...",
  "payment_data": {...},
  "retry_count": 1,
  "retries_remaining": 2
}
```

### 5. Get Pending Invoices
```http
GET /api/method/oropendola_ai.oropendola_ai.api.payment.get_pending_invoices
```

**Response:**
```json
{
  "success": true,
  "invoices": [
    {
      "name": "INV-2025-00001",
      "status": "Abandoned",
      "total_amount": 2500.0,
      "currency": "INR",
      "invoice_date": "2025-10-31",
      "retry_count": 0,
      "can_retry": true,
      "retries_remaining": 3
    }
  ]
}
```

### 6. PayU Bolt (Embedded Payment)
```http
POST /api/method/oropendola_ai.oropendola_ai.services.payu_gateway.create_bolt_payment
Content-Type: application/json

{
  "invoice_id": "INV-2025-00001",
  "embed_mode": true
}
```

**Response:**
```json
{
  "success": true,
  "mode": "bolt_embedded",
  "bolt_config": {
    "key": "Er62CB",
    "txnid": "OROINV202500001",
    "amount": "2500.00",
    ...
    "pg_redirect_flow": "embedded",
    "show_payment_mode": "CC,DC,NB,UPI,CASH"
  },
  "embed_mode": true,
  "instructions": {
    "embedded": "Use PayU Bolt SDK on frontend with these parameters in iframe"
  }
}
```

## Frontend Integration Examples

### Standard Redirect Flow
```javascript
async function initiatePayment(invoiceId) {
  const response = await fetch('/api/method/oropendola_ai.oropendola_ai.api.payment.initiate_payment', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      invoice_id: invoiceId,
      gateway: 'payu'
    })
  });

  const data = await response.json();

  if (data.message.success) {
    // Create form and submit to PayU
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = data.message.payment_url;

    Object.keys(data.message.payment_data).forEach(key => {
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = key;
      input.value = data.message.payment_data[key];
      form.appendChild(input);
    });

    document.body.appendChild(form);
    form.submit();
  }
}
```

### Embedded PayU Bolt Flow
```javascript
async function initiateBoltPayment(invoiceId) {
  const response = await fetch('/api/method/oropendola_ai.oropendola_ai.services.payu_gateway.create_bolt_payment', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      invoice_id: invoiceId,
      embed_mode: true
    })
  });

  const data = await response.json();

  if (data.message.success) {
    // Initialize PayU Bolt SDK
    bolt.launch(data.message.bolt_config, {
      responseHandler: function(response) {
        // Handle payment response
        if (response.response.txnStatus === 'SUCCESS') {
          window.location.href = '/payment-success';
        } else {
          window.location.href = '/payment-failed';
        }
      },
      catchException: function(error) {
        console.error('Payment error:', error);
      }
    });
  }
}
```

### Retry Payment Flow
```javascript
async function retryPayment(invoiceId) {
  const response = await fetch('/api/method/oropendola_ai.oropendola_ai.api.payment.retry_payment', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      invoice_id: invoiceId,
      gateway: 'payu'
    })
  });

  const data = await response.json();

  if (data.message.success) {
    // Redirect to payment gateway
    initiatePayment(invoiceId);
  } else {
    alert(data.message.error);
  }
}
```

## Abandoned Payment Handling

### Background Job Setup
Add to `hooks.py`:
```python
scheduler_events = {
    "cron": {
        "*/30 * * * *": [  # Every 30 minutes
            "oropendola_ai.oropendola_ai.api.payment.check_abandoned_payments"
        ]
    }
}
```

### Manual Check
```python
import frappe
from oropendola_ai.oropendola_ai.api.payment import check_abandoned_payments

# Check and mark abandoned payments
count = check_abandoned_payments()
print(f"Marked {count} invoices as abandoned")
```

## Multi-Gateway Architecture

The payment system is designed to support multiple gateways:

### Current Gateways
- **PayU** (Primary) - Indian market, UPI/Cards/NetBanking/Wallets
- **Razorpay** (Ready) - Alternative for India
- **Stripe** (Planned) - International markets
- **PayPal** (Planned) - International markets

### Adding New Gateway

1. Create gateway service file:
```python
# services/new_gateway.py
class NewGateway:
    def __init__(self):
        # Initialize with credentials
        pass

    def create_payment_request(self, invoice_id):
        # Create payment
        pass

    def verify_payment(self, response_data):
        # Verify payment
        pass

    def process_payment_success(self, response_data):
        # Handle success
        pass
```

2. Update `payment.py`:
```python
@frappe.whitelist()
def initiate_payment(invoice_id: str, gateway: str = "payu"):
    # ... existing code ...

    elif gateway == "newgateway":
        from oropendola_ai.oropendola_ai.services.new_gateway import get_gateway
        gw = get_gateway()
        return gw.create_payment_request(invoice_id)
```

3. Update `get_available_gateways()`:
```python
if new_gateway_configured:
    gateways.append({
        "id": "newgateway",
        "name": "New Gateway",
        "available": True,
        "methods": ["cards", "wallet"]
    })
```

## Testing

### Test Mode
PayU is currently in **test mode**. To switch to production:

1. Update Oropendola Settings:
   - Set `payu_mode` = "production"
   - Update credentials with production keys

2. Test scenarios:
   - ✅ Successful payment
   - ✅ Failed payment
   - ✅ Abandoned payment (wait 30 min or trigger manually)
   - ✅ Retry payment (after failed/abandoned)
   - ✅ Multiple retries (test 3-retry limit)

### Test Card Details (PayU Test Mode)
```
Card Number: 5123456789012346
CVV: 123
Expiry: Any future date
OTP: 123456
```

## Security Considerations

1. **Hash Verification**: All PayU responses are hash-verified
2. **User Authorization**: Invoice ownership verified before payment
3. **HTTPS Required**: All payment endpoints use HTTPS
4. **Encrypted Storage**: Gateway credentials stored encrypted
5. **Rate Limiting**: Retry attempts limited to 3

## Monitoring and Alerts

### Key Metrics to Monitor
- Payment success rate
- Average payment completion time
- Abandoned payment rate
- Retry success rate
- Gateway-specific failure rates

### Recommended Alerts
- Abandoned payment rate > 20%
- Payment failure rate > 10%
- Pending invoices older than 24 hours
- Gateway downtime

## Troubleshooting

### Issue: Invoice stuck in Processing
**Solution:** Run abandoned payment checker or manually mark as abandoned

### Issue: Payment successful but subscription not activated
**Check:**
1. PayU callback received? Check Error Log
2. Hash verification passed?
3. Invoice status updated to Paid?
4. Subscription status updated to Active?

### Issue: User can't retry payment
**Check:**
1. Retry count < 3?
2. Invoice status is Failed or Abandoned?
3. User owns the invoice?

## Critical Bug Fix: Auto-Activation Prevention

### Problem Identified
Previously, users were getting functional access to the platform WITHOUT completing payment because:
- Subscriptions were created with status "Pending" ✓ (correct)
- BUT `set_quota()` was giving full quota immediately ✗
- AND `create_api_key()` was creating active API keys immediately ✗
- Result: Even though subscription status was "Pending", users had full quota and API key = they could use the service without paying!

### Solution Implemented

#### 1. Modified `set_quota()` in AI Subscription
**File:** `oropendola_ai/doctype/ai_subscription/ai_subscription.py:48-61`

```python
def set_quota(self):
    """Initialize daily quota - only give quota if subscription is Active or Trial"""
    plan = frappe.get_doc("AI Plan", self.plan)
    self.daily_quota_limit = plan.requests_limit_per_day

    # Only give quota if subscription is Active, Trial, or if it's a free plan
    if self.status in ["Active", "Trial"] or (plan.price == 0 and plan.is_free):
        self.daily_quota_remaining = plan.requests_limit_per_day if plan.requests_limit_per_day > 0 else -1
    else:
        # Pending subscriptions get 0 quota until payment is completed
        self.daily_quota_remaining = 0
        frappe.logger().info(f"Subscription {self.name} is {self.status} - quota set to 0")

    self.priority_score = plan.priority_score
```

#### 2. Modified `create_api_key()` in AI Subscription
**File:** `oropendola_ai/doctype/ai_subscription/ai_subscription.py:80-118`

```python
def create_api_key(self):
    """Generate and create API key for this subscription - only for Active/Trial subscriptions"""
    # Check if we should create API key based on subscription status
    plan = frappe.get_doc("AI Plan", self.plan)

    # Only create API key if subscription is Active, Trial, or it's a free plan
    if self.status not in ["Active", "Trial"] and not (plan.price == 0 and plan.is_free):
        frappe.logger().info(f"Skipping API key creation for {self.status} subscription {self.name} - will create after payment")
        return

    # ... rest of API key creation logic
```

#### 3. Added `activate_after_payment()` Method
**File:** `oropendola_ai/doctype/ai_subscription/ai_subscription.py:166-192`

```python
def activate_after_payment(self):
    """
    Activate subscription after successful payment.
    This method is called when payment is confirmed successful.
    """
    frappe.logger().info(f"Activating subscription {self.name} after payment")

    # Set status to Active
    self.status = "Active"

    # Set quota (will now give full quota since status is Active)
    self.set_quota()

    # Create API key (will now create since status is Active)
    if not self.api_key_link:
        self.create_api_key()

    # Update last payment date
    self.last_payment_date = today()

    # Save the changes
    self.save(ignore_permissions=True)
    frappe.db.commit()

    frappe.logger().info(f"Subscription {self.name} activated successfully - Status: {self.status}, Quota: {self.daily_quota_remaining}, API Key: {self.api_key_link}")

    return True
```

#### 4. Updated Payment Success Callback
**File:** `oropendola_ai/api/subscription_renewal.py:354-370`

The payment success callback now calls `activate_after_payment()` instead of just setting status to Active:

```python
else:
    # New subscription or renewal after expiration: Activate
    subscription.db_set("amount_paid", invoice.total_amount)
    subscription.db_set("last_payment_date", nowdate())

    # Ensure dates are set
    if not subscription.start_date:
        subscription.db_set("start_date", today())
    if not subscription.end_date:
        plan = frappe.get_doc("AI Plan", subscription.plan)
        subscription.db_set("end_date", add_days(subscription.start_date, plan.duration_days))

    # Reload subscription to get latest data
    subscription.reload()

    # Activate subscription (sets status, quota, and creates API key)
    subscription.activate_after_payment()
```

### New Subscription Flow

#### Before Payment:
1. User signs up with a paid plan
2. Subscription created with status: **"Pending"**
3. Invoice created with status: **"Pending"**
4. **Quota set to 0** (cannot make API requests)
5. **No API key created** (cannot authenticate)
6. User redirected to payment gateway

#### After Successful Payment:
1. PayU sends success callback
2. Invoice marked as **"Paid"**
3. `activate_after_payment()` called:
   - Status changed to **"Active"**
   - `set_quota()` called → gives full quota
   - `create_api_key()` called → creates active API key
4. User can now use the service

#### For Free Plans:
Free plans (price = 0) work as before:
- Quota given immediately
- API key created immediately
- No payment required

### Testing the Fix

To verify the fix works:

1. **Create new paid subscription:**
```python
# Should create subscription with status="Pending", quota=0, no API key
```

2. **Check subscription before payment:**
```sql
SELECT name, status, daily_quota_remaining, api_key_link
FROM `tabAI Subscription`
WHERE user = 'test@example.com'
ORDER BY creation DESC LIMIT 1;

-- Expected: status='Pending', daily_quota_remaining=0, api_key_link=NULL
```

3. **Complete payment:**
```python
# Simulate PayU success callback
```

4. **Check subscription after payment:**
```sql
SELECT name, status, daily_quota_remaining, api_key_link
FROM `tabAI Subscription`
WHERE user = 'test@example.com'
ORDER BY creation DESC LIMIT 1;

-- Expected: status='Active', daily_quota_remaining=<full_quota>, api_key_link=<API_KEY_ID>
```

### Impact
✅ Users can no longer use the service without payment
✅ Pending subscriptions have 0 quota and no API key
✅ Only successful payment activates the subscription
✅ Free plans continue to work as expected

## Future Enhancements

- [ ] Webhook support for real-time updates
- [ ] Partial payments
- [ ] Installment plans
- [ ] Auto-retry for failed payments
- [ ] Payment analytics dashboard
- [ ] Multi-currency support
- [ ] Subscription upgrades/downgrades mid-cycle

---

**Last Updated:** October 31, 2025 (Critical Bug Fix Applied)
**Version:** 1.1.0
**Maintained by:** Oropendola AI Team
