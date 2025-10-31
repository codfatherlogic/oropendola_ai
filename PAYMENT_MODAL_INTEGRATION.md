# Payment Modal Integration Guide

This guide explains how to integrate the embedded payment modal with your Pricing page or any other page where users can subscribe.

## Overview

The payment modal provides:
- **Gateway Selection**: Users can choose between payment gateways (PayU, Razorpay - Coming Soon, Stripe - Coming Soon)
- **Embedded Payment**: PayU Bolt embedded iframe for seamless in-page payment
- **Session Tracking**: Automatic tracking of payment attempts and retries
- **Responsive Design**: Mobile-friendly modal that works on all devices

## Files Included

The payment system consists of:
- `/public/js/payment_modal.js` - Payment modal JavaScript (auto-loaded)
- `/public/css/payment_modal.css` - Payment modal styles (auto-loaded)
- `/api/payment_embed.py` - Backend API for payment sessions
- `/doctype/payment_session/` - Payment Session DocType for tracking

## Quick Start

### 1. Basic Integration on Pricing Page

Add this code to your Pricing page where users click "Subscribe":

```html
<script>
// Handle Subscribe button clicks
document.querySelectorAll('.btn-subscribe').forEach(button => {
    button.addEventListener('click', function(e) {
        e.preventDefault();

        const plan_id = this.dataset.planId;
        const plan_name = this.dataset.planName;
        const amount = this.dataset.amount;
        const currency = this.dataset.currency || 'INR';

        // Call subscription API to create invoice
        frappe.call({
            method: 'oropendola_ai.oropendola_ai.api.payment.create_subscription_and_invoice',
            args: { plan_id: plan_id },
            callback: function(r) {
                if (r.message && r.message.success) {
                    const invoice_id = r.message.invoice_id;

                    // Show payment modal
                    window.paymentModal.show({
                        invoice_id: invoice_id,
                        plan_name: plan_name,
                        amount: amount,
                        currency: currency,
                        onSuccess: function(result) {
                            console.log('Payment successful!', result);
                            frappe.msgprint('Payment successful! Redirecting...');

                            // Redirect to dashboard or subscription page
                            setTimeout(() => {
                                window.location.href = '/dashboard';
                            }, 1500);
                        },
                        onCancel: function(result) {
                            console.log('Payment cancelled', result);
                            frappe.msgprint('Payment was cancelled. You can retry anytime.');
                        }
                    });
                } else {
                    frappe.msgprint(r.message.error || 'Failed to initiate payment');
                }
            }
        });
    });
});
</script>
```

### 2. HTML Structure for Pricing Cards

Example pricing card structure:

```html
<div class="pricing-card">
    <h3>Starter Plan</h3>
    <div class="price">₹199/month</div>
    <ul class="features">
        <li>1000 requests/day</li>
        <li>Basic support</li>
        <li>Email notifications</li>
    </ul>
    <button class="btn btn-primary btn-subscribe"
            data-plan-id="PLAN-00001"
            data-plan-name="Starter Plan"
            data-amount="199"
            data-currency="INR">
        Subscribe Now
    </button>
</div>
```

### 3. Sign-In Flow Integration

For users who sign in from the Pricing page:

```javascript
// After successful login
function handleSuccessfulLogin(user) {
    // Check if user came from pricing page
    const selectedPlan = sessionStorage.getItem('selected_plan');

    if (selectedPlan) {
        const planData = JSON.parse(selectedPlan);

        // Clear storage
        sessionStorage.removeItem('selected_plan');

        // Trigger payment flow
        triggerPaymentFlow(planData);
    }
}

// Store selected plan before showing login
function selectPlanAndLogin(planData) {
    // Store plan selection
    sessionStorage.setItem('selected_plan', JSON.stringify(planData));

    // Show login modal or redirect to login
    window.location.href = '/login?redirect=/pricing';
}
```

## API Reference

### Payment Modal API

#### `window.paymentModal.show(options)`

Opens the payment modal.

