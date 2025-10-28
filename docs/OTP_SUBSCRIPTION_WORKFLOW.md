# OTP-Based Subscription Workflow - Implementation Guide

## 🎉 COMPLETE IMPLEMENTATION SUMMARY

### ✅ **What Has Been Built**

This document describes the complete OTP-based subscription workflow for Oropendola AI, including:

1. **Backend OTP Authentication System**
2. **Frontend Login/Signup Modal with OTP**
3. **Payment Integration**
4. **VS Code Extension Support** (ready for integration)

---

## 📁 **Files Created/Modified**

### **Backend API:**
- `/oropendola_ai/oropendola_ai/api/otp_auth.py` - OTP authentication endpoints

### **Frontend:**
- `/oropendola_ai/www/pricing/index.html` - Updated with modal integration
- `/oropendola_ai/templates/pricing/auth-modal.html` - OTP authentication modal

### **Installation:**
- `/oropendola_ai/install.py` - AI Plans creation with cost weights

---

## 🔄 **Complete User Flow**

### **Step-by-Step Journey:**

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER SUBSCRIPTION FLOW                      │
└─────────────────────────────────────────────────────────────────┘

1. USER VISITS PRICING PAGE
   ↓
   https://oropendola.ai/pricing
   └─ Sees 3 plans: ₹199, ₹849, ₹2999

2. USER CLICKS "SUBSCRIBE NOW"
   ↓
   Opens Authentication Modal (Popup)
   
3. STEP 1: EMAIL INPUT
   ├─ User enters email: user@example.com
   ├─ Clicks "Continue"
   └─ System sends 6-digit OTP to email
   
4. STEP 2: OTP VERIFICATION
   ├─ User receives email with code (e.g., 123456)
   ├─ Enters 6-digit code in modal
   ├─ Auto-advances between digits
   ├─ 10-minute timer shown
   ├─ Can resend after 30 seconds
   └─ Clicks "Verify Code"
   
5. STEP 3: COMPLETE PROFILE
   ├─ User enters Full Name
   ├─ User sets Password (min 8 chars)
   └─ Clicks "Create Account & Continue to Payment"
   
6. ACCOUNT CREATION
   ├─ Creates Frappe User
   ├─ Creates AI Customer (email_verified = 1)
   ├─ Creates AI Subscription (status = Pending)
   ├─ Auto-login
   └─ Sends Welcome Email
   
7. PAYMENT REDIRECT
   ├─ Creates AI Invoice
   ├─ Generates PayU payment hash
   ├─ Redirects to PayU gateway
   └─ User pays with card
   
8. PAYMENT SUCCESS
   ├─ PayU callback to /api/method/.../payu_success
   ├─ Updates Invoice (status = Paid)
   ├─ Activates Subscription (status = Active)
   ├─ Generates API Key
   └─ Redirects to /payment-success
   
9. USER DASHBOARD
   └─ /my-profile
      ├─ View API Key
      ├─ See subscription details
      ├─ Download VS Code extension
      └─ Start using AI features
```

---

## 📧 **OTP Email Example**

```html
╔══════════════════════════════════════════════╗
║            Oropendola AI                      ║
║        (Purple Gradient Logo)                 ║
╚══════════════════════════════════════════════╝

Your Verification Code
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Welcome! Use this code to complete your
registration:

        ┌─────────────────┐
        │   1 2 3 4 5 6   │
        └─────────────────┘

⏱️ This code expires in 10 minutes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 Security Tip: Never share this code with
   anyone.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 Selected Plan: 7 Days - ₹849

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Need help? support@oropendola.ai
```

---

## 🔌 **API Endpoints**

### **1. Send OTP**
```http
POST /api/method/oropendola_ai.oropendola_ai.api.otp_auth.send_otp

{
  "email": "user@example.com",
  "purpose": "signup",
  "plan_id": "7-days"
}

