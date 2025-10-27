# 🚀 VS Code Authentication - Quick Reference

## 🔗 Customer-Subscription Linking

```
AI Customer (email, name, status)
     ↓ [user field]
Frappe User (email, enabled)
     ↓ [subscription.customer]
AI Subscription (plan, api_key)
     ↓ [api_key_link]
API Key (key_hash, status)
```

---

## 🔄 Auth Flow (5 Steps)

### **Step 1: Initiate** (VS Code)
```bash
POST /api/method/oropendola_ai.oropendola_ai.api.auth.initiate_signin
{
  "email": "user@example.com"
}

→ Returns: { auth_url, state }
```

### **Step 2: Open Browser** (VS Code)
```typescript
vscode.env.openExternal(auth_url);
```

### **Step 3: Authenticate** (Browser)
```
Browser → https://oropendola.ai/.../authenticate?email=...&state=...

If new user → Redirect to /signup
If existing → Redirect to /dashboard (or /verification-pending)
```

### **Step 4: Sign Up** (User)
```html
<form action="/api/method/.../signup">
  <input name="email" value="user@example.com" />
  <input name="customer_name" placeholder="Name" />
  <button>Sign Up</button>
</form>

→ Creates AI Customer
→ Sends verification email
```

### **Step 5: Verify Email** (User)
```
User clicks link in email:
https://oropendola.ai/.../verify_email?token=...

→ Marks email_verified=1
→ Creates Frappe User
→ Creates AI Subscription
→ Generates API Key
```

### **Step 6: Poll Status** (VS Code)
```typescript
// Every 5 seconds
POST /api/method/.../check_auth_status
{ "state": "xyz789" }

Responses:
- { status: "pending" } → Keep polling
- { status: "verification_pending" } → Keep polling
- { status: "complete", api_key: "..." } → Done!
```

---

## 📝 API Endpoints Summary

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `initiate_signin` | ❌ Guest | Start auth flow |
| `authenticate` | ❌ Guest | Browser redirect handler |
| `signup` | ❌ Guest | Create new customer |
| `verify_email` | ❌ Guest | Verify email token |
| `check_auth_status` | ❌ Guest | Poll for completion |
| `resend_verification` | ❌ Guest | Resend verification |
| `get_api_key` | ✅ User | Get API key (logged in) |

---

## 💾 Key Data Fields

### **AI Customer**
```python
{
    "customer_name": "John Doe",
    "email": "john@example.com",
    "user": "john@example.com",  # Link to Frappe User
    "status": "Active" | "Pending Verification",
    "email_verified": 1,
    "verification_token": "sha256_hash",
    "verification_sent_at": "2025-10-27 10:00:00",
    "verified_at": "2025-10-27 10:05:00"
}
```

### **AI Subscription**
```python
{
    "customer": "AIC.25.0001",  # Link to AI Customer
    "plan": "free",
    "status": "Active",
    "billing_email": "john@example.com",
    "api_key_link": "APIKEY-001"
}
```

---

## 🔐 Security Tokens

### **State Token** (CSRF)
- **Purpose**: CSRF protection
- **Storage**: Redis (5 min)
- **Format**: `secrets.token_urlsafe(32)`
- **Usage**: Link email to auth session

### **Verification Token**
- **Purpose**: Email verification
- **Storage**: Database (SHA-256 hash)
- **Expiry**: 24 hours
- **Usage**: Single-use verification link

### **API Key**
- **Purpose**: API authentication
- **Storage**: Database (SHA-256 hash) + Cache (5 min)
- **Format**: `secrets.token_urlsafe(32)`
- **Shown**: Only once (after creation)

---

## 📧 Email Verification

### **Sent Automatically**
- After customer creation (`after_insert`)
- When resend requested
- When unverified user tries to sign in

### **Email Content**
```
Subject: Verify Your Oropendola AI Account

Hello John,
Click below to verify:
[Verify Email Button]

Link: https://oropendola.ai/.../verify_email?token=...
Expires in 24 hours
```

### **Token Validation**
```python
# Hash provided token
token_hash = hashlib.sha256(token.encode()).hexdigest()

# Check matches stored hash
if token_hash == customer.verification_token:
    # Check expiry (24 hours)
    if now() < verification_sent_at + 24h:
        # Valid!
        customer.email_verified = 1
        customer.create_frappe_user()
```