**Parameters:**

```javascript
{
    invoice_id: String,      // Required: AI Invoice ID
    plan_name: String,       // Required: Display name of plan
    amount: Number,          // Required: Payment amount
    currency: String,        // Required: Currency code (INR, USD, etc.)
    onSuccess: Function,     // Optional: Success callback
    onCancel: Function       // Optional: Cancel callback
}
```

**Example:**

```javascript
window.paymentModal.show({
    invoice_id: 'INV-2025-00123',
    plan_name: 'Professional Plan',
    amount: 849,
    currency: 'INR',
    onSuccess: (result) => {
        // Handle success
        console.log('Subscription ID:', result.subscription_id);
        console.log('Transaction ID:', result.transaction_id);
        window.location.href = '/dashboard';
    },
    onCancel: (result) => {
        // Handle cancel
        console.log('User cancelled payment');
    }
});
```

### Backend API Endpoints

#### 1. Initialize Payment Session

```python
frappe.call({
    method: 'oropendola_ai.oropendola_ai.api.payment_embed.initialize_payment_session',
    args: {
        invoice_id: 'INV-2025-00123',
        gateway: 'PayU',          // Optional, defaults to PayU
        embed_mode: true          // Optional, defaults to true
    },
    callback: (r) => {
        if (r.message.success) {
            // Session created
            console.log(r.message.session_id);
        }
    }
});
```

#### 2. Get Payment Session

```python
frappe.call({
    method: 'oropendola_ai.oropendola_ai.api.payment_embed.get_payment_session',
    args: {
        session_id: 'PS-2025-00001'
        // OR
        invoice_id: 'INV-2025-00123'
    },
    callback: (r) => {
        if (r.message.success) {
            console.log(r.message.session);
        }
    }
});
```

#### 3. Retry Failed Payment

```python
frappe.call({
    method: 'oropendola_ai.oropendola_ai.api.payment_embed.retry_payment_session',
    args: {
        invoice_id: 'INV-2025-00123',
        gateway: 'PayU'  // Optional
    },
    callback: (r) => {
        if (r.message.success) {
            // New session created for retry
            window.paymentModal.show({...});
        }
    }
});
```

#### 4. Cancel Payment Session

```python
frappe.call({
    method: 'oropendola_ai.oropendola_ai.api.payment_embed.cancel_payment_session',
    args: {
        session_id: 'PS-2025-00001',
        reason: 'User clicked cancel'
    }
});
```

## Payment Retry Flow

### Show Retry Option in UI

```html
<div class="pending-payment-alert" v-if="hasPendingPayment">
    <div class="alert alert-warning">
        <strong>Incomplete Payment</strong>
        <p>You have a pending payment. Click below to complete it.</p>
        <button class="btn btn-primary" @click="retryPayment">
            Complete Payment
        </button>
    </div>
</div>
```

```javascript
// Check for pending payments
frappe.call({
    method: 'oropendola_ai.oropendola_ai.api.payment.get_pending_invoices',
    callback: (r) => {
        if (r.message && r.message.invoices && r.message.invoices.length > 0) {
            const invoice = r.message.invoices[0];

            // Show retry UI
            showRetryUI(invoice);
        }
    }
});

function showRetryUI(invoice) {
    // Show alert or banner
    const retryBtn = document.createElement('button');
    retryBtn.textContent = 'Complete Payment';
    retryBtn.onclick = () => {
        frappe.call({
            method: 'oropendola_ai.oropendola_ai.api.payment_embed.retry_payment_session',
            args: { invoice_id: invoice.name },
            callback: (r) => {
                if (r.message.success) {
                    window.paymentModal.show({
                        invoice_id: invoice.name,
                        plan_name: invoice.plan,
                        amount: invoice.total_amount,
                        currency: invoice.currency,
                        onSuccess: () => window.location.reload()
                    });
                } else {
                    frappe.msgprint(r.message.error);
                }
            }
        });
    };
}
```

## Edge Cases Handled