Response:
{
  "success": true,
  "message": "Verification code sent to user@example.com",
  "expires_in": 600
}
```

### **2. Verify OTP**
```http
POST /api/method/oropendola_ai.oropendola_ai.api.otp_auth.verify_otp

{
  "email": "user@example.com",
  "otp": "123456",
  "purpose": "signup"
}

Response:
{
  "success": true,
  "message": "Verification successful!",
  "email": "user@example.com",
  "plan_id": "7-days"
}
```

### **3. Resend OTP**
```http
POST /api/method/oropendola_ai.oropendola_ai.api.otp_auth.resend_otp

{
  "email": "user@example.com",
  "purpose": "signup",
  "plan_id": "7-days"
}

Response:
{
  "success": true,
  "message": "Verification code sent to user@example.com",
  "expires_in": 600
}
```

### **4. Complete Signup**
```http
POST /api/method/oropendola_ai.oropendola_ai.api.otp_auth.signup_with_otp

{
  "email": "user@example.com",
  "full_name": "John Doe",
  "password": "SecurePass123!",
  "otp": "123456",
  "plan_id": "7-days"
}

Response:
{
  "success": true,
  "message": "Account created successfully!",
  "user_id": "user@example.com",
  "customer_id": "CUST-0001",
  "subscription_id": "AI-SUB-0001",
  "plan_id": "7-days"
}
```

### **5. Login with OTP**
```http
POST /api/method/oropendola_ai.oropendola_ai.api.otp_auth.login_with_otp

{
  "email": "user@example.com",
  "otp": "123456"
}

Response:
{
  "success": true,
  "message": "Login successful!",
  "user_id": "user@example.com",
  "redirect": "/my-profile"
}
```

---

## 🔒 **Security Features**

### **Implemented:**

✅ **OTP Hashing** - SHA-256, stored hash only  
✅ **Single Use** - OTP deleted after verification  
✅ **Expiry** - 10-minute validity  
✅ **Rate Limiting** - 30-second cooldown between resends  
✅ **Attempt Limiting** - Max 3 failed attempts  
✅ **Email Validation** - Format checking  
✅ **Duplicate Prevention** - Checks existing users  
✅ **CSRF Protection** - Token validation  
✅ **Secure Password** - Minimum 8 characters  
✅ **Auto-logout on Expiry** - Session management

---

## 🎨 **UI/UX Features**

### **Modal Popup:**
- ✅ Dark theme matching Oropendola brand
- ✅ Purple-cyan gradient accents
- ✅ 3-step wizard (Email → OTP → Signup)
- ✅ Auto-focus inputs
- ✅ Auto-advance OTP digits
- ✅ Live countdown timer
- ✅ Resend link with cooldown
- ✅ Escape key to close
- ✅ Outside click to close
- ✅ Loading spinners
- ✅ Error handling
- ✅ Success animations

---

## 💾 **Database Records Created**

### **On Signup:**

**1. User** (Frappe Core)
```python
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "enabled": 1,
  "user_type": "Website User"
}
```

**2. AI Customer**
```python
{
  "customer_name": "John Doe",
  "email": "user@example.com",
  "user": "user@example.com",
  "email_verified": 1,  # OTP verified
  "status": "Active"
}
```

**3. AI Subscription**
```python
{
  "user": "user@example.com",
  "customer": "CUST-0001",
  "plan": "7-days",
  "status": "Pending",  # Active after payment
  "start_date": "2025-01-15",
  "end_date": "2025-01-22",
  "daily_quota_limit": 300,
  "daily_quota_remaining": 300,
  "monthly_budget_limit": 1000,
  "monthly_budget_used": 0,
  "auto_renew": 1
}
```

**4. AI Invoice**
```python
{
  "user": "user@example.com",
  "subscription": "AI-SUB-0001",
  "plan": "7-days",
  "status": "Pending",  # Paid after PayU
  "total_amount": 849,
  "currency": "INR",
  "payment_gateway": "PayU"
}
```

**5. AI API Key** (after payment)
```python
{
  "name": "oro_xxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "user": "user@example.com",
  "subscription": "AI-SUB-0001",
  "is_active": 1
}
```

---

## 🧪 **Testing the Flow**

### **Test OTP Email:**
```bash
curl -X POST 'https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.otp_auth.send_otp' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "your@email.com",
    "purpose": "signup",
    "plan_id": "7-days"
  }'
