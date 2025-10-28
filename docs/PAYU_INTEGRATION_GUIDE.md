# PayU Payment Gateway Integration - Complete Guide

## Overview

This guide explains the complete PayU payment gateway integration for Oropendola AI, including the subscription purchase flow, payment processing, and user onboarding.

---

## 🎯 Features Implemented

### 1. **PayU Payment Gateway Service**
- ✅ Order creation with hash generation
- ✅ Payment verification
- ✅ Success/failure callback handling
- ✅ Transaction status checking
- ✅ Secure hash validation

### 2. **Complete User Flow**
- ✅ Professional homepage (cursor.com inspired)
- ✅ Dynamic pricing page
- ✅ Payment checkout
- ✅ Success/failure pages
- ✅ Subscription activation

### 3. **API Endpoints**
- ✅ `/api/method/oropendola_ai.oropendola_ai.api.payment.get_plans`
- ✅ `/api/method/oropendola_ai.oropendola_ai.api.payment.create_subscription_and_invoice`
- ✅ `/api/method/oropendola_ai.oropendola_ai.api.payment.initiate_payment`
- ✅ `/api/method/oropendola_ai.oropendola_ai.api.payment.payu_success`
- ✅ `/api/method/oropendola_ai.oropendola_ai.api.payment.payu_failure`

---

## 📋 Prerequisites

### 1. PayU Account Setup