### 1. User Closes Modal Mid-Payment

The payment session is automatically tracked. If the user closes the modal:
- Session status remains "Pending" or "Processing"
- After 30 minutes, abandoned payment checker marks it as "Abandoned"
- User can retry from the Pricing page or Account settings

### 2. Payment Gateway Failure

If PayU Bolt fails to load:
- Error message is displayed
- "Try Again" button shown
- User can select different gateway (when available)

### 3. Multiple Retries

- Maximum 3 retry attempts per invoice
- Attempt counter increments with each try
- After 3 failed attempts, user must contact support

### 4. Duplicate Subscriptions

The system prevents duplicate active subscriptions:
- Checks for existing active subscription
- Shows error if user tries to subscribe while active subscription exists

### 5. Network Loss During Payment

- Session marked as "Abandoned" after 30 minutes
- Server-side verification used for final confirmation
- Webhook handler processes actual payment status from gateway

## Testing

### Test Payment Flow

```javascript
// Test with a free plan (no actual payment)
window.paymentModal.show({
    invoice_id: 'test-invoice-id',
    plan_name: 'Test Plan',
    amount: 0,
    currency: 'INR',
    onSuccess: (result) => {
        console.log('Free plan activated:', result);
    }
});
```

### Test PayU Sandbox

PayU test credentials are already configured in development mode. Use PayU's test cards:

- **Success Card**: 5123456789012346
- **Failure Card**: 4012001037141112
- CVV: Any 3 digits
- Expiry: Any future date

## Troubleshooting

### Modal Not Showing

Check if assets are loaded:

```javascript
// In browser console
console.log(typeof window.paymentModal); // Should be 'object'
console.log(typeof PaymentModal);         // Should be 'function'
```

If undefined, rebuild assets:

```bash
cd /home/frappe/frappe-bench
bench build
bench --site oropendola.ai clear-cache
bench restart
```

### Payment Not Completing

1. Check browser console for errors
2. Verify invoice status: should be "Pending" before payment
3. Check PayU credentials in Oropendola Settings
4. Ensure webhook URLs are accessible

### Session Not Found

If "No active payment session found" error:

```javascript
// Check session status
frappe.call({
    method: 'oropendola_ai.oropendola_ai.api.payment_embed.get_user_payment_sessions',
    args: { limit: 10 },
    callback: (r) => {
        console.log('Recent sessions:', r.message.sessions);
    }
});
```

## Best Practices

1. **Always Clear Session Storage**: After successful payment, clear any stored plan data
2. **Show Loading States**: Use loading indicators during API calls
3. **Handle Errors Gracefully**: Show user-friendly error messages
4. **Log Important Events**: Log payment attempts, successes, and failures
5. **Test Thoroughly**: Test all flows: success, failure, cancel, retry
6. **Mobile Testing**: Test on actual mobile devices, not just responsive mode
7. **Webhook Verification**: Always verify payments server-side via webhook

## Security Notes

1. **Never Store** payment credentials in frontend
2. **Never Expose** gateway keys in JavaScript
3. **Always Use HTTPS** for payment pages
4. **Validate Server-Side**: Trust only server verification, not client responses
5. **CSRF Protection**: All API endpoints are CSRF-protected by Frappe

## Production Checklist

Before going live:

- [ ] Switch `payu_mode` to "production" in Oropendola Settings
- [ ] Update PayU credentials with production keys
- [ ] Test payment flow end-to-end
- [ ] Verify webhook endpoints are accessible
- [ ] Enable abandoned payment checker (already configured)
- [ ] Set up monitoring for failed payments
- [ ] Configure email notifications
- [ ] Test retry flow
- [ ] Verify SSL certificate
- [ ] Review error handling

## Support

For issues or questions:
- Check logs: `bench --site oropendola.ai logs`
- Review Payment Session records in DocType
- Check AI Invoice status
- Contact: sammish.thundiyil@gmail.com

---

**Last Updated**: October 31, 2025
**Version**: 1.0.0