```

### **Check Email:**
You'll receive an email with a 6-digit code.

### **Test Complete Flow:**
1. Visit https://oropendola.ai/pricing
2. Click "Subscribe Now" on any plan
3. Enter your email in the popup
4. Check your email for the OTP
5. Enter the 6-digit code
6. Complete your profile
7. Proceed to payment

---

## 💻 **VS Code Extension Integration**

### **Ready for Implementation:**

The OTP system is ready to integrate with VS Code extension for "Plan Expired" notifications.

### **Extension Flow:**

```javascript
// VS Code Extension - Check Subscription Status
async function checkSubscription(apiKey) {
  const response = await fetch(
    'https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.validate_api_key',
    {
      headers: {
        'Authorization': `token ${apiKey}`
      }
    }
  );
  
  const data = await response.json();
  
  if (data.message && data.message.subscription_expired) {
    vscode.window.showWarningMessage(
      'Your Oropendola AI plan has expired. Please renew to continue.',
      'Renew Now'
    ).then(selection => {
      if (selection === 'Renew Now') {
        vscode.env.openExternal(
          vscode.Uri.parse('https://oropendola.ai/pricing')
        );
      }
    });
  }
}
```

---

## 📊 **AI Plans Configuration**

### **Current Plans:**

| Plan | Price | Duration | Requests/Day | Models |
|------|-------|----------|--------------|--------|
| 1 Day Trial | ₹199 | 1 day | 200 | 5 |
| 7 Days | ₹849 | 7 days | 300 | 5 |
| 1 Month Unlimited | ₹2999 | 30 days | Unlimited | 5 |

### **Model Distribution (Cost Weights):**
- DeepSeek: 60%
- Grok: 10%
- Claude: 10%
- GPT-4: 10%
- Gemini: 10%

---

## 🚀 **Next Steps**

### **Optional Enhancements:**

1. **SMS OTP** - Add phone number field + SMS gateway
2. **Social Login** - Google/GitHub OAuth
3. **2FA** - Optional two-factor authentication
4. **Email Templates** - More customization options
5. **Rate Limiting** - Global rate limiting per IP
6. **Captcha** - Prevent bot signups
7. **Email Domain Validation** - Block disposable emails
8. **Password Strength Meter** - Visual feedback
9. **Password Recovery** - OTP-based password reset
10. **VS Code Extension** - Complete implementation

---

## 📞 **Support**

If users face issues:

- **Email not received?** → Check spam folder, resend OTP
- **OTP expired?** → Request new code
- **Payment failed?** → Retry from dashboard
- **API key issues?** → Contact support@oropendola.ai

---

## ✅ **Implementation Checklist**

- [x] OTP Backend API created
- [x] Email templates designed
- [x] OTP verification logic
- [x] Rate limiting implemented
- [x] Frontend modal created
- [x] 3-step wizard flow
- [x] Auto-advance OTP inputs
- [x] Timer countdown
- [x] Resend functionality
- [x] Password validation
- [x] User creation
- [x] Subscription creation
- [x] Payment integration
- [x] Welcome email
- [x] Auto-login
- [x] Error handling
- [x] Security features
- [x] Documentation
- [ ] VS Code extension integration
- [ ] SMS OTP (optional)
- [ ] Social login (optional)

---

## 🎉 **COMPLETE & READY TO USE!**

The OTP-based subscription workflow is **fully implemented** and **production-ready**.

Users can now:
✅ Sign up with email OTP verification  
✅ Complete payment seamlessly  
✅ Get instant access to AI features  
✅ Use VS Code extension (after integration)

**Test it now at: https://oropendola.ai/pricing**
# OTP-Based Subscription Workflow - Implementation Guide

## 🎉 COMPLETE IMPLEMENTATION SUMMARY

### ✅ **What Has Been Built**

This document describes the complete OTP-based subscription workflow for Oropendola AI, including:

1. **Backend OTP Authentication System**
2. **Frontend Login/Signup Modal with OTP**
3. **Payment Integration**
4. **VS Code Extension Support** (ready for integration)

---

## 📁 **Files Created/Modified**

### **Backend API:**
- `/oropendola_ai/oropendola_ai/api/otp_auth.py` - OTP authentication endpoints

### **Frontend:**
- `/oropendola_ai/www/pricing/index.html` - Updated with modal integration
- `/oropendola_ai/templates/pricing/auth-modal.html` - OTP authentication modal

### **Installation:**
- `/oropendola_ai/install.py` - AI Plans creation with cost weights

---

## 🔄 **Complete User Flow**

### **Step-by-Step Journey:**

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER SUBSCRIPTION FLOW                      │
└─────────────────────────────────────────────────────────────────┘

1. USER VISITS PRICING PAGE
   ↓
   https://oropendola.ai/pricing
   └─ Sees 3 plans: ₹199, ₹849, ₹2999

2. USER CLICKS "SUBSCRIBE NOW"
   ↓
   Opens Authentication Modal (Popup)
   
3. STEP 1: EMAIL INPUT
   ├─ User enters email: user@example.com
   ├─ Clicks "Continue"
   └─ System sends 6-digit OTP to email
   
4. STEP 2: OTP VERIFICATION
   ├─ User receives email with code (e.g., 123456)
   ├─ Enters 6-digit code in modal
   ├─ Auto-advances between digits
   ├─ 10-minute timer shown
   ├─ Can resend after 30 seconds
   └─ Clicks "Verify Code"
   
5. STEP 3: COMPLETE PROFILE
   ├─ User enters Full Name
   ├─ User sets Password (min 8 chars)
   └─ Clicks "Create Account & Continue to Payment"
   
6. ACCOUNT CREATION
   ├─ Creates Frappe User
   ├─ Creates AI Customer (email_verified = 1)
   ├─ Creates AI Subscription (status = Pending)
   ├─ Auto-login
   └─ Sends Welcome Email
   
7. PAYMENT REDIRECT
   ├─ Creates AI Invoice
   ├─ Generates PayU payment hash
   ├─ Redirects to PayU gateway
   └─ User pays with card
   
8. PAYMENT SUCCESS
   ├─ PayU callback to /api/method/.../payu_success
   ├─ Updates Invoice (status = Paid)
   ├─ Activates Subscription (status = Active)
   ├─ Generates API Key
   └─ Redirects to /payment-success
   
9. USER DASHBOARD
   └─ /my-profile
      ├─ View API Key
      ├─ See subscription details
      ├─ Download VS Code extension
      └─ Start using AI features
```

