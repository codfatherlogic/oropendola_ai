# VS Code Extension API Integration Guide

**Version:** 1.0
**Last Updated:** November 1, 2025
**Base URL:** `https://oropendola.ai`

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication Flow](#authentication-flow)
3. [API Endpoints](#api-endpoints)
4. [Subscription Validation](#subscription-validation)
5. [Renewal Detection](#renewal-detection)
6. [Error Handling](#error-handling)
7. [Security Considerations](#security-considerations)
8. [Sample Implementation](#sample-implementation)

---

## Overview

This document describes the complete API integration for the Oropendola AI VS Code extension, including:

- **OAuth-like authentication flow** for secure login
- **Token-based session management** for API calls
- **Real-time subscription status validation**
- **Automatic renewal detection**

### Key Features

- ✅ Secure token exchange between VS Code and website
- ✅ Automatic subscription status polling
- ✅ Graceful handling of expired subscriptions
- ✅ Seamless renewal flow
- ✅ Session persistence across VS Code restarts

---

## Authentication Flow

### Flow Diagram

```
┌─────────────┐                    ┌──────────────┐                   ┌─────────────┐
│  VS Code    │                    │   Website    │                   │   Backend   │
│  Extension  │                    │  (Browser)   │                   │   API       │
└──────┬──────┘                    └──────┬───────┘                   └──────┬──────┘
       │                                  │                                  │
       │ 1. Initiate Login                │                                  │
       │ GET /api/method/...              │                                  │
       │  /vscode/auth/initiate           │                                  │
       │─────────────────────────────────>│                                  │
       │                                  │                                  │
       │ 2. Return auth_request_id        │                                  │
       │    + login_url                   │                                  │
       │<─────────────────────────────────│                                  │
       │                                  │                                  │
       │ 3. Open browser with login_url   │                                  │
       │─────────────────────────────────>│                                  │
       │                                  │                                  │
       │                                  │ 4. User logs in                  │
       │                                  │─────────────────────────────────>│
       │                                  │                                  │
       │                                  │ 5. Session created               │
       │                                  │<─────────────────────────────────│
       │                                  │                                  │
       │                                  │ 6. Redirect to callback          │
       │                                  │    with auth_code                │
       │                                  │─────────────────────────────────>│
       │                                  │                                  │
       │                                  │ 7. Mark auth_request as complete │
       │                                  │<─────────────────────────────────│
       │                                  │                                  │
       │                                  │ 8. Show success page             │
       │                                  │    (user can close browser)      │
       │                                  │                                  │
       │ 9. Poll for completion           │                                  │
       │    GET /vscode/auth/status       │                                  │
       │─────────────────────────────────────────────────────────────────────>│
       │                                  │                                  │
       │ 10. Return access_token          │                                  │
       │     + user info                  │                                  │
       │<─────────────────────────────────────────────────────────────────────│
       │                                  │                                  │
       │ 11. Store token & fetch          │                                  │
       │     subscription status          │                                  │
       │                                  │                                  │
```

### Step-by-Step Process

#### Step 1: Initiate Authentication

**VS Code Extension → Backend**

The extension initiates the login process by requesting an auth session.

```http
GET /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.initiate_auth
```

**Response:**
```json
{
  "message": {
    "success": true,
    "auth_request_id": "AUTH-REQ-2025-00123",
    "login_url": "https://oropendola.ai/vscode-login?auth_request=AUTH-REQ-2025-00123",
    "expires_in": 300,
    "poll_interval": 2
  }
}
```

#### Step 2: Open Browser

The extension opens the `login_url` in the user's default browser.

#### Step 3: User Logs In

User completes login on the website using email/password or OTP.

#### Step 4: Callback & Token Generation

After successful login, the website redirects to:

```
/api/method/oropendola_ai.oropendola_ai.api.vscode_auth.complete_auth?auth_request_id=AUTH-REQ-2025-00123
```

Backend generates an access token and marks the auth request as complete.

#### Step 5: Poll for Completion

VS Code extension polls for auth completion:

```http
GET /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.check_auth_status?auth_request_id=AUTH-REQ-2025-00123
```

**Response (Pending):**
```json
{
  "message": {
    "success": true,
    "status": "pending",
    "message": "Waiting for user to complete login"
  }
}
```

**Response (Completed):**
```json
{
  "message": {
    "success": true,
    "status": "completed",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 2592000,
    "user": {
      "email": "user@example.com",
      "full_name": "John Doe",
      "user_image": "/files/user_image.jpg"
    }
  }
}
```

---

## API Endpoints

### 1. Authentication Endpoints

#### 1.1 Initiate Authentication

**Endpoint:** `GET /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.initiate_auth`

**Description:** Initiates VS Code authentication flow

**Authentication:** None required

**Request:**
```http
GET /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.initiate_auth
```

**Response:**
```json
{
  "message": {
    "success": true,
    "auth_request_id": "AUTH-REQ-2025-00123",
    "login_url": "https://oropendola.ai/vscode-login?auth_request=AUTH-REQ-2025-00123",
    "expires_in": 300,
    "poll_interval": 2
  }
}
```

**Fields:**
- `auth_request_id`: Unique identifier for this auth request
- `login_url`: URL to open in browser for user login
- `expires_in`: Seconds until auth request expires (5 minutes)
- `poll_interval`: Recommended polling interval in seconds

---

#### 1.2 Check Authentication Status

**Endpoint:** `GET /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.check_auth_status`

**Description:** Poll to check if user has completed login

**Authentication:** None required

**Request:**
```http
GET /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.check_auth_status?auth_request_id=AUTH-REQ-2025-00123
```

**Response (Pending):**
```json
{
  "message": {
    "success": true,
    "status": "pending",
    "message": "Waiting for user to complete login"
  }
}
```

**Response (Completed):**
```json
{
  "message": {
    "success": true,
    "status": "completed",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 2592000,
    "user": {
      "email": "user@example.com",
      "full_name": "John Doe",
      "user_image": "/files/user_image.jpg"
    }
  }
}
```

**Response (Expired):**
```json
{
  "message": {
    "success": false,
    "status": "expired",
    "error": "Authentication request expired. Please try again."
  }
}
```

---

#### 1.3 Refresh Access Token

**Endpoint:** `POST /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.refresh_token`

**Description:** Refresh an expired access token using refresh token

**Authentication:** None required (uses refresh_token)

**Request:**
```http
POST /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.refresh_token
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "message": {
    "success": true,
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 2592000
  }
}
```

---

#### 1.4 Logout

**Endpoint:** `POST /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.logout`

**Description:** Revoke access and refresh tokens

**Authentication:** Bearer token required

**Request:**
```http
POST /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "message": {
    "success": true,
    "message": "Successfully logged out"
  }
}
```

---

### 2. Subscription Status Endpoints

#### 2.1 Get Subscription Status

**Endpoint:** `GET /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.get_subscription_status`

**Description:** Get current user's subscription status

**Authentication:** Bearer token required

**Request:**
```http
GET /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.get_subscription_status
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (Active Subscription):**
```json
{
  "message": {
    "success": true,
    "subscription": {
      "id": "SUB-2025-00123",
      "status": "Active",
      "plan_name": "Pro Plan",
      "plan_type": "7-days",
      "start_date": "2025-11-01 12:30:00",
      "end_date": "2025-11-08 12:30:00",
      "is_active": true,
      "is_trial": false,
      "days_remaining": 7,
      "auto_renew": true,
      "quota": {
        "daily_limit": 300,
        "daily_remaining": 250,
        "usage_percent": 16.67
      }
    }
  }
}
```

**Response (Expired Subscription):**
```json
{
  "message": {
    "success": true,
    "subscription": {
      "id": "SUB-2025-00120",
      "status": "Expired",
      "plan_name": "Pro Plan",
      "plan_type": "7-days",
      "start_date": "2025-10-20 12:30:00",
      "end_date": "2025-10-27 12:30:00",
      "is_active": false,
      "is_trial": false,
      "days_remaining": 0,
      "auto_renew": false,
      "expired_days_ago": 5
    }
  }
}
```

**Response (No Subscription):**
```json
{
  "message": {
    "success": true,
    "subscription": null,
    "message": "No active subscription found"
  }
}
```

---

#### 2.2 Check Feature Access

**Endpoint:** `GET /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.check_feature_access`

**Description:** Check if user can access specific features

**Authentication:** Bearer token required

**Request:**
```http
GET /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.check_feature_access?feature=ai_completion
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Query Parameters:**
- `feature`: Feature name (e.g., `ai_completion`, `chat`, `code_review`)

**Response:**
```json
{
  "message": {
    "success": true,
    "has_access": true,
    "subscription_status": "Active",
    "quota_remaining": 250,
    "message": "Access granted"
  }
}
```

**Response (No Access):**
```json
{
  "message": {
    "success": true,
    "has_access": false,
    "subscription_status": "Expired",
    "message": "Subscription expired. Please renew to continue.",
    "renewal_url": "https://oropendola.ai/pricing"
  }
}
```

---

### 3. Renewal Detection Endpoints

#### 3.1 Subscribe to Renewal Events (Webhook)

**Endpoint:** `POST /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.register_webhook`

**Description:** Register a webhook URL for subscription change notifications

**Authentication:** Bearer token required

**Request:**
```http
POST /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.register_webhook
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "webhook_url": "http://localhost:54321/subscription-webhook",
  "events": ["subscription.renewed", "subscription.expired", "subscription.cancelled"]
}
```

**Response:**
```json
{
  "message": {
    "success": true,
    "webhook_id": "WEBHOOK-2025-00001",
    "message": "Webhook registered successfully"
  }
}
```

**Webhook Payload (when subscription changes):**
```json
{
  "event": "subscription.renewed",
  "timestamp": "2025-11-01T12:30:00Z",
  "user_email": "user@example.com",
  "subscription": {
    "id": "SUB-2025-00123",
    "status": "Active",
    "plan_name": "Pro Plan",
    "end_date": "2025-11-15 12:30:00"
  }
}
```

---

#### 3.2 Poll for Subscription Changes

**Endpoint:** `GET /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.poll_subscription_changes`

**Description:** Poll for subscription changes since last check

**Authentication:** Bearer token required

**Request:**
```http
GET /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.poll_subscription_changes?last_check=2025-11-01T12:00:00Z
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Query Parameters:**
- `last_check`: ISO 8601 timestamp of last check

**Response (No Changes):**
```json
{
  "message": {
    "success": true,
    "has_changes": false,
    "current_status": "Active"
  }
}
```

**Response (Subscription Renewed):**
```json
{
  "message": {
    "success": true,
    "has_changes": true,
    "change_type": "renewed",
    "subscription": {
      "id": "SUB-2025-00123",
      "status": "Active",
      "plan_name": "Pro Plan",
      "end_date": "2025-11-15 12:30:00"
    }
  }
}
```

---

## Subscription Validation

### Subscription Status Values

| Status | Description | VS Code Behavior |
|--------|-------------|------------------|
| `Active` | Valid paid subscription | Full access granted |
| `Trial` | Trial period active | Full access granted, show trial badge |
| `Expired` | Subscription ended | Show renewal banner, limited/no access |
| `Cancelled` | User cancelled, pending expiry | Show until end_date, then show renewal banner |
| `Pending` | Payment initiated but not completed | Show "Payment Pending" message |

### Validation Logic

```javascript
function canAccessFeature(subscription) {
  if (!subscription) {
    return {
      hasAccess: false,
      reason: "no_subscription",
      action: "subscribe"
    };
  }

  const now = new Date();
  const endDate = new Date(subscription.end_date);

  if (subscription.status === "Active" || subscription.status === "Trial") {
    if (endDate > now) {
      return {
        hasAccess: true,
        expiresIn: Math.ceil((endDate - now) / (1000 * 60 * 60 * 24))
      };
    }
  }

  return {
    hasAccess: false,
    reason: "expired",
    action: "renew",
    expiredDaysAgo: Math.ceil((now - endDate) / (1000 * 60 * 60 * 24))
  };
}
```

---

## Renewal Detection

### Polling Strategy

VS Code extension should poll for subscription changes:

1. **On Extension Activation**: Check subscription status immediately
2. **Regular Polling**: Every 5 minutes during active use
3. **After Focus**: When VS Code window regains focus
4. **Manual Refresh**: When user clicks "Check Subscription" button

### Sample Polling Implementation

```javascript
class SubscriptionManager {
  constructor(accessToken) {
    this.accessToken = accessToken;
    this.lastCheck = null;
    this.pollInterval = 5 * 60 * 1000; // 5 minutes
  }

  async startPolling() {
    // Initial check
    await this.checkSubscription();

    // Poll every 5 minutes
    setInterval(async () => {
      await this.pollChanges();
    }, this.pollInterval);

    // Check on window focus
    window.addEventListener('focus', async () => {
      await this.pollChanges();
    });
  }

  async checkSubscription() {
    const response = await fetch(
      'https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_auth.get_subscription_status',
      {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`
        }
      }
    );

    const data = await response.json();
    this.updateUI(data.message.subscription);
    this.lastCheck = new Date().toISOString();
  }

  async pollChanges() {
    if (!this.lastCheck) {
      return await this.checkSubscription();
    }

    const response = await fetch(
      `https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_auth.poll_subscription_changes?last_check=${this.lastCheck}`,
      {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`
        }
      }
    );

    const data = await response.json();

    if (data.message.has_changes) {
      this.updateUI(data.message.subscription);
      this.showNotification(`Subscription ${data.message.change_type}`);
    }

    this.lastCheck = new Date().toISOString();
  }

  updateUI(subscription) {
    // Update status bar, banners, etc.
  }

  showNotification(message) {
    // Show VS Code notification
  }
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 401 | Unauthorized | Refresh token or re-authenticate |
| 403 | Forbidden | Subscription required/expired |
| 404 | Not Found | Resource doesn't exist |
| 429 | Rate Limited | Wait and retry with exponential backoff |
| 500 | Server Error | Retry with exponential backoff |

### Error Response Format

```json
{
  "message": {
    "success": false,
    "error": "Error message",
    "error_code": "SUBSCRIPTION_EXPIRED",
    "details": {
      "expired_date": "2025-10-27 12:30:00",
      "renewal_url": "https://oropendola.ai/pricing"
    }
  }
}
```

### Common Error Codes

| Error Code | Description | Recommended Action |
|------------|-------------|-------------------|
| `INVALID_TOKEN` | Access token is invalid | Refresh token or re-authenticate |
| `TOKEN_EXPIRED` | Access token expired | Use refresh token |
| `REFRESH_TOKEN_EXPIRED` | Refresh token expired | Re-authenticate |
| `SUBSCRIPTION_EXPIRED` | Subscription ended | Show renewal banner |
| `NO_SUBSCRIPTION` | User never subscribed | Prompt to subscribe |
| `QUOTA_EXCEEDED` | Daily quota exhausted | Show quota exceeded message |
| `AUTH_REQUEST_EXPIRED` | Auth request timeout (5 min) | Initiate new auth request |

---

## Security Considerations

### Token Storage

**DO:**
- ✅ Store tokens in VS Code SecretStorage API
- ✅ Use HTTPS for all API calls
- ✅ Validate token expiry before each request
- ✅ Clear tokens on logout

**DON'T:**
- ❌ Store tokens in plain text files
- ❌ Log tokens to console or files
- ❌ Store tokens in VS Code settings (user-visible)

### Token Lifecycle

```javascript
// Store token securely
await context.secrets.store('oropendola_access_token', accessToken);
await context.secrets.store('oropendola_refresh_token', refreshToken);

// Retrieve token
const accessToken = await context.secrets.get('oropendola_access_token');

// Clear on logout
await context.secrets.delete('oropendola_access_token');
await context.secrets.delete('oropendola_refresh_token');
```

### API Request Headers

Always include these headers:

```http
Authorization: Bearer <access_token>
User-Agent: Oropendola-VSCode/1.0.0
Content-Type: application/json
```

---

## Sample Implementation

### Complete VS Code Extension Flow

```typescript
import * as vscode from 'vscode';
import axios from 'axios';

const BASE_URL = 'https://oropendola.ai';

class OropendolaAuthProvider {
  private context: vscode.ExtensionContext;
  private statusBarItem: vscode.StatusBarItem;

  constructor(context: vscode.ExtensionContext) {
    this.context = context;
    this.statusBarItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Right,
      100
    );
  }

  async login(): Promise<boolean> {
    try {
      // Step 1: Initiate auth
      const initResponse = await axios.get(
        `${BASE_URL}/api/method/oropendola_ai.oropendola_ai.api.vscode_auth.initiate_auth`
      );

      const { auth_request_id, login_url, poll_interval } = initResponse.data.message;

      // Step 2: Open browser
      vscode.env.openExternal(vscode.Uri.parse(login_url));

      // Step 3: Show progress
      return await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: 'Waiting for login...',
          cancellable: true
        },
        async (progress, token) => {
          return await this.pollForCompletion(auth_request_id, poll_interval, token);
        }
      );
    } catch (error) {
      vscode.window.showErrorMessage(`Login failed: ${error.message}`);
      return false;
    }
  }

  private async pollForCompletion(
    authRequestId: string,
    pollInterval: number,
    cancellationToken: vscode.CancellationToken
  ): Promise<boolean> {
    const maxAttempts = 150; // 5 minutes with 2s interval
    let attempts = 0;

    while (attempts < maxAttempts && !cancellationToken.isCancellationRequested) {
      try {
        const statusResponse = await axios.get(
          `${BASE_URL}/api/method/oropendola_ai.oropendola_ai.api.vscode_auth.check_auth_status`,
          {
            params: { auth_request_id: authRequestId }
          }
        );

        const result = statusResponse.data.message;

        if (result.status === 'completed') {
          // Store tokens
          await this.context.secrets.store('access_token', result.access_token);
          await this.context.secrets.store('refresh_token', result.refresh_token);

          vscode.window.showInformationMessage(
            `Welcome, ${result.user.full_name}!`
          );

          // Check subscription
          await this.checkSubscription();
          return true;
        }

        if (result.status === 'expired') {
          vscode.window.showErrorMessage('Login expired. Please try again.');
          return false;
        }

        // Wait before next poll
        await new Promise(resolve => setTimeout(resolve, pollInterval * 1000));
        attempts++;

      } catch (error) {
        console.error('Polling error:', error);
        await new Promise(resolve => setTimeout(resolve, pollInterval * 1000));
        attempts++;
      }
    }

    vscode.window.showWarningMessage('Login timeout. Please try again.');
    return false;
  }

  async checkSubscription(): Promise<void> {
    try {
      const accessToken = await this.context.secrets.get('access_token');

      if (!accessToken) {
        this.showSubscriptionBanner('not_logged_in');
        return;
      }

      const response = await axios.get(
        `${BASE_URL}/api/method/oropendola_ai.oropendola_ai.api.vscode_auth.get_subscription_status`,
        {
          headers: { Authorization: `Bearer ${accessToken}` }
        }
      );

      const subscription = response.data.message.subscription;

      if (!subscription) {
        this.showSubscriptionBanner('no_subscription');
      } else if (subscription.status === 'Expired') {
        this.showSubscriptionBanner('expired', subscription);
      } else if (subscription.status === 'Active' || subscription.status === 'Trial') {
        this.updateStatusBar(subscription);
      }

    } catch (error) {
      if (error.response?.status === 401) {
        await this.refreshToken();
      } else {
        console.error('Subscription check error:', error);
      }
    }
  }

  private showSubscriptionBanner(type: string, subscription?: any): void {
    let message: string;
    let action: string;

    switch (type) {
      case 'not_logged_in':
        message = 'Please sign in to use Oropendola AI';
        action = 'Sign In';
        break;
      case 'no_subscription':
        message = 'No active subscription. Subscribe to use Oropendola AI';
        action = 'Subscribe Now';
        break;
      case 'expired':
        message = `Your subscription expired on ${subscription.end_date}. Renew to continue.`;
        action = 'Renew Now';
        break;
      default:
        return;
    }

    vscode.window.showWarningMessage(message, action).then(selection => {
      if (selection === action) {
        if (type === 'not_logged_in') {
          this.login();
        } else {
          vscode.env.openExternal(vscode.Uri.parse(`${BASE_URL}/pricing`));
        }
      }
    });
  }

  private updateStatusBar(subscription: any): void {
    this.statusBarItem.text = `$(check) ${subscription.plan_name}`;
    this.statusBarItem.tooltip = `Active until ${subscription.end_date}\n${subscription.quota.daily_remaining}/${subscription.quota.daily_limit} requests remaining`;
    this.statusBarItem.show();
  }

  async refreshToken(): Promise<boolean> {
    try {
      const refreshToken = await this.context.secrets.get('refresh_token');

      if (!refreshToken) {
        return false;
      }

      const response = await axios.post(
        `${BASE_URL}/api/method/oropendola_ai.oropendola_ai.api.vscode_auth.refresh_token`,
        { refresh_token: refreshToken }
      );

      const { access_token } = response.data.message;
      await this.context.secrets.store('access_token', access_token);

      return true;
    } catch (error) {
      // Refresh token expired, need to re-authenticate
      await this.logout();
      return false;
    }
  }

  async logout(): Promise<void> {
    await this.context.secrets.delete('access_token');
    await this.context.secrets.delete('refresh_token');
    this.statusBarItem.hide();
    vscode.window.showInformationMessage('Logged out successfully');
  }
}

export function activate(context: vscode.ExtensionContext) {
  const authProvider = new OropendolaAuthProvider(context);

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand('oropendola.login', () => authProvider.login())
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('oropendola.logout', () => authProvider.logout())
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('oropendola.checkSubscription', () => authProvider.checkSubscription())
  );

  // Check subscription on activation
  authProvider.checkSubscription();

  // Poll for changes every 5 minutes
  setInterval(() => authProvider.checkSubscription(), 5 * 60 * 1000);
}
```

---

## Testing Checklist

### Authentication Flow
- [ ] Initiate auth creates valid auth_request_id
- [ ] Login URL opens in browser correctly
- [ ] Polling completes successfully after login
- [ ] Tokens are stored securely
- [ ] Expired auth requests return proper error
- [ ] Refresh token works correctly
- [ ] Logout clears all tokens

### Subscription Validation
- [ ] Active subscription grants access
- [ ] Expired subscription shows renewal banner
- [ ] No subscription prompts to subscribe
- [ ] Quota limits are enforced
- [ ] Trial subscriptions display trial badge

### Renewal Detection
- [ ] Polling detects subscription renewal
- [ ] Banner disappears after renewal
- [ ] Status bar updates correctly
- [ ] Notification shown on renewal

### Error Handling
- [ ] 401 errors trigger token refresh
- [ ] Network errors handled gracefully
- [ ] Rate limiting respected
- [ ] Invalid tokens cleared properly

---

## API Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| Authentication | 10 requests | 1 minute |
| Subscription Status | 60 requests | 1 minute |
| Poll Changes | 120 requests | 1 minute |
| All Others | 100 requests | 1 minute |

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1698765432
```

---

## Support & Resources

- **API Base URL:** https://oropendola.ai
- **Documentation:** https://docs.oropendola.ai/vscode-integration
- **Support Email:** support@oropendola.ai
- **GitHub Issues:** https://github.com/oropendola/vscode-extension/issues

---

## Changelog

### Version 1.0 (November 1, 2025)
- Initial API documentation
- OAuth-like authentication flow
- Subscription validation endpoints
- Renewal detection mechanism
- Complete sample implementation

---

**End of Document**
