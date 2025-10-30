# AI Subscription Renewal & Lifecycle Management

## Overview

This document explains the comprehensive subscription renewal and lifecycle management system implemented in Oropendola AI.

## Business Rules

### 1. Auto-Renewal Policy
- **Auto-renewal is ALWAYS disabled** (`auto_renew = 0`)
- Customers must manually renew subscriptions before or after expiration
- No automatic charges or recurring billing
- Provides full transparency and control to customers

### 2. Subscription States

```
┌─────────────┐
│   Pending   │  ← Created, awaiting payment
└──────┬──────┘
       │ payment success
       ▼
┌─────────────┐
│   Active    │  ← Normal operation, API access granted
└──────┬──────┘
       │ end_date passed
       ▼
┌─────────────┐
│   Expired   │  ← No API access, can renew anytime
└──────┬──────┘
       │ manual renewal
       ▼
┌─────────────┐
│New Active   │  ← Fresh subscription created
└─────────────┘
```

## Renewal Scenarios

### Scenario 1: Renewal Before Expiration (Extension)

**Use Case:** Active customer wants to extend their subscription

**Logic:**
```python
# Current State
subscription.status = "Active"
subscription.end_date = "2025-11-27"

# Customer renews on 2025-11-20
renewal_result = renew_subscription(plan_id="same_plan")

# After Payment
subscription.end_date = "2025-12-27"  # Extended by 30 days from current end_date
# Same subscription continues, no new subscription created
```

**Requirements:**
- ✅ Can only extend with SAME plan
- ✅ Renewal allowed within 7 days before expiration
- ✅ New end_date = current_end_date + plan_duration_days
- ✅ Seamless continuity, no service interruption

**API Call:**
```javascript
// Frontend
await fetch('/api/method/oropendola_ai.oropendola_ai.api.subscription_renewal.renew_subscription', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({plan_id: 'current_plan_id'})
});

// Response
{
    "success": true,
    "renewal_type": "extension",
    "current_end_date": "2025-11-27",
    "new_end_date": "2025-12-27",
    "invoice_id": "INV-2025-00123",
    "amount": 849.00
}
```

---

### Scenario 2: Plan Change During Active Subscription

**Use Case:** Customer wants to upgrade/downgrade while subscription is active

**Logic:**
```python
# Current State
subscription.status = "Active"
subscription.plan = "7_days_plan"
subscription.end_date = "2025-11-27"

# Customer tries to switch to "30_days_plan"
renewal_result = renew_subscription(plan_id="30_days_plan")

# Response
{
    "success": false,
    "error": "Cannot change plan while subscription is active...",
    "suggestion": "wait_for_expiration",
    "current_end_date": "2025-11-27"
}
```

**Requirements:**
- ❌ Plan changes NOT allowed during active period
- ✅ Customer must wait until current subscription expires
- ✅ Clear error message with expiration date
- ✅ Prevents partial billing complications

**Best Practice:**
- Customer lets current subscription expire
- Then subscribes to new plan
- Clean cutover, simple billing

---

### Scenario 3: Renewal After Expiration

**Use Case:** Customer forgot to renew, subscription expired

**Logic:**
```python
# Current State
subscription_old.status = "Expired"
subscription_old.end_date = "2025-11-27"  # past date
current_date = "2025-12-05"

# Customer renews
renewal_result = renew_subscription(plan_id="7_days_plan")

# New Subscription Created
subscription_new = {
    "status": "Pending",
    "start_date": "2025-12-05",  # TODAY
    "end_date": "2025-12-12",    # Today + 7 days
    "plan": "7_days_plan"
}

# Old subscription remains as historical record
subscription_old.status = "Expired"  # unchanged
```

**Requirements:**
- ✅ Creates NEW subscription (not extension)
- ✅ Starts from TODAY (not from old end_date)
- ✅ Old subscription preserved for history
- ✅ Can choose same or different plan

**API Response:**
```javascript
{
    "success": true,
    "renewal_type": "new_after_expiration",
    "subscription_id": "SUB-2025-00200",
    "old_subscription_id": "SUB-2025-00150",
    "invoice_id": "INV-2025-00250",
    "message": "New subscription created. Previous subscription has expired."
}
```