---

## 📧 **OTP Email Example**

```html
╔══════════════════════════════════════════════╗
║            Oropendola AI                      ║
║        (Purple Gradient Logo)                 ║
╚══════════════════════════════════════════════╝

Your Verification Code
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Welcome! Use this code to complete your
registration:

        ┌─────────────────┐
        │   1 2 3 4 5 6   │
        └─────────────────┘

⏱️ This code expires in 10 minutes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 Security Tip: Never share this code with
   anyone.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 Selected Plan: 7 Days - ₹849

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Need help? support@oropendola.ai
```

---

## 🔌 **API Endpoints**

### **1. Send OTP**
```http
POST /api/method/oropendola_ai.oropendola_ai.api.otp_auth.send_otp

{
  "email": "user@example.com",
  "purpose": "signup",
  "plan_id": "7-days"
}

Response:
{
  "success": true,
  "message": "Verification code sent to user@example.com",
  "expires_in": 600
}
```

### **2. Verify OTP**
```http
POST /api/method/oropendola_ai.oropendola_ai.api.otp_auth.verify_otp

{
  "email": "user@example.com",
  "otp": "123456",
  "purpose": "signup"
}

Response:
{
  "success": true,
  "message": "Verification successful!",
  "email": "user@example.com",
  "plan_id": "7-days"
}
```