---

## 🎯 Status Flow

### **Customer Status**
```
New Customer
    ↓
Pending Verification (email sent)
    ↓ [user clicks verify link]
Active (email verified, user created)
```

### **Auth Status (Polling)**
```
pending → User hasn't signed up yet
    ↓
verification_pending → Signed up, waiting for email verify
    ↓
complete → Email verified, API key ready
```

---

## 🛠️ Common Operations

### **Check if Customer Exists**
```python
customer_id = frappe.db.exists("AI Customer", {"email": email})
```

### **Get Customer's Subscription**
```python
subscription = frappe.get_all(
    "AI Subscription",
    filters={"customer": customer_id, "status": ["in", ["Active", "Trial"]]},
    limit=1
)
```

### **Get API Key from Subscription**
```python
subscription = frappe.get_doc("AI Subscription", subscription_id)
api_key = frappe.get_doc("AI API Key", subscription.api_key_link)
```

### **Verify Customer**
```python
customer.verify_email(token)
# → Sets email_verified=1
# → Creates Frappe User
# → Customer.user = user.name
```

### **Create Subscription**
```python
customer.get_or_create_subscription(plan_id="free")
# → Returns existing or creates new
# → Automatically generates API key
```

---

## 📱 Frontend Pages

| Page | URL | Purpose |
|------|-----|---------|
| Sign Up | `/signup?email=...&state=...` | New user registration |
| Pending | `/verification-pending?email=...` | Waiting for email |
| Success | `/verification-success?email=...` | Email verified! |
| Error | `/verification-error?reason=...` | Verification failed |
| Dashboard | `/dashboard` | Logged-in user home |

---

## 🔍 Troubleshooting

### **Verification Email Not Received**
1. Check spam folder
2. Resend via: `POST /api/method/.../resend_verification`
3. Check email service logs

### **Token Expired**
1. Request new verification: `POST /api/method/.../resend_verification`
2. New token generated (old one invalidated)

### **API Key Lost**
1. Cannot retrieve after initial display
2. Contact support or regenerate via dashboard

### **Polling Never Completes**
1. Check browser completed verification
2. Verify state token hasn't expired (5 min)
3. Check customer email_verified=1

---

## 🧪 Testing

### **Test New User Flow**
```bash
# 1. Initiate
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.auth.initiate_signin \
  -d '{"email":"test@example.com"}'

# 2. Sign up
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.auth.signup \
  -d '{"email":"test@example.com","customer_name":"Test User","state":"..."}'

# 3. Poll status
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.auth.check_auth_status \
  -d '{"state":"..."}'
```

---

## 📊 Key Methods

### **AI Customer Methods**
```python
customer.send_verification_email()
customer.verify_email(token) → bool
customer.create_frappe_user()
customer.get_or_create_subscription(plan_id) → subscription
```

### **Auth API Methods**
```python
auth.initiate_signin(email) → {auth_url, state}
auth.authenticate(email, state) → HTTP redirect
auth.signup(email, name, state) → {success, customer_id}
auth.verify_email(token) → HTTP redirect
auth.check_auth_status(state) → {status, api_key?}
auth.resend_verification(email) → {success}
auth.get_api_key() → {api_key, subscription}
```

---

## ✅ Quick Checklist

### **For VS Code Extension**
- [ ] Call `initiate_signin` with user email
- [ ] Open returned `auth_url` in browser
- [ ] Start polling `check_auth_status` every 5s
- [ ] Store API key when status="complete"
- [ ] Handle errors gracefully

### **For Backend**
- [x] Enhanced AI Customer with verification
- [x] Created auth API endpoints
- [x] Implemented email verification
- [x] Added polling mechanism
- [x] Integrated with subscriptions

### **For Frontend**
- [ ] Build /signup page
- [ ] Build /verification-pending page
- [ ] Build /verification-success page
- [ ] Build /verification-error page
- [ ] Build /dashboard page

---

**Quick Start**: Read [`VSCODE_AUTHENTICATION_FLOW.md`](./VSCODE_AUTHENTICATION_FLOW.md) for complete details!
