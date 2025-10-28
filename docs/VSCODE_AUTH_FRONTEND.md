# VS Code Authentication - Frontend Implementation Guide

## Backend Status: ✅ COMPLETE

The backend API endpoints have been added to `vscode_extension.py`:
- `initiate_vscode_auth()` - Generate session token
- `check_vscode_auth_status(session_token)` - Polling endpoint
- `complete_vscode_auth(session_token, user_email, api_key, subscription)` - Mark complete

## Frontend Implementation Required

You need to create a custom web page in your Frappe site for the authentication flow.

---

## Step 1: Create Directory Structure

```bash
cd /home/frappe/frappe-bench/apps/oropendola_ai
mkdir -p oropendola_ai/www/vscode-auth
```

---

## Step 2: Create `index.html`

**File**: `oropendola_ai/www/vscode-auth/index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VS Code Authentication - Oropendola AI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .auth-container {
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 500px;
            width: 100%;
            padding: 40px;
            text-align: center;
        }

        .logo {
            width: 80px;
            height: 80px;
            margin: 0 auto 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
            color: white;
            font-weight: bold;
        }

        h1 {
            font-size: 28px;
            color: #1a1a1a;
            margin-bottom: 12px;
            font-weight: 600;
        }

        p {
            font-size: 16px;
            color: #666;
            margin-bottom: 32px;
            line-height: 1.6;
        }

        .spinner {
            width: 50px;
            height: 50px;
            margin: 20px auto;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .status {
            padding: 16px;
            border-radius: 8px;
            margin-top: 24px;
            font-size: 14px;
            font-weight: 500;
        }

        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .status.info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }

        .checkmark {
            width: 80px;
            height: 80px;
            margin: 20px auto;
            border-radius: 50%;
            background: #28a745;
            position: relative;
            animation: scaleIn 0.3s ease-in-out;
        }

        .checkmark:after {
            content: '✓';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: white;
            font-size: 48px;
            font-weight: bold;
        }

        @keyframes scaleIn {
            0% { transform: scale(0); }
            100% { transform: scale(1); }
        }

        .btn {
            display: inline-block;
            padding: 12px 32px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 500;
            font-size: 16px;
            border: none;
            cursor: pointer;
            margin-top: 20px;
            transition: transform 0.2s;
        }

        .btn:hover {
            transform: translateY(-2px);
        }

        .subscription-info {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 16px;
            margin: 24px 0;
            text-align: left;
        }

        .subscription-info h3 {
            font-size: 14px;
            color: #666;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .subscription-info .detail {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 15px;
        }

        .subscription-info .detail span:first-child {
            color: #666;
        }

        .subscription-info .detail span:last-child {
            color: #1a1a1a;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="auth-container">
        <div class="logo">O</div>
        <h1 id="title">Authenticating VS Code</h1>
        <p id="message">Please wait while we verify your account...</p>
        
        <div id="loading" class="spinner"></div>
        
        <div id="subscription-details" class="subscription-info" style="display: none;">
            <h3>Your Subscription</h3>
            <div class="detail">
                <span>Plan:</span>
                <span id="plan-name">-</span>
            </div>
            <div class="detail">
                <span>Status:</span>
                <span id="plan-status">-</span>
            </div>
            <div class="detail">
                <span>Daily Quota:</span>
                <span id="quota-info">-</span>
            </div>
        </div>
        
        <div id="status" class="status" style="display: none;"></div>
    </div>

    <script>
        // Get session token from URL
        const urlParams = new URLSearchParams(window.location.search);
        const sessionToken = urlParams.get('token');

        // Configuration
        const API_BASE = window.location.origin;

        // Main authentication flow
        async function authenticateVSCode() {
            if (!sessionToken) {
                showError('Invalid authentication link. Please try again from VS Code.');
                return;
            }

            try {
                // Check if user is logged in
                const isLoggedIn = await checkLoginStatus();
                
                if (!isLoggedIn) {
                    // Redirect to login page, then back here
                    const returnUrl = encodeURIComponent(window.location.href);
                    window.location.href = `/login?redirect-to=${returnUrl}`;
                    return;
                }

                // User is logged in - get their API key and subscription
                await completeAuthentication();

            } catch (error) {
                console.error('Authentication error:', error);
                showError(`Authentication failed: ${error.message}`);
            }
        }

        async function checkLoginStatus() {
            try {
                const response = await fetch(`${API_BASE}/api/method/frappe.auth.get_logged_user`, {
                    method: 'GET',
                    credentials: 'include'
                });

                const data = await response.json();
                return data.message && data.message !== 'Guest';
            } catch (error) {
                console.error('Login check error:', error);
                return false;
            }
        }

        async function completeAuthentication() {
            try {
                // Get user's API key
                const apiKeyResponse = await fetch(`${API_BASE}/api/method/oropendola_ai.oropendola_ai.api.user_api.get_my_api_key`, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Frappe-CSRF-Token': getCookie('csrf_token')
                    }
                });

                if (!apiKeyResponse.ok) {
                    throw new Error('Failed to retrieve API key');
                }

                const apiKeyData = await apiKeyResponse.json();
                
                if (!apiKeyData.message || !apiKeyData.message.success) {
                    throw new Error(apiKeyData.message?.error || 'No API key found. Please contact support.');
                }

                const apiKey = apiKeyData.message.api_key;
                const userEmail = apiKeyData.message.user;

                // Get subscription details
                const subResponse = await fetch(`${API_BASE}/api/method/oropendola_ai.oropendola_ai.api.user_api.get_my_subscription`, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Frappe-CSRF-Token': getCookie('csrf_token')
                    }
                });

                if (!subResponse.ok) {
                    throw new Error('Failed to retrieve subscription');
                }

                const subData = await subResponse.json();
                
                if (!subData.message || !subData.message.success) {
                    throw new Error('No active subscription found');
                }

                const subscription = subData.message.subscription;

                // Display subscription info
                displaySubscriptionInfo(subscription);

                // Complete the VS Code auth flow
                const completeResponse = await fetch(`${API_BASE}/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.complete_vscode_auth`, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Frappe-CSRF-Token': getCookie('csrf_token')
                    },
                    body: JSON.stringify({
                        session_token: sessionToken,
                        user_email: userEmail,
                        api_key: apiKey,
                        subscription: subscription
                    })
                });

                if (!completeResponse.ok) {
                    throw new Error('Failed to complete authentication');
                }

                const completeData = await completeResponse.json();

                if (completeData.message && completeData.message.success) {
                    showSuccess();
                } else {
                    throw new Error(completeData.message?.error || 'Authentication failed');
                }

            } catch (error) {
                console.error('Complete auth error:', error);
                throw error;
            }
        }

        function displaySubscriptionInfo(subscription) {
            const subscriptionDiv = document.getElementById('subscription-details');
            document.getElementById('plan-name').textContent = subscription.plan_name || 'Free';
            document.getElementById('plan-status').textContent = subscription.status || 'Active';
            
            const quota = subscription.daily_quota_limit === -1 
                ? 'Unlimited' 
                : `${subscription.daily_quota_remaining || 0} / ${subscription.daily_quota_limit || 0}`;
            document.getElementById('quota-info').textContent = quota;
            
            subscriptionDiv.style.display = 'block';
        }

        function showSuccess() {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('title').textContent = 'Authentication Successful!';
            document.getElementById('message').textContent = 'You can now return to VS Code. The extension will automatically detect the authentication.';
            
            const container = document.querySelector('.auth-container');
            const checkmark = document.createElement('div');
            checkmark.className = 'checkmark';
            container.insertBefore(checkmark, document.getElementById('subscription-details'));
            
            const statusDiv = document.getElementById('status');
            statusDiv.className = 'status success';
            statusDiv.textContent = '✓ Your VS Code extension is now authenticated and ready to use!';
            statusDiv.style.display = 'block';

            // Auto-close after 5 seconds
            setTimeout(() => {
                window.close();
            }, 5000);
        }

        function showError(message) {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('title').textContent = 'Authentication Failed';
            document.getElementById('message').textContent = message;
            
            const statusDiv = document.getElementById('status');
            statusDiv.className = 'status error';
            statusDiv.innerHTML = `<strong>Error:</strong> ${message}<br><br><a href="/login" class="btn">Try Again</a>`;
            statusDiv.style.display = 'block';
        }

        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return '';
        }

        // Start authentication on page load
        authenticateVSCode();
    </script>
</body>
</html>
```