1. **Create PayU Account**: Visit [https://payu.in](https://payu.in)
2. **Get Credentials**: Navigate to Dashboard → Settings → API Keys
3. **Copy**:
   - Merchant Key
   - Merchant Salt

### 2. Configure Site Config

Edit your site configuration:

```bash
cd /home/frappe/frappe-bench
nano sites/oropendola.ai/site_config.json
```

Add PayU credentials:

```json
{
  "payu_merchant_key": "your_merchant_key_here",
  "payu_merchant_salt": "your_merchant_salt_here",
  "payu_mode": "test"
}
```

**Note**: Use `"payu_mode": "production"` for live transactions.

---

## 🚀 Complete User Journey

### **Flow 1: New User Signup with Subscription**

```
1. User visits homepage (/)
   ↓
2. Clicks "Get Started" or "View Pricing"
   ↓
3. Views pricing page (/pricing)
   ↓
4. Selects a plan
   ↓
5. Redirected to signup (/login#signup?plan=pro)
   ↓
6. User creates account
   ↓
7. Subscription created (status: Pending)
   ↓
8. Invoice generated
   ↓
9. Redirected to payment page (/payment?invoice=INV-XXX)
   ↓
10. User clicks "Proceed to PayU"
    ↓
11. Redirected to PayU payment gateway
    ↓
12. User completes payment
    ↓
13. PayU redirects to success callback
    ↓
14. Subscription activated
    ↓
15. Redirected to /payment-success
    ↓
16. User can access dashboard
```

### **Flow 2: Existing User Login**

```
1. User visits homepage (/)
   ↓
2. Clicks "Sign In"
   ↓
3. Logs in
   ↓
4. If no subscription:
   → Redirected to /pricing
   → Follows subscription flow
   
5. If has subscription:
   → Access to all features
   → VS Code authentication available
```

---

## 🏗️ Architecture

### **File Structure**

```
oropendola_ai/
├── oropendola_ai/
│   ├── api/
│   │   └── payment.py              # Payment API endpoints
│   ├── services/
│   │   └── payu_gateway.py         # PayU integration logic
│   └── www/
│       ├── index.html              # Homepage
│       ├── pricing/
│       │   └── index.html          # Pricing page
│       ├── payment/
│       │   └── index.html          # Payment checkout
│       ├── payment-success/
│       │   └── index.html          # Success page
│       └── payment-failed/
│           └── index.html          # Failure page
```

### **Payment Hash Generation**

PayU requires SHA512 hash for security:

```python
hash_string = (
    f"{merchant_key}|{txnid}|{amount}|"
    f"{productinfo}|{firstname}|{email}|"
    f"{udf1}|{udf2}|{udf3}|{udf4}|{udf5}||||||{merchant_salt}"
)
hash = hashlib.sha512(hash_string.encode('utf-8')).hexdigest()
```

### **Payment Verification Hash**

```python
hash_string = (
    f"{merchant_salt}|{status}||||||"
    f"{udf5}|{udf4}|{udf3}|{udf2}|{udf1}|{email}|"
    f"{firstname}|{productinfo}|{amount}|{txnid}|{merchant_key}"
)
```

---

## 🔧 API Reference

### 1. **Get Plans**

**Endpoint**: `POST /api/method/oropendola_ai.oropendola_ai.api.payment.get_plans`

**Auth**: Not required

**Response**:
```json
{
  "message": {
    "success": true,
    "plans": [
      {
        "plan_id": "free",
        "title": "Free",
        "price": 0,
        "duration_days": 30,
        "requests_limit_per_day": 100,
        "features": [...],
        "models": [...]
      }
    ]
  }
}
```

### 2. **Create Subscription**

**Endpoint**: `POST /api/method/oropendola_ai.oropendola_ai.api.payment.create_subscription_and_invoice`

**Auth**: Required

**Request**:
```json
{
  "plan_id": "pro"
}
```

**Response (Paid Plan)**:
```json
{
  "message": {
    "success": true,
    "is_free": false,
    "subscription_id": "SUB-2025-00001",
    "invoice_id": "INV-2025-00001",
    "amount": 999,
    "currency": "INR"
  }
}
```

**Response (Free Plan)**:
```json
{
  "message": {
    "success": true,
    "is_free": true,
    "subscription_id": "SUB-2025-00001",
    "status": "Active"
  }
}
```

### 3. **Initiate Payment**

**Endpoint**: `POST /api/method/oropendola_ai.oropendola_ai.api.payment.initiate_payment`

**Auth**: Required

**Request**:
```json
{
  "invoice_id": "INV-2025-00001",
  "gateway": "payu"
}
```

**Response**:
```json
{
  "message": {
    "success": true,
    "payment_url": "https://test.payu.in/_payment",
    "payment_data": {
      "key": "merchant_key",
      "txnid": "ORO202500001",
      "amount": "999",
      "hash": "generated_hash",
      ...
    }
  }
}
```

---

## 🔐 Security Features

### 1. **Hash Validation**
- All payment requests validated with SHA512 hash
- Response hash verified before processing

### 2. **CSRF Protection**
- All authenticated endpoints require CSRF token
- Token obtained from cookies

### 3. **User Authorization**
- Invoice ownership verified
- Subscription access controlled

### 4. **Transaction Security**
- Unique transaction IDs
- Invoice status tracking
- Payment reconciliation

---

## 🧪 Testing Guide

### **Test Mode Configuration**

```json
{
  "payu_mode": "test",
  "payu_merchant_key": "your_test_key",
  "payu_merchant_salt": "your_test_salt"
}
```

### **Test Cards (PayU Test Mode)**

**Successful Transaction**:
- Card Number: `5123456789012346`
- CVV: `123`
- Expiry: Any future date
- OTP: `123456`

**Failed Transaction**:
- Card Number: `4000000000000002`

### **Manual Testing Steps**

1. **Homepage Test**:
   ```bash
   curl https://oropendola.ai/
   ```

2. **Pricing API Test**:
   ```bash
   curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.payment.get_plans
   ```

3. **End-to-End Flow**:
   - Open https://oropendola.ai
   - Click "Get Started"
   - Sign up with test email
   - Select a paid plan
   - Complete test payment
   - Verify subscription activation

---

## 📊 Database Schema

### **AI Subscription**

```
- user: Link to User
- plan: Link to AI Plan
- status: Active/Pending/Cancelled/Expired
- start_date: Date
- end_date: Date
- amount_paid: Currency
- last_payment_date: Date
```

### **AI Invoice**

```
- user: Link to User
- subscription: Link to AI Subscription
- plan: Link to AI Plan
- status: Pending/Paid/Failed
- total_amount: Currency
- payment_gateway: PayU/Razorpay
- payment_gateway_order_id: Transaction ID
- payment_gateway_payment_id: Payment ID
```

---

## 🎨 UI Pages

### 1. **Homepage** (`/`)
- Hero section with CTA
- Feature highlights
- Demo code window
- Professional design inspired by cursor.com

### 2. **Pricing** (`/pricing`)
- Dynamic plan loading from database
- Real-time subscription checking
- Plan comparison
- Subscribe buttons with auth flow

### 3. **Payment** (`/payment?invoice=XXX`)
- Invoice details display
- PayU form auto-submission
- Secure payment processing

### 4. **Success** (`/payment-success`)
- Confirmation message
- Subscription details
- Dashboard link

### 5. **Failure** (`/payment-failed`)
- Error message
- Retry option
- Support information

---

## 🚨 Troubleshooting

### **Issue 1: Payment Hash Mismatch**

**Symptom**: "Invalid payment hash" error

**Solution**:
1. Verify merchant salt is correct
2. Check parameter order in hash string
3. Ensure no extra spaces in credentials

### **Issue 2: Callback Not Working**

**Symptom**: Payment completes but subscription not activated

**Solution**:
1. Check callback URLs in site config
2. Verify server is accessible from internet
3. Check error logs: `bench --site oropendola.ai console`

### **Issue 3: Plans Not Loading**

**Symptom**: Pricing page shows loading spinner forever

**Solution**:
1. Check if AI Plan documents exist
2. Verify API endpoint is accessible
3. Check browser console for errors

---

## 🔄 Deployment Checklist

- [ ] PayU credentials configured in `site_config.json`
- [ ] Homepage set in `hooks.py`
- [ ] Database migrations run: `bench --site oropendola.ai migrate`
- [ ] Cache cleared: `bench --site oropendola.ai clear-cache`
- [ ] Build completed: `bench build --app oropendola_ai`
- [ ] Server restarted: `bench restart`
- [ ] Test plans created in AI Plan doctype
- [ ] Test subscription flow end-to-end
- [ ] PayU webhooks configured (production)
- [ ] SSL certificate installed (production)

---

## 📞 Support

For issues or questions:
1. Check error logs: `bench --site oropendola.ai console`
2. Review PayU documentation: https://docs.payu.in
3. Contact PayU support for payment-specific issues

---

## 🎉 Next Steps

1. **Create Default Plans**: Add plans via ERPNext UI or API
2. **Test Complete Flow**: Sign up → Subscribe → Pay → Activate
3. **Configure Production**: Switch to production mode with live credentials
4. **Monitor Transactions**: Track payments in AI Invoice doctype
5. **Enable VS Code Auth**: Test authentication flow
6. **Setup Analytics**: Monitor conversion rates

---

**Implementation Complete**: You now have a fully functional payment gateway integration with PayU! 🚀
# PayU Payment Gateway Integration - Complete Guide

## Overview

This guide explains the complete PayU payment gateway integration for Oropendola AI, including the subscription purchase flow, payment processing, and user onboarding.

---

## 🎯 Features Implemented

### 1. **PayU Payment Gateway Service**
- ✅ Order creation with hash generation
- ✅ Payment verification
- ✅ Success/failure callback handling
- ✅ Transaction status checking
- ✅ Secure hash validation

### 2. **Complete User Flow**
- ✅ Professional homepage (cursor.com inspired)
- ✅ Dynamic pricing page
- ✅ Payment checkout
- ✅ Success/failure pages
- ✅ Subscription activation

### 3. **API Endpoints**
- ✅ `/api/method/oropendola_ai.oropendola_ai.api.payment.get_plans`
- ✅ `/api/method/oropendola_ai.oropendola_ai.api.payment.create_subscription_and_invoice`
- ✅ `/api/method/oropendola_ai.oropendola_ai.api.payment.initiate_payment`
- ✅ `/api/method/oropendola_ai.oropendola_ai.api.payment.payu_success`
- ✅ `/api/method/oropendola_ai.oropendola_ai.api.payment.payu_failure`

---

## 📋 Prerequisites

### 1. PayU Account Setup

1. **Create PayU Account**: Visit [https://payu.in](https://payu.in)
2. **Get Credentials**: Navigate to Dashboard → Settings → API Keys
3. **Copy**:
   - Merchant Key
   - Merchant Salt

### 2. Configure Site Config

Edit your site configuration:

```bash
cd /home/frappe/frappe-bench
nano sites/oropendola.ai/site_config.json
```

Add PayU credentials:

```json
{
  "payu_merchant_key": "your_merchant_key_here",
  "payu_merchant_salt": "your_merchant_salt_here",
  "payu_mode": "test"
}
```

**Note**: Use `"payu_mode": "production"` for live transactions.

---

## 🚀 Complete User Journey

### **Flow 1: New User Signup with Subscription**

```
1. User visits homepage (/)
   ↓
2. Clicks "Get Started" or "View Pricing"
   ↓
3. Views pricing page (/pricing)
   ↓
4. Selects a plan
   ↓
5. Redirected to signup (/login#signup?plan=pro)
   ↓
6. User creates account
   ↓
7. Subscription created (status: Pending)
   ↓
8. Invoice generated
   ↓
9. Redirected to payment page (/payment?invoice=INV-XXX)
   ↓
10. User clicks "Proceed to PayU"
    ↓
11. Redirected to PayU payment gateway
    ↓
12. User completes payment
    ↓
13. PayU redirects to success callback
    ↓
14. Subscription activated
    ↓
15. Redirected to /payment-success
    ↓
16. User can access dashboard
```

### **Flow 2: Existing User Login**

```
1. User visits homepage (/)
   ↓
2. Clicks "Sign In"
   ↓
3. Logs in
   ↓
4. If no subscription:
   → Redirected to /pricing
   → Follows subscription flow
   
5. If has subscription:
   → Access to all features
   → VS Code authentication available
```

---

## 🏗️ Architecture

### **File Structure**

```
oropendola_ai/
├── oropendola_ai/
│   ├── api/
│   │   └── payment.py              # Payment API endpoints
│   ├── services/
│   │   └── payu_gateway.py         # PayU integration logic
│   └── www/
│       ├── index.html              # Homepage
│       ├── pricing/
│       │   └── index.html          # Pricing page
│       ├── payment/
│       │   └── index.html          # Payment checkout
│       ├── payment-success/
│       │   └── index.html          # Success page
│       └── payment-failed/
│           └── index.html          # Failure page
```

### **Payment Hash Generation**

PayU requires SHA512 hash for security:

```python
hash_string = (
    f"{merchant_key}|{txnid}|{amount}|"
    f"{productinfo}|{firstname}|{email}|"
    f"{udf1}|{udf2}|{udf3}|{udf4}|{udf5}||||||{merchant_salt}"
)
hash = hashlib.sha512(hash_string.encode('utf-8')).hexdigest()
```

### **Payment Verification Hash**

```python
hash_string = (
    f"{merchant_salt}|{status}||||||"
    f"{udf5}|{udf4}|{udf3}|{udf2}|{udf1}|{email}|"
    f"{firstname}|{productinfo}|{amount}|{txnid}|{merchant_key}"
)
```

---

## 🔧 API Reference

### 1. **Get Plans**

**Endpoint**: `POST /api/method/oropendola_ai.oropendola_ai.api.payment.get_plans`

**Auth**: Not required

**Response**:
```json
{
  "message": {
    "success": true,
    "plans": [
      {
        "plan_id": "free",
        "title": "Free",
        "price": 0,
        "duration_days": 30,
        "requests_limit_per_day": 100,
        "features": [...],
        "models": [...]
      }
    ]
  }
}
```

### 2. **Create Subscription**

**Endpoint**: `POST /api/method/oropendola_ai.oropendola_ai.api.payment.create_subscription_and_invoice`

**Auth**: Required

**Request**:
```json
{
  "plan_id": "pro"
}
```

**Response (Paid Plan)**:
```json
{
  "message": {
    "success": true,
    "is_free": false,
    "subscription_id": "SUB-2025-00001",
    "invoice_id": "INV-2025-00001",
    "amount": 999,
    "currency": "INR"
  }
}
```

**Response (Free Plan)**:
```json
{
  "message": {
    "success": true,
    "is_free": true,
    "subscription_id": "SUB-2025-00001",
    "status": "Active"
  }
}
```

### 3. **Initiate Payment**

**Endpoint**: `POST /api/method/oropendola_ai.oropendola_ai.api.payment.initiate_payment`

**Auth**: Required

**Request**:
```json
{
  "invoice_id": "INV-2025-00001",
  "gateway": "payu"
}
```

**Response**:
```json
{
  "message": {
    "success": true,
    "payment_url": "https://test.payu.in/_payment",
    "payment_data": {
      "key": "merchant_key",
      "txnid": "ORO202500001",
      "amount": "999",
      "hash": "generated_hash",
      ...
    }
  }
}
```

---

## 🔐 Security Features

### 1. **Hash Validation**
- All payment requests validated with SHA512 hash
- Response hash verified before processing

### 2. **CSRF Protection**
- All authenticated endpoints require CSRF token
- Token obtained from cookies

### 3. **User Authorization**
- Invoice ownership verified
- Subscription access controlled

### 4. **Transaction Security**
- Unique transaction IDs
- Invoice status tracking
- Payment reconciliation

---

## 🧪 Testing Guide

### **Test Mode Configuration**

```json
{
  "payu_mode": "test",
  "payu_merchant_key": "your_test_key",
  "payu_merchant_salt": "your_test_salt"
}
```

### **Test Cards (PayU Test Mode)**

**Successful Transaction**:
- Card Number: `5123456789012346`
- CVV: `123`
- Expiry: Any future date
- OTP: `123456`

**Failed Transaction**:
- Card Number: `4000000000000002`

### **Manual Testing Steps**

1. **Homepage Test**:
   ```bash
   curl https://oropendola.ai/
   ```

2. **Pricing API Test**:
   ```bash
   curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.payment.get_plans
   ```

3. **End-to-End Flow**:
   - Open https://oropendola.ai
   - Click "Get Started"
   - Sign up with test email
   - Select a paid plan
   - Complete test payment
   - Verify subscription activation

---

## 📊 Database Schema

### **AI Subscription**

```
- user: Link to User
- plan: Link to AI Plan
- status: Active/Pending/Cancelled/Expired
- start_date: Date
- end_date: Date
- amount_paid: Currency
- last_payment_date: Date
```

### **AI Invoice**

```
- user: Link to User
- subscription: Link to AI Subscription
- plan: Link to AI Plan
- status: Pending/Paid/Failed
- total_amount: Currency
- payment_gateway: PayU/Razorpay
- payment_gateway_order_id: Transaction ID
- payment_gateway_payment_id: Payment ID
```

---

## 🎨 UI Pages

### 1. **Homepage** (`/`)
- Hero section with CTA
- Feature highlights
- Demo code window
- Professional design inspired by cursor.com

### 2. **Pricing** (`/pricing`)
- Dynamic plan loading from database
- Real-time subscription checking
- Plan comparison
- Subscribe buttons with auth flow

### 3. **Payment** (`/payment?invoice=XXX`)
- Invoice details display
- PayU form auto-submission
- Secure payment processing

### 4. **Success** (`/payment-success`)
- Confirmation message
- Subscription details
- Dashboard link

### 5. **Failure** (`/payment-failed`)
- Error message
- Retry option
- Support information

---

## 🚨 Troubleshooting

### **Issue 1: Payment Hash Mismatch**

**Symptom**: "Invalid payment hash" error

**Solution**:
1. Verify merchant salt is correct
2. Check parameter order in hash string
3. Ensure no extra spaces in credentials

### **Issue 2: Callback Not Working**

**Symptom**: Payment completes but subscription not activated

**Solution**:
1. Check callback URLs in site config
2. Verify server is accessible from internet
3. Check error logs: `bench --site oropendola.ai console`

### **Issue 3: Plans Not Loading**

**Symptom**: Pricing page shows loading spinner forever

**Solution**:
1. Check if AI Plan documents exist
2. Verify API endpoint is accessible
3. Check browser console for errors

---

## 🔄 Deployment Checklist

- [ ] PayU credentials configured in `site_config.json`
- [ ] Homepage set in `hooks.py`
- [ ] Database migrations run: `bench --site oropendola.ai migrate`
- [ ] Cache cleared: `bench --site oropendola.ai clear-cache`
- [ ] Build completed: `bench build --app oropendola_ai`
- [ ] Server restarted: `bench restart`
- [ ] Test plans created in AI Plan doctype
- [ ] Test subscription flow end-to-end
- [ ] PayU webhooks configured (production)
- [ ] SSL certificate installed (production)

---

## 📞 Support

For issues or questions:
1. Check error logs: `bench --site oropendola.ai console`
2. Review PayU documentation: https://docs.payu.in
3. Contact PayU support for payment-specific issues

---

## 🎉 Next Steps

1. **Create Default Plans**: Add plans via ERPNext UI or API
2. **Test Complete Flow**: Sign up → Subscribe → Pay → Activate
3. **Configure Production**: Switch to production mode with live credentials
4. **Monitor Transactions**: Track payments in AI Invoice doctype
5. **Enable VS Code Auth**: Test authentication flow
6. **Setup Analytics**: Monitor conversion rates

---

**Implementation Complete**: You now have a fully functional payment gateway integration with PayU! 🚀
