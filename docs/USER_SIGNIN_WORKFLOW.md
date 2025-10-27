# 🔐 Complete User Sign-In Workflow - Oropendola AI

## Overview

This document explains the **complete end-to-end workflow** of what happens after a user successfully signs in to the Oropendola AI system, including authentication verification, session establishment, subscription linking, and API key management.

---

## 🎯 Architecture: Frappe User-Based System

Oropendola AI uses **Frappe's built-in User system** for authentication, eliminating the need for custom authentication logic.

### **Core Components**

```
┌─────────────────┐
│  Frappe User    │  ← Primary Identity (email, password, session)
└────────┬────────┘
         │ user field
         ↓
┌─────────────────┐
│ AI Subscription │  ← Plan, quota, budget tracking
└────────┬────────┘
         │ api_key_link
         ↓
┌─────────────────┐
│   AI API Key    │  ← Secure hash, usage tracking
└─────────────────┘
```

---

## 📋 Complete Workflow: Step-by-Step

### **Phase 1: User Registration & Email Verification**

#### **Step 1.1: User Signs Up**

```
URL: https://oropendola.ai/login#signup
```

**User submits**:
- Email address
- Full name
- Password

**Frappe Framework handles**:
1. Validates email uniqueness
2. Hashes password (BCrypt)
3. Creates User document with `user_type: "Website User"`
4. Sets `enabled: 0` (disabled until verified)
5. Generates verification token
6. Sends verification email

**Code Location**: Built-in Frappe (`frappe/core/doctype/user/user.py`)

---

#### **Step 1.2: Email Verification**

**User receives email** with verification link:
```
https://oropendola.ai/api/method/frappe.core.doctype.user.user.verify_email?key=<token>
```

**User clicks link → Frappe**:
1. Validates token (not expired, matches hash)
2. Updates User: `enabled: 1`, `email_verified: 1`
3. Triggers `after_insert` event (if first verification)
4. **Redirects to**: `/login` or custom redirect URL

**Code Location**: Built-in Frappe

---

### **Phase 2: Auto-Subscription Creation Hook**

#### **Step 2.1: Hook Triggers**