### **3. Resend OTP**
```http
POST /api/method/oropendola_ai.oropendola_ai.api.otp_auth.resend_otp

{
  "email": "user@example.com",
  "purpose": "signup",
  "plan_id": "7-days"
}

Response:
{
  "success": true,
  "message": "Verification code sent to user@example.com",
  "expires_in": 600
}
```

### **4. Complete Signup**
```http
POST /api/method/oropendola_ai.oropendola_ai.api.otp_auth.signup_with_otp

{
  "email": "user@example.com",
  "full_name": "John Doe",
  "password": "SecurePass123!",
  "otp": "123456",
  "plan_id": "7-days"
}

Response:
{
  "success": true,
  "message": "Account created successfully!",
  "user_id": "user@example.com",
  "customer_id": "CUST-0001",
  "subscription_id": "AI-SUB-0001",
  "plan_id": "7-days"
}
```

### **5. Login with OTP**
```http
POST /api/method/oropendola_ai.oropendola_ai.api.otp_auth.login_with_otp

{
  "email": "user@example.com",
  "otp": "123456"
}

Response:
{
  "success": true,
  "message": "Login successful!",
  "user_id": "user@example.com",
  "redirect": "/my-profile"
}
```

---

## 🔒 **Security Features**

### **Implemented:**

✅ **OTP Hashing** - SHA-256, stored hash only  
✅ **Single Use** - OTP deleted after verification  
✅ **Expiry** - 10-minute validity  
✅ **Rate Limiting** - 30-second cooldown between resends  
✅ **Attempt Limiting** - Max 3 failed attempts  
✅ **Email Validation** - Format checking  
✅ **Duplicate Prevention** - Checks existing users  
✅ **CSRF Protection** - Token validation  
✅ **Secure Password** - Minimum 8 characters  
✅ **Auto-logout on Expiry** - Session management

---

## 🎨 **UI/UX Features**

### **Modal Popup:**
- ✅ Dark theme matching Oropendola brand
- ✅ Purple-cyan gradient accents
- ✅ 3-step wizard (Email → OTP → Signup)
- ✅ Auto-focus inputs
- ✅ Auto-advance OTP digits
- ✅ Live countdown timer
- ✅ Resend link with cooldown
- ✅ Escape key to close
- ✅ Outside click to close
- ✅ Loading spinners
- ✅ Error handling
- ✅ Success animations

---

## 💾 **Database Records Created**

### **On Signup:**

**1. User** (Frappe Core)
```python
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "enabled": 1,
  "user_type": "Website User"
}
```

**2. AI Customer**
```python
{
  "customer_name": "John Doe",
  "email": "user@example.com",
  "user": "user@example.com",
  "email_verified": 1,  # OTP verified
  "status": "Active"
}
```

**3. AI Subscription**
```python
{
  "user": "user@example.com",
  "customer": "CUST-0001",
  "plan": "7-days",
  "status": "Pending",  # Active after payment
  "start_date": "2025-01-15",
  "end_date": "2025-01-22",
  "daily_quota_limit": 300,
  "daily_quota_remaining": 300,
  "monthly_budget_limit": 1000,
  "monthly_budget_used": 0,
  "auto_renew": 1
}
```

**4. AI Invoice**
```python
{
  "user": "user@example.com",
  "subscription": "AI-SUB-0001",
  "plan": "7-days",
  "status": "Pending",  # Paid after PayU
  "total_amount": 849,
  "currency": "INR",
  "payment_gateway": "PayU"
}
```

**5. AI API Key** (after payment)
```python
{
  "name": "oro_xxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "user": "user@example.com",
  "subscription": "AI-SUB-0001",
  "is_active": 1
}
```