---

## Step 3: Create `index.py`

**File**: `oropendola_ai/www/vscode-auth/index.py`

```python
# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

import frappe

def get_context(context):
	"""
	Context for VS Code authentication page
	"""
	context.no_cache = 1
	context.show_sidebar = False
	
	# Get session token from query params
	session_token = frappe.form_dict.get('token')
	
	if not session_token:
		frappe.throw("Invalid authentication request")
	
	context.session_token = session_token
	context.title = "VS Code Authentication"
	
	return context
```

---

## Step 4: Deployment Instructions

### 1. Copy Files to Your Frappe App

```bash
# Navigate to your app directory
cd /home/frappe/frappe-bench/apps/oropendola_ai

# Create the directory
mkdir -p oropendola_ai/www/vscode-auth

# Create index.html (copy the HTML content above)
nano oropendola_ai/www/vscode-auth/index.html

# Create index.py (copy the Python content above)
nano oropendola_ai/www/vscode-auth/index.py
```

### 2. Clear Cache and Restart

```bash
cd /home/frappe/frappe-bench

# Clear cache
bench --site oropendola.ai clear-cache

# Restart bench
bench restart
```

### 3. Test the Authentication Flow

**Method 1: Manual Test**
```bash
# In VS Code extension, call:
POST /api/method/oropendola_ai.oropendola_ai.api.vscode_extension.initiate_vscode_auth

# Response:
{
  "message": {
    "success": true,
    "auth_url": "https://oropendola.ai/vscode-auth?token=XXXXX",
    "session_token": "XXXXX",
    "expires_in": 600
  }
}

# Open the auth_url in browser
# User logs in (if not already logged in)
# Page displays subscription info
# Page calls complete_vscode_auth()

# VS Code polls:
POST /api/method/oropendola_ai.oropendola_ai.api.vscode_extension.check_vscode_auth_status
{
  "session_token": "XXXXX"
}

# Response when complete:
{
  "message": {
    "success": true,
    "status": "complete",
    "api_key": "oro_XXXXXXXX",
    "user_email": "user@example.com",
    "subscription": { ... }
  }
}
```