---

### Scenario 4: Duplicate Subscription Prevention

**Use Case:** User tries to buy another subscription while one is active

**Logic:**
```python
# Current State
existing_subscription.status = "Active"
existing_subscription.end_date = "2025-12-15"

# User clicks "Subscribe Now" on pricing page
result = create_subscription_and_invoice(plan_id="any_plan")

# Response
{
    "success": false,
    "error": "You already have an active subscription",
    "existing_subscription": {
        "name": "SUB-2025-00150",
        "plan": "7_days_plan",
        "status": "Active"
    }
}
```

**Requirements:**
- ✅ Only ONE active subscription per user
- ✅ Clear error message
- ✅ Shows details of existing subscription
- ✅ User must wait for expiration or use renewal flow

---

## API Endpoints

### 1. Renew Subscription
```python
@frappe.whitelist()
def renew_subscription(plan_id: str = None)
```

**Purpose:** Universal renewal endpoint
- Handles all renewal scenarios automatically
- Detects current subscription state
- Applies appropriate logic (extension/new subscription)

**Parameters:**
- `plan_id` (optional): Plan to renew with (defaults to current plan)

**Returns:**
```json
{
    "success": true,
    "renewal_type": "extension|new_after_expiration|new",
    "subscription_id": "SUB-2025-XXXXX",
    "invoice_id": "INV-2025-XXXXX",
    "amount": 849.00,
    "currency": "INR",
    "is_free": false,
    "message": "Human-readable status"
}
```

---

### 2. Get Subscription Status
```python
@frappe.whitelist()
def get_subscription_status()
```

**Purpose:** Get detailed subscription info and renewal eligibility

**Returns:**
```json
{
    "success": true,
    "has_subscription": true,
    "subscription": {
        "id": "SUB-2025-00150",
        "plan_name": "7 Days Plan",
        "status": "Active",
        "start_date": "2025-10-28",
        "end_date": "2025-11-27",
        "days_remaining": 10,
        "auto_renew": 0
    },
    "can_renew": true,
    "renewal_type": "extension",
    "renewal_message": "Your subscription expires in 10 days. Renew now to extend your access."
}
```

---

### 3. Apply Payment to Subscription
```python
@frappe.whitelist()
def apply_payment_to_subscription(invoice_id: str)
```

**Purpose:** Called by payment gateway callback
- Updates subscription based on invoice billing_type
- Handles extensions vs new subscriptions
- Sets correct dates and status

**Internal Use Only** (called by PayU/Razorpay callbacks)

---

## Frontend Integration

### Check Subscription Status
```javascript
async function checkSubscriptionStatus() {
    const response = await fetch('/api/method/oropendola_ai.oropendola_ai.api.subscription_renewal.get_subscription_status', {
        method: 'POST',
        credentials: 'include'
    });
    const data = await response.json();
    
    if (data.message.can_renew) {
        // Show "Renew Now" button
        showRenewButton(data.message.renewal_message);
    }
}
```

### Initiate Renewal
```javascript
async function renewSubscription(planId = null) {
    const response = await fetch('/api/method/oropendola_ai.oropendola_ai.api.subscription_renewal.renew_subscription', {
        method: 'POST',
        credentials: 'include',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({plan_id: planId})
    });
    const data = await response.json();
    
    if (data.message.success) {
        if (data.message.is_free) {
            // Free plan activated
            window.location.href = '/my-profile';
        } else {
            // Redirect to payment
            await initiatePayment(data.message.invoice_id);
        }
    }
}
```

---

## Database Structure

### AI Subscription Fields
```python
# Core fields
user: Link to User
plan: Link to AI Plan
status: Select (Active, Trial, Expired, Cancelled, Pending, Suspended)
start_date: Date
end_date: Date
auto_renew: Check (always 0)

# Billing
billing_email: Data
amount_paid: Currency
last_payment_date: Date
next_billing_date: Date  # Used for extension logic

# Quota
daily_quota_limit: Int
daily_quota_remaining: Int
monthly_budget_limit: Currency
monthly_budget_used: Currency
```

