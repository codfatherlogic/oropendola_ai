# VS Code Extension API - Quick Reference

## Base URL
```
https://oropendola.ai
```

## Authentication Flow Summary

```
VS Code → Initiate Auth → Open Browser → User Logs In → Poll for Token → Store Token → Access APIs
```

## Core Endpoints

### 1. Start Authentication
```http
GET /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.initiate_auth
```
**Returns:** `auth_request_id`, `login_url`

### 2. Poll for Completion
```http
GET /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.check_auth_status?auth_request_id=XXX
```
**Returns:** `access_token`, `refresh_token` when complete

### 3. Get My Profile
```http
GET /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.get_my_profile
Authorization: Bearer <access_token>
```
**Returns:** User profile, subscription, and usage statistics

### 4. Get Subscription Status
```http
GET /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.get_subscription_status
Authorization: Bearer <access_token>
```
**Returns:** Current subscription details with quota

### 5. Check Feature Access
```http
GET /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.check_feature_access?feature=ai_completion
Authorization: Bearer <access_token>
```
**Returns:** `has_access: true/false`

### 6. Poll for Changes
```http
GET /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.poll_subscription_changes?last_check=2025-11-01T12:00:00Z
Authorization: Bearer <access_token>
```
**Returns:** `has_changes: true/false` with updated subscription

### 7. Refresh Token
```http
POST /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.refresh_token
Content-Type: application/json

{
  "refresh_token": "xxx"
}
```
**Returns:** New `access_token`

### 8. Logout
```http
POST /api/method/oropendola_ai.oropendola_ai.api.vscode_auth.logout
Authorization: Bearer <access_token>
```
**Returns:** Success message

## Subscription Status Values

| Status | Meaning | Access |
|--------|---------|--------|
| `Active` | Paid subscription active | ✅ Full access |
| `Trial` | Trial period | ✅ Full access |
| `Expired` | Subscription ended | ❌ Show renewal banner |
| `Cancelled` | User cancelled | ⏳ Access until end_date |
| `Pending` | Payment pending | ⏳ Waiting for payment |

## Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 401 | Unauthorized | Refresh token or re-auth |
| 403 | Forbidden | Subscription required |
| 429 | Rate limited | Exponential backoff |
| 500 | Server error | Retry |

## Sample VS Code Implementation

```typescript
// 1. Initiate Auth
const initResponse = await fetch('https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_auth.initiate_auth');
const { auth_request_id, login_url } = initResponse.data.message;

// 2. Open Browser
vscode.env.openExternal(vscode.Uri.parse(login_url));

// 3. Poll for Token
while (true) {
  const statusResponse = await fetch(
    `https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_auth.check_auth_status?auth_request_id=${auth_request_id}`
  );

  if (statusResponse.data.message.status === 'completed') {
    const { access_token, refresh_token } = statusResponse.data.message;
    // Store tokens securely
    await context.secrets.store('access_token', access_token);
    await context.secrets.store('refresh_token', refresh_token);
    break;
  }

  await sleep(2000); // Poll every 2 seconds
}

// 4. Check Subscription
const token = await context.secrets.get('access_token');
const subResponse = await fetch(
  'https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_auth.get_subscription_status',
  {
    headers: { 'Authorization': `Bearer ${token}` }
  }
);

const subscription = subResponse.data.message.subscription;

if (!subscription || !subscription.is_active) {
  // Show renewal banner
  vscode.window.showWarningMessage(
    'Subscription expired. Renew to continue.',
    'Renew Now'
  ).then(selection => {
    if (selection === 'Renew Now') {
      vscode.env.openExternal(vscode.Uri.parse('https://oropendola.ai/pricing'));
    }
  });
}
```

## Polling Strategy

1. **On Activation**: Check subscription immediately
2. **Every 5 Minutes**: Poll for changes
3. **On Window Focus**: Check status
4. **Manual Refresh**: User-triggered check

## Security Best Practices

1. ✅ Store tokens in VS Code SecretStorage
2. ✅ Use HTTPS for all requests
3. ✅ Clear tokens on logout
4. ❌ Never log tokens
5. ❌ Don't store in plain text

## Testing URLs

- **Documentation**: https://oropendola.ai/docs/VSCODE_API_INTEGRATION.md
- **Login Test**: https://oropendola.ai/vscode-login?auth_request=TEST
- **Pricing Page**: https://oropendola.ai/pricing

## Support

- **Email**: support@oropendola.ai
- **Docs**: https://docs.oropendola.ai