---

## Step 5: VS Code Extension Integration

Your VS Code extension needs to implement the authentication flow. Here's the TypeScript code:

**File**: `src/auth.ts` (in your VS Code extension)

```typescript
import * as vscode from 'vscode';
import fetch from 'node-fetch';

const API_BASE = 'https://oropendola.ai';
const POLL_INTERVAL = 5000; // 5 seconds
const POLL_TIMEOUT = 600000; // 10 minutes

export async function authenticateVSCode(context: vscode.ExtensionContext): Promise<string | null> {
    try {
        // Step 1: Initiate auth flow
        const initResponse = await fetch(
            `${API_BASE}/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.initiate_vscode_auth`,
            { method: 'POST' }
        );

        const initData = await initResponse.json();
        
        if (!initData.message?.success) {
            vscode.window.showErrorMessage('Failed to initiate authentication');
            return null;
        }

        const { auth_url, session_token } = initData.message;

        // Step 2: Open browser for user to authenticate
        vscode.window.showInformationMessage(
            'Opening browser for authentication...',
            'Open Browser'
        ).then(selection => {
            if (selection === 'Open Browser') {
                vscode.env.openExternal(vscode.Uri.parse(auth_url));
            }
        });

        // Step 3: Poll for authentication completion
        const apiKey = await pollAuthStatus(session_token);

        if (apiKey) {
            // Store API key securely
            await context.secrets.store('oropendola_api_key', apiKey);
            vscode.window.showInformationMessage('✓ Successfully authenticated with Oropendola AI!');
            return apiKey;
        } else {
            vscode.window.showErrorMessage('Authentication timed out or was cancelled');
            return null;
        }

    } catch (error) {
        console.error('Authentication error:', error);
        vscode.window.showErrorMessage(`Authentication failed: ${error.message}`);
        return null;
    }
}

async function pollAuthStatus(sessionToken: string): Promise<string | null> {
    const startTime = Date.now();

    return new Promise((resolve) => {
        const pollInterval = setInterval(async () => {
            try {
                // Check if timeout exceeded
                if (Date.now() - startTime > POLL_TIMEOUT) {
                    clearInterval(pollInterval);
                    resolve(null);
                    return;
                }

                // Poll the status endpoint
                const response = await fetch(
                    `${API_BASE}/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.check_vscode_auth_status`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ session_token: sessionToken })
                    }
                );

                const data = await response.json();

                if (data.message?.status === 'complete') {
                    clearInterval(pollInterval);
                    resolve(data.message.api_key);
                } else if (data.message?.status === 'expired') {
                    clearInterval(pollInterval);
                    resolve(null);
                }
                // Otherwise keep polling (status is 'pending')

            } catch (error) {
                console.error('Poll error:', error);
                // Continue polling despite errors
            }
        }, POLL_INTERVAL);
    });
}

export async function getStoredApiKey(context: vscode.ExtensionContext): Promise<string | null> {
    return await context.secrets.get('oropendola_api_key') || null;
}

export async function clearApiKey(context: vscode.ExtensionContext): Promise<void> {
    await context.secrets.delete('oropendola_api_key');
}
```