### AI Invoice Fields
```python
user: Link to User
subscription: Link to AI Subscription
plan: Link to AI Plan
status: Select (Pending, Paid, Failed, Cancelled)
billing_type: Select (Subscription, Renewal, Upgrade, Downgrade)
total_amount: Currency
period_start: Date
period_end: Date
```

---

## Payment Flow Integration

### PayU Gateway Callback
```python
# services/payu_gateway.py - process_payment_success()
def process_payment_success(response_data):
    # Update invoice
    invoice.status = "Paid"
    
    # Apply payment using centralized renewal logic
    from subscription_renewal import apply_payment_to_subscription
    apply_payment_to_subscription(invoice.name)
    
    # Handles:
    # - New subscriptions: Activate
    # - Renewals/Extensions: Extend end_date
    # - Billing type detection: Automatic
```

---

## Scheduled Tasks

### Expiration Check (Hourly)
```python
# tasks.py - check_expired_subscriptions()
def check_expired_subscriptions():
    # Find subscriptions where end_date < today
    # Change status from "Active" to "Expired"
    # Revoke API keys
    # No automatic renewal (manual only)
```

### Daily Quota Reset (Daily)
```python
# tasks.py - reset_daily_quotas()
def reset_daily_quotas():
    # Reset daily_quota_remaining to daily_quota_limit
    # For all Active subscriptions
```

---

## Best Practices

### For Customers

1. **Renewal Timing:**
   - ✅ Renew within 7 days before expiration (seamless extension)
   - ✅ Can renew anytime after expiration (new subscription)
   - ❌ Cannot change plans during active period

2. **Plan Changes:**
   - Wait for current subscription to expire
   - Then subscribe to new plan
   - Clean cutover, no prorating needed

3. **Expired Subscriptions:**
   - API access immediately revoked
   - Can renew anytime (no data loss)
   - New subscription starts from renewal date

### For Developers

1. **Use Renewal API:**
   - Always use `renew_subscription()` for renewals
   - Don't call `create_subscription_and_invoice()` for renewals
   - Let the system detect and handle scenarios

2. **Check Status First:**
   - Call `get_subscription_status()` before showing renewal options
   - Use `can_renew` flag to enable/disable buttons
   - Display `renewal_message` to guide users

3. **Payment Integration:**
   - Renewal invoices have `billing_type = "Renewal"`
   - Payment callback automatically applies correct logic
   - No manual date calculations needed

---

## Testing Scenarios

### Test 1: Active Subscription Extension
```bash
# Setup
User has active subscription expiring in 5 days

# Action
Call renew_subscription(same_plan_id)

# Expected
✓ Invoice created with billing_type="Renewal"
✓ After payment: end_date extended by plan_duration
✓ No new subscription created
```

### Test 2: Expired Subscription Renewal
```bash
# Setup
User has expired subscription (end_date in past)

# Action
Call renew_subscription(plan_id)

# Expected
✓ New subscription created
✓ start_date = today
✓ end_date = today + duration
✓ Old subscription remains "Expired"
```

### Test 3: Duplicate Prevention
```bash
# Setup
User has active subscription

# Action
Call create_subscription_and_invoice()

# Expected
✓ Error: "You already have an active subscription"
✓ No new subscription created
✓ Existing subscription details returned
```

---

## Migration Notes

### Existing Subscriptions
All existing subscriptions should have `auto_renew = 0`. Run this migration:

```sql
UPDATE `tabAI Subscription` 
SET auto_renew = 0 
WHERE auto_renew = 1;
```

### Billing Type Field
Ensure all existing invoices have `billing_type` set:

```sql
UPDATE `tabAI Invoice` 
SET billing_type = 'Subscription' 
WHERE billing_type IS NULL OR billing_type = '';
```

---

## Summary

✅ **Auto-renewal always disabled** - Manual renewals only
✅ **Extension before expiration** - Seamless with same plan
✅ **New subscription after expiration** - Clean start
✅ **Plan changes after expiration** - Simple and clear
✅ **Duplicate prevention** - One active subscription per user
✅ **Automatic expiration** - Hourly checks
✅ **Centralized renewal logic** - Single source of truth

The system provides complete flexibility while maintaining billing simplicity and data integrity.