**File**: [`hooks.py`](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/hooks.py#L139-L145)

```python
doc_events = {
    "User": {
        "after_insert": "oropendola_ai.oropendola_ai.utils.user_utils.create_default_subscription"
    }
}
```

**Triggered**: Immediately after User document is created (after email verification).

---

#### **Step 2.2: Auto-Create Subscription**

**File**: [`user_utils.py`](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/oropendola_ai/utils/user_utils.py#L11-L72)

**Function**: `create_default_subscription(user, method)`

**Logic**:

```python
# 1. Check if Website User (not System User)
if user.user_type != "Website User":
    return  # Skip admin/internal users

# 2. Check if user is enabled
if not user.enabled:
    return  # Skip disabled users

# 3. Check for existing subscription
existing = frappe.db.exists("AI Subscription", {
    "user": user.name, 
    "status": ["in", ["Active", "Trial"]]
})
if existing:
    return  # User already has subscription

# 4. Find free plan
free_plan = frappe.db.get_value("AI Plan", {
    "plan_id": "free", 
    "is_active": 1
})

# 5. Create AI Subscription
subscription = frappe.get_doc({
    "doctype": "AI Subscription",
    "user": user.name,  # Link to Frappe User
    "plan": free_plan,
    "status": "Active",
    "billing_email": user.email
})
subscription.insert(ignore_permissions=True)
frappe.db.commit()
```

**Result**: User now has an active AI Subscription!

---

### **Phase 3: Subscription Initialization**

#### **Step 3.1: Subscription `before_insert` Event**

**File**: [`ai_subscription.py`](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/oropendola_ai/doctype/ai_subscription/ai_subscription.py#L17-L21)

**Method**: `before_insert()`

**Operations**:

```python
def before_insert(self):
    self.set_dates()                    # Set start/end dates
    self.set_quota()                    # Initialize daily quota
    self.initialize_monthly_budget()    # Initialize budget tracking
    self.created_by_user = frappe.session.user
```

**Details**:

**1. Set Dates** ([`set_dates()`](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/oropendola_ai/doctype/ai_subscription/ai_subscription.py#L30-L42)):
```python
# Start date = today
self.start_date = today()

# Get plan details
plan = frappe.get_doc("AI Plan", self.plan)

# Calculate end date if plan has duration
if plan.duration_days > 0:
    self.end_date = add_days(self.start_date, plan.duration_days)

# Set trial status if applicable
if plan.is_trial:
    self.status = "Trial"
    self.trial_end_date = self.end_date
```

**2. Set Quota** ([`set_quota()`](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/oropendola_ai/doctype/ai_subscription/ai_subscription.py#L44-L49)):
```python
plan = frappe.get_doc("AI Plan", self.plan)

# Daily request quota from plan
self.daily_quota_limit = plan.requests_limit_per_day
self.daily_quota_remaining = plan.requests_limit_per_day

# Priority score for routing
self.priority_score = plan.priority_score
```

**3. Initialize Monthly Budget** ([`initialize_monthly_budget()`](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/oropendola_ai/doctype/ai_subscription/ai_subscription.py#L175-L186)):
```python
import datetime

# First day of current month
today_date = datetime.date.today()
self.current_month_start = today_date.replace(day=1)

# Reset budget used
self.monthly_budget_used = 0.0

# Set alert threshold (90% by default)
self.budget_alert_threshold = 0.9
```

---

#### **Step 3.2: Subscription `after_insert` Event**

**File**: [`ai_subscription.py`](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/oropendola_ai/doctype/ai_subscription/ai_subscription.py#L23-L25)

**Method**: `after_insert()`

**Operation**: Automatically create API key!

```python
def after_insert(self):
    """Create API key after subscription is created"""
    self.create_api_key()
```

---

### **Phase 4: API Key Generation**

#### **Step 4.1: Generate Secure API Key**

**File**: [`ai_subscription.py`](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/oropendola_ai/doctype/ai_subscription/ai_subscription.py#L72-L105)

**Method**: `create_api_key()`

**Process**:

```python
import secrets
import hashlib

# 1. Generate random 32-byte API key
raw_key = secrets.token_urlsafe(32)
# Example: "xyz789abc123def456ghi789jkl012mno345pqr678stu901vwx234"

# 2. Hash the key (SHA-256)
key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
# Store hash only - raw key NEVER stored in database

# 3. Create AI API Key document
api_key_doc = frappe.get_doc({
    "doctype": "AI API Key",
    "user": self.user,              # Link to Frappe User
    "subscription": self.name,       # Link to subscription
    "key_hash": key_hash,            # SHA-256 hash
    "key_prefix": raw_key[:8],       # First 8 chars for display
    "status": "Active",
    "created_by": frappe.session.user
})
api_key_doc.insert(ignore_permissions=True)

# 4. Link API key to subscription
self.db_set("api_key_link", api_key_doc.name)

# 5. Cache raw key (5 minutes only!)
cache_key = f"api_key_raw:{self.name}"
frappe.cache().set_value(cache_key, raw_key, expires_in_sec=300)
```

**Security**:
- ✅ Raw key **never stored** in database
- ✅ Only SHA-256 hash stored
- ✅ Raw key cached for 5 minutes only
- ✅ User must retrieve immediately

---

### **Phase 5: User Sign-In**

#### **Step 5.1: User Logs In**

```
URL: https://oropendola.ai/login#login
```

**User submits**:
- Email: `user@example.com`
- Password: `********`

**Frappe handles**:
1. Validates credentials (BCrypt hash comparison)
2. Creates session (HTTP-only cookie)
3. Generates CSRF token
4. **Redirects to**: `/dashboard` or custom home page

**Session Cookie** (set by Frappe):
```
sid=<session_id>; HttpOnly; Secure; SameSite=Lax
```

**Code Location**: Built-in Frappe (`frappe/auth.py`)

---

#### **Step 5.2: Session Established**

**Session Data** (stored in Redis/Memcache):
```python
{
    "user": "user@example.com",
    "session_id": "abc123def456...",
    "device": "Mozilla/5.0...",
    "last_updated": "2025-10-27 12:34:56",
    "csrf_token": "xyz789..."
}
```

**Session Management**:
- ✅ Automatic expiry (configurable)
- ✅ Multi-device support
- ✅ CSRF protection
- ✅ IP tracking (optional)

---

### **Phase 6: Authenticated User Flow**

#### **Step 6.1: User Navigates to Dashboard**

**URL**: `https://oropendola.ai/dashboard`

**Page loads → JavaScript calls**:

```javascript
// Get API key
fetch('/api/method/oropendola_ai.oropendola_ai.api.user_api.get_my_api_key', {
    method: 'POST',
    credentials: 'include'  // Include session cookie
})
```

---

#### **Step 6.2: API Key Retrieval**

**File**: [`user_api.py`](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/oropendola_ai/api/user_api.py#L13-L87)

**Function**: `get_my_api_key()`

**Process**:

```python
# 1. Check authentication
if frappe.session.user == "Guest":
    return {"success": False, "error": "Authentication required"}

# 2. Get active subscription for current user
subscriptions = frappe.get_all(
    "AI Subscription",
    filters={
        "user": frappe.session.user,  # Current logged-in user
        "status": ["in", ["Active", "Trial"]]
    },
    fields=["name", "plan", "status", "api_key_link"],
    limit=1
)

if not subscriptions:
    return {"success": False, "error": "No active subscription"}

subscription = subscriptions[0]

# 3. Get API key document
api_key = frappe.get_doc("AI API Key", subscription.api_key_link)

# 4. Try to get raw key from cache
cache_key = f"api_key_raw:{subscription.name}"
raw_key = frappe.cache().get_value(cache_key)

if raw_key:
    # Raw key available (within 5 minutes of creation)
    return {
        "success": True,
        "api_key": raw_key,  # Full key shown
        "api_key_prefix": api_key.key_prefix,
        "subscription_id": subscription.name,
        "plan": subscription.plan,
        "warning": "⚠️ Store it securely - won't be shown again!"
    }
else:
    # Raw key expired from cache
    return {
        "success": True,
        "api_key": None,  # Not available
        "api_key_prefix": api_key.key_prefix,  # Only prefix
        "message": "API key already retrieved. Regenerate if lost."
    }
```

**Response Example** (first time):
```json
{
  "success": true,
  "api_key": "xyz789abc123def456ghi789jkl012mno345pqr678stu901vwx234",
  "api_key_prefix": "xyz789ab",
  "subscription_id": "SUB-2025-00001",
  "plan": "free",
  "status": "Active",
  "warning": "⚠️ Store it securely - it will not be shown again!"
}
```

---

#### **Step 6.3: User Stores API Key**

**Frontend JavaScript**:

```javascript
const data = await response.json();

if (data.success && data.api_key) {
    // Display API key (one time only!)
    document.getElementById('api-key-display').textContent = data.api_key;
    
    // Warn user to copy
    alert(data.warning);
    
    // User copies to VS Code extension or other client
}
```

---

### **Phase 7: API Key Usage (Authenticated Requests)**

#### **Step 7.1: VS Code Extension Makes Request**

**Extension sends**:

```http
POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.chat_completion
Authorization: Bearer xyz789abc123def456ghi789jkl012mno345pqr678stu901vwx234
Content-Type: application/json

{
  "messages": [{"role": "user", "content": "Hello"}],
  "model": "gpt-4"
}
```

---

#### **Step 7.2: API Key Validation**

**File**: [`model_router.py`](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/oropendola_ai/services/model_router.py#L52-L111)

**Method**: `validate_api_key(api_key: str)`

**Process**:

```python
import hashlib

# 1. Check Redis cache first (performance)
cache_key = f"api_key:{api_key[:16]}"
cached_data = redis.get(cache_key)

if cached_data:
    import json
    return json.loads(cached_data)  # Cache hit!

# 2. Hash the provided API key
key_hash = hashlib.sha256(api_key.encode()).hexdigest()

# 3. Query database
api_key_docs = frappe.get_all(
    "AI API Key",
    filters={
        "key_hash": key_hash,  # Compare hashes
        "status": "Active"
    },
    fields=["name", "subscription", "user"]
)

if not api_key_docs:
    return None  # Invalid key

# 4. Get subscription
subscription = frappe.get_doc("AI Subscription", api_key_doc.subscription)

if not subscription.is_active():
    return None  # Expired subscription

# 5. Get plan details
plan = subscription.get_plan_details()

# 6. Prepare subscription data
sub_data = {
    "subscription_id": subscription.name,
    "user": subscription.user,
    "plan_id": subscription.plan,
    "priority_score": subscription.priority_score,
    "daily_quota_limit": subscription.daily_quota_limit,
    "daily_quota_remaining": subscription.daily_quota_remaining,
    "allowed_models": plan.get_allowed_models(),
    "rate_limit_qps": plan.rate_limit_qps,
    "status": subscription.status
}

# 7. Cache for performance (60 seconds)
import json
redis.setex(cache_key, 60, json.dumps(sub_data))

return sub_data
```

**Result**: Request validated! Proceed to routing.

---

#### **Step 7.3: Quota & Budget Check**

**Before processing request**:

```python
# 1. Check daily quota
if not subscription.consume_quota(units=1):
    raise Exception("Daily quota exceeded")

# 2. Estimate request cost
estimated_cost = estimate_request_cost(model, tokens)

# 3. Check monthly budget
allowed, message, remaining = subscription.check_monthly_budget(estimated_cost)

if not allowed:
    raise Exception(f"Budget exceeded: {message}")

# 4. Process request...
```

**File**: [`ai_subscription.py`](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/oropendola_ai/doctype/ai_subscription/ai_subscription.py#L107-L122)

---

#### **Step 7.4: Request Processing & Usage Tracking**

**After successful request**:

```python
# 1. Update quota
subscription.db_set("daily_quota_remaining", quota - 1)
subscription.db_set("total_requests", total + 1)

# 2. Consume monthly budget
subscription.consume_monthly_budget(actual_cost)

# 3. Log usage
usage_log = frappe.get_doc({
    "doctype": "AI Usage Log",
    "subscription": subscription.name,
    "user": subscription.user,
    "model": "gpt-4",
    "tokens_used": 150,
    "cost": 0.003,
    "timestamp": frappe.utils.now()
})
usage_log.insert(ignore_permissions=True)
```

---

## 🔄 Session Management

### **Session Lifecycle**

```mermaid
graph LR
    A[Login] --> B[Session Created]
    B --> C[Session Cookie Set]
    C --> D[User Authenticated]
    D --> E{Activity?}
    E -->|Yes| F[Session Extended]
    E -->|No| G[Session Timeout]
    F --> D
    G --> H[Logout]
    H --> I[Session Destroyed]
```

### **Session Features**

**Frappe Built-in**:
- ✅ **HTTP-only cookies** - Prevents XSS attacks
- ✅ **Secure flag** - HTTPS only
- ✅ **SameSite** - CSRF protection
- ✅ **Auto-renewal** - Activity-based
- ✅ **Multi-device** - Separate sessions per device
- ✅ **Device tracking** - IP, user agent logging

**Configuration** (`site_config.json`):
```json
{
  "session_expiry": "06:00:00",
  "session_expiry_mobile": "24:00:00",
  "force_user_to_login_again": 0
}
```

---

## 🔐 Security Features

### **1. Password Security**

- ✅ **BCrypt hashing** - Industry standard
- ✅ **Salt per user** - Rainbow table protection
- ✅ **Password strength** - Configurable rules
- ✅ **Password history** - Prevent reuse
- ✅ **Reset via email** - Built-in flow

### **2. API Key Security**

- ✅ **SHA-256 hashing** - One-way encryption
- ✅ **Never stored raw** - Hash comparison only
- ✅ **Time-limited cache** - 5 minutes
- ✅ **Prefix display** - Identification without exposure
- ✅ **Revocation** - Instant invalidation

### **3. Session Security**

- ✅ **HTTP-only cookies** - JavaScript cannot access
- ✅ **Secure flag** - HTTPS required
- ✅ **CSRF tokens** - Cross-site protection
- ✅ **IP validation** - Optional binding
- ✅ **Device fingerprinting** - Anomaly detection

### **4. Email Verification**

- ✅ **Token-based** - Unique per user
- ✅ **Time-limited** - 24-hour expiry
- ✅ **Single-use** - Cannot reuse
- ✅ **Secure transmission** - Email only

---

## 📊 Data Flow Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant B as Browser
    participant F as Frappe
    participant H as Hook
    participant S as Subscription
    participant K as API Key
    participant R as Redis

    U->>B: Navigate to /login#signup
    B->>F: Submit signup form
    F->>F: Create User (disabled)
    F->>U: Send verification email
    
    U->>B: Click verify link
    B->>F: Verify email token
    F->>F: Enable user
    F->>H: Trigger after_insert hook
    H->>S: Create AI Subscription
    S->>S: Initialize dates, quota, budget
    S->>K: Generate API Key
    K->>K: Hash key with SHA-256
    K->>R: Cache raw key (5 min)
    
    U->>B: Navigate to /login#login
    B->>F: Submit credentials
    F->>F: Validate password (BCrypt)
    F->>F: Create session
    F->>B: Set session cookie
    B->>U: Redirect to /dashboard
    
    U->>B: Request API key
    B->>F: GET /api/user_api.get_my_api_key
    F->>F: Check session
    F->>S: Get subscription
    S->>K: Get API key
    K->>R: Check cache
    R->>K: Return raw key (if available)
    K->>F: Return key data
    F->>B: Return response
    B->>U: Display API key
    
    U->>U: Copy API key
    U->>VS: Paste into VS Code
    
    VS->>F: API request with key
    F->>F: Hash provided key
    F->>K: Validate hash
    K->>S: Get subscription
    S->>S: Check quota & budget
    S->>F: Process request
    F->>S: Update usage
    S->>S: Log to AI Usage Log
    F->>VS: Return response
```

---

## 🎯 Summary: Key Takeaways

### **1. User Registration → Auto-Subscription**

✅ User signs up → Frappe creates User → Email verification → Hook triggers → Subscription auto-created → API key generated

### **2. Session-Based Authentication**

✅ Login → Session created → Cookie set → Session validates all requests → Auto-renewal on activity

### **3. API Key Management**

✅ Generated on subscription creation → Hashed (SHA-256) → Cached (5 min) → User retrieves once → Validated on each API request

### **4. Quota & Budget Tracking**

✅ Daily quota checked per request → Monthly budget tracked → Alerts sent at threshold → Auto-reset on new day/month

### **5. Security Layers**

✅ BCrypt passwords → HTTP-only cookies → CSRF protection → SHA-256 API keys → Email verification → Rate limiting

---

## 🔧 Configuration Files

- **Hooks**: [`hooks.py`](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/hooks.py)
- **User Utils**: [`user_utils.py`](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/oropendola_ai/utils/user_utils.py)
- **User API**: [`user_api.py`](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/oropendola_ai/api/user_api.py)
- **Subscription**: [`ai_subscription.py`](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/oropendola_ai/doctype/ai_subscription/ai_subscription.py)
- **Router**: [`model_router.py`](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/oropendola_ai/services/model_router.py)

---

## 📚 Related Documentation

- [Frappe User Refactoring Guide](./FRAPPE_USER_REFACTORING.md)
- [User API Quick Reference](./USER_API_QUICK_REF.md)
- [VS Code Extension API](./VSCODE_EXTENSION_API.md)
- [User-Based Budget Tracking](./USER_BASED_BUDGET_TRACKING.md)

---

**This workflow ensures**: Secure authentication, automatic provisioning, seamless API access, and comprehensive usage tracking! 🚀