**Usage in Extension**:

```typescript
// extension.ts
import { authenticateVSCode, getStoredApiKey } from './auth';

export async function activate(context: vscode.ExtensionContext) {
    // Check for existing API key
    let apiKey = await getStoredApiKey(context);

    // Register authenticate command
    let authenticateCmd = vscode.commands.registerCommand(
        'oropendola.authenticate',
        async () => {
            apiKey = await authenticateVSCode(context);
        }
    );

    context.subscriptions.push(authenticateCmd);

    // Auto-authenticate if no API key found
    if (!apiKey) {
        vscode.window.showInformationMessage(
            'Oropendola AI: Please authenticate to use the extension',
            'Authenticate'
        ).then(selection => {
            if (selection === 'Authenticate') {
                vscode.commands.executeCommand('oropendola.authenticate');
            }
        });
    }
}
```

---

## Step 6: Testing Checklist

- [ ] Backend endpoints accessible (test with curl/Postman)
- [ ] `/vscode-auth` page loads correctly
- [ ] User not logged in → redirects to `/login`
- [ ] After login → redirects back to `/vscode-auth`
- [ ] Page displays subscription information
- [ ] VS Code polling receives API key
- [ ] API key stored in VS Code secrets
- [ ] Auto-close after 5 seconds works

---

## Security Notes

1. **Session Tokens**: Expire in 10 minutes, stored in Redis cache
2. **CSRF Protection**: All authenticated endpoints require CSRF token
3. **API Key Security**: Never logged or displayed after initial creation
4. **Secure Storage**: VS Code uses secret storage API (encrypted)
5. **HTTPS Only**: Always use HTTPS in production

---

## Troubleshooting

### Page Not Found
```bash
# Check if www directory exists
ls -la oropendola_ai/www/vscode-auth/

# Clear cache and rebuild
bench --site oropendola.ai clear-cache
bench build
bench restart
```

### Authentication Fails
```bash
# Check error logs
bench --site oropendola.ai console

# Check cache
frappe.cache().get_value('vscode_auth:TOKEN')
```

### API Key Not Found
- Ensure user has a subscription (auto-created on signup)
- Check if API key exists in AI API Key doctype
- Verify user field is correctly set

---

## Summary

✅ **Backend**: 3 API endpoints added to `vscode_extension.py`
📄 **Frontend**: HTML page + Python context handler
🔌 **VS Code**: TypeScript authentication flow
🔒 **Security**: Session tokens, CSRF protection, secure storage

The authentication flow is now complete end-to-end!