---

## 🧪 **Testing the Flow**

### **Test OTP Email:**
```bash
curl -X POST 'https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.otp_auth.send_otp' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "your@email.com",
    "purpose": "signup",
    "plan_id": "7-days"
  }'
```

### **Check Email:**
You'll receive an email with a 6-digit code.

### **Test Complete Flow:**
1. Visit https://oropendola.ai/pricing
2. Click "Subscribe Now" on any plan
3. Enter your email in the popup
4. Check your email for the OTP
5. Enter the 6-digit code
6. Complete your profile
7. Proceed to payment

---

## 💻 **VS Code Extension Integration**

### **Ready for Implementation:**

The OTP system is ready to integrate with VS Code extension for "Plan Expired" notifications.

### **Extension Flow:**

```javascript
// VS Code Extension - Check Subscription Status
async function checkSubscription(apiKey) {
  const response = await fetch(
    'https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.validate_api_key',
    {
      headers: {
        'Authorization': `token ${apiKey}`
      }
    }
  );
  
  const data = await response.json();
  
  if (data.message && data.message.subscription_expired) {
    vscode.window.showWarningMessage(
      'Your Oropendola AI plan has expired. Please renew to continue.',
      'Renew Now'
    ).then(selection => {
      if (selection === 'Renew Now') {
        vscode.env.openExternal(
          vscode.Uri.parse('https://oropendola.ai/pricing')
        );
      }
    });
  }
}
```

---

## 📊 **AI Plans Configuration**

### **Current Plans:**

| Plan | Price | Duration | Requests/Day | Models |
|------|-------|----------|--------------|--------|
| 1 Day Trial | ₹199 | 1 day | 200 | 5 |
| 7 Days | ₹849 | 7 days | 300 | 5 |
| 1 Month Unlimited | ₹2999 | 30 days | Unlimited | 5 |

### **Model Distribution (Cost Weights):**
- DeepSeek: 60%
- Grok: 10%
- Claude: 10%
- GPT-4: 10%
- Gemini: 10%

---

## 🚀 **Next Steps**

### **Optional Enhancements:**

1. **SMS OTP** - Add phone number field + SMS gateway
2. **Social Login** - Google/GitHub OAuth
3. **2FA** - Optional two-factor authentication
4. **Email Templates** - More customization options
5. **Rate Limiting** - Global rate limiting per IP
6. **Captcha** - Prevent bot signups
7. **Email Domain Validation** - Block disposable emails
8. **Password Strength Meter** - Visual feedback
9. **Password Recovery** - OTP-based password reset
10. **VS Code Extension** - Complete implementation

---

## 📞 **Support**

If users face issues:

- **Email not received?** → Check spam folder, resend OTP
- **OTP expired?** → Request new code
- **Payment failed?** → Retry from dashboard
- **API key issues?** → Contact support@oropendola.ai

---

## ✅ **Implementation Checklist**

- [x] OTP Backend API created
- [x] Email templates designed
- [x] OTP verification logic
- [x] Rate limiting implemented
- [x] Frontend modal created
- [x] 3-step wizard flow
- [x] Auto-advance OTP inputs
- [x] Timer countdown
- [x] Resend functionality
- [x] Password validation
- [x] User creation
- [x] Subscription creation
- [x] Payment integration
- [x] Welcome email
- [x] Auto-login
- [x] Error handling
- [x] Security features
- [x] Documentation
- [ ] VS Code extension integration
- [ ] SMS OTP (optional)
- [ ] Social login (optional)

---

## 🎉 **COMPLETE & READY TO USE!**

The OTP-based subscription workflow is **fully implemented** and **production-ready**.

Users can now:
✅ Sign up with email OTP verification  
✅ Complete payment seamlessly  
✅ Get instant access to AI features  
✅ Use VS Code extension (after integration)

**Test it now at: https://oropendola.ai/pricing**
