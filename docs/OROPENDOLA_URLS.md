# 🌐 Oropendola AI URLs Reference

Quick reference for all important URLs in the Oropendola AI system.

---

## 🔐 **Authentication URLs**

### **Sign Up (New User Registration)**
```
https://oropendola.ai/login#signup
```

**Purpose**: Create a new user account  
**Method**: POST  
**Form Fields**:
- Full Name
- Email Address
- Password

**Process**:
1. User fills signup form
2. Frappe creates User account (disabled)
3. Verification email sent
4. User clicks verification link in email
5. Account activated
6. Auto-subscription created via hook
7. API key generated

---

### **Login (Existing User)**
```
https://oropendola.ai/login#login
```

**Purpose**: Sign in to existing account  
**Method**: POST  
**Form Fields**:
- Email Address
- Password

**Process**:
1. User submits credentials
2. Frappe validates BCrypt password hash
3. Session created in Redis
4. HTTP-only cookie set (`sid`)
5. CSRF token generated
6. Redirect to `/dashboard` or custom home page

---

## 📱 **User Dashboard URLs**

### **Main Dashboard**
```
https://oropendola.ai/dashboard
```

**Purpose**: User home page after login  
**Access**: Requires active session  
**Features**:
- Subscription overview
- Usage statistics
- API key management
- Account settings

---

### **API Key Management**
```
https://oropendola.ai/dashboard/api-key
```

**Purpose**: View and manage API keys  
**Access**: Requires active session  
**Actions**:
- View API key (first 5 minutes after creation)
- View API key prefix (always visible)
- Regenerate API key
- Revoke API key

---

## 🔧 **API Endpoints**

### **Base URL**
```
https://oropendola.ai/api/method/
```

---

### **User API Endpoints**

#### **Get My API Key**
```
POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.user_api.get_my_api_key
```

**Auth**: Session required (logged-in user)  
**Returns**: API key details (raw key if within 5 min cache)

---

#### **Get My Subscription**
```
POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.user_api.get_my_subscription
```

**Auth**: Session required  
**Returns**: Subscription details, quota, budget

---

#### **Regenerate API Key**
```
POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.user_api.regenerate_api_key
```

**Auth**: Session required  
**Action**: Revokes old key, creates new one  
**Returns**: New API key (5-minute cache)

---

### **VS Code Extension API Endpoints**

**Base URL**:
```
https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.
```

#### **Health Check**
```
GET https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.health_check
```

**Auth**: None  
**Returns**: Service status

---

#### **Validate API Key**
```
POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.validate_api_key
```

**Auth**: API Key in body  
**Returns**: Subscription details if valid

---

#### **Chat Completion**
```
POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.chat_completion
```

**Auth**: API Key in Authorization header  
**Body**: OpenAI-compatible format  
**Returns**: AI response

---

#### **Code Completion**
```
POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.code_completion
```

**Auth**: API Key in Authorization header  
**Returns**: Code suggestions

---

#### **Code Explanation**
```
POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.code_explanation
```

**Auth**: API Key in Authorization header  
**Returns**: Code explanation

---

#### **Code Refactor**
```
POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.code_refactor
```

**Auth**: API Key in Authorization header  
**Returns**: Refactored code

---

#### **Get Available Models**
```
GET https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.get_available_models
```

**Auth**: API Key in Authorization header  
**Returns**: List of models available to user's plan

---

#### **Get Usage Stats**
```
GET https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.get_usage_stats
```

**Auth**: API Key in Authorization header  
**Returns**: Usage statistics, quota, budget

---

## 🛠️ **Admin URLs**

### **Frappe Desk**
```
https://oropendola.ai/app
```

**Purpose**: Frappe admin interface  
**Access**: System User role required

---

### **AI Subscription Management**
```
https://oropendola.ai/app/ai-subscription
```

**Purpose**: Manage all AI subscriptions  
**Access**: System Manager role

---

### **AI Plan Configuration**
```
https://oropendola.ai/app/ai-plan
```

**Purpose**: Configure subscription plans  
**Access**: System Manager role

---

### **AI Model Profile**
```
https://oropendola.ai/app/ai-model-profile
```

**Purpose**: Configure AI model providers  
**Access**: System Manager role

---

### **AI Usage Log**
```
https://oropendola.ai/app/ai-usage-log
```

**Purpose**: View usage logs  
**Access**: System Manager role

---

## 🔑 **Email Verification URL**

### **Email Verification Link**
```
https://oropendola.ai/api/method/frappe.core.doctype.user.user.verify_email?key=<token>
```

**Purpose**: Verify user email address  
**Sent**: Automatically after signup  
**Expiry**: 24 hours  
**Action**: Activates user account, triggers auto-subscription

---

## 🔄 **Password Reset URLs**

### **Request Password Reset**
```
https://oropendola.ai/login#forgot
```

**Purpose**: Request password reset email  
**Method**: POST  
**Field**: Email address

---

### **Reset Password Link**
```
https://oropendola.ai/update-password?key=<token>
```

**Purpose**: Set new password  
**Sent**: Via email after reset request  
**Expiry**: 24 hours

---

## 📊 **Quick Reference Table**

| Action | URL | Auth Required |
|--------|-----|---------------|
| **Sign Up** | `https://oropendola.ai/login#signup` | No |
| **Login** | `https://oropendola.ai/login#login` | No |
| **Dashboard** | `https://oropendola.ai/dashboard` | Session |
| **Get API Key** | `/api/method/...user_api.get_my_api_key` | Session |
| **Regenerate Key** | `/api/method/...user_api.regenerate_api_key` | Session |
| **Chat Completion** | `/api/method/...vscode_extension.chat_completion` | API Key |
| **Validate Key** | `/api/method/...vscode_extension.validate_api_key` | API Key |
| **Usage Stats** | `/api/method/...vscode_extension.get_usage_stats` | API Key |

---

## 🎯 **URL Patterns**

### **Session-Based (Browser)**
```
https://oropendola.ai/{page}
```
- Requires HTTP-only session cookie
- CSRF token validation
- Used by: Dashboard, account management

---

### **API Key-Based (Programmatic)**
```
POST https://oropendola.ai/api/method/{module}.{function}
Authorization: Bearer <api_key>
```
- Requires valid API key in header
- Used by: VS Code extension, CLI tools, integrations

---

## 🔐 **Authentication Headers**

### **Session-Based**
```http
Cookie: sid=<session_id>
X-Frappe-CSRF-Token: <csrf_token>
```

### **API Key-Based**
```http
Authorization: Bearer <api_key>
Content-Type: application/json
```

---

## 📚 **Related Documentation**

- [User Sign-In Workflow](./USER_SIGNIN_WORKFLOW.md) - Complete authentication flow
- [User API Quick Reference](./USER_API_QUICK_REF.md) - API endpoint details
- [VS Code Extension API](./VSCODE_EXTENSION_API.md) - Extension integration
- [Authentication Flow Visual](./AUTHENTICATION_FLOW_VISUAL.md) - Visual diagrams

---

## ✅ **URL Validation**

All URLs use HTTPS (TLS 1.3) for secure transmission:
- ✅ `https://oropendola.ai/` (secure)
- ❌ `http://oropendola.ai/` (not allowed)

Session cookies are:
- ✅ HTTP-only (XSS protection)
- ✅ Secure flag (HTTPS only)
- ✅ SameSite=Lax (CSRF protection)

---

**Complete URL reference for Oropendola AI system!** 🚀
