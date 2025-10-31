# Account Reactivation Guide

## Overview

When a user deletes their account, the system anonymizes their data but keeps the email for audit purposes. If the same user tries to sign up again months later, they need a way to reactivate their old account.

## How It Works

### 1. Account States

- **Active Account**: `enabled = 1`, normal user data
- **Deleted Account**: `enabled = 0`, `full_name = "Deleted User"`, `bio = "Account deleted"`
- **Disabled Account**: `enabled = 0`, but NOT deleted (requires admin support)

### 2. Signup Flow Integration

#### Step 1: Check Email During Signup

When a user enters their email during signup, call the check endpoint:

```javascript
// Example signup form handling
async function handleSignup(email, fullName, password) {
    // First, check if email exists and account status
    const checkResponse = await fetch('/api/method/oropendola_ai.api.account_deletion.check_and_reactivate_account', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            email: email
        })
    });

    const result = await checkResponse.json();
    const data = result.message;

    // Handle different scenarios
    if (data.can_signup) {
        // Email is available - proceed with normal signup
        proceedWithNormalSignup(email, fullName, password);
    }
    else if (data.can_reactivate) {
        // Account was deleted - offer reactivation
        showReactivationOption(email, fullName, password);
    }
    else if (data.is_active) {
        // Account exists and is active
        showError('This email is already registered. Please login instead.');
    }
    else if (data.is_disabled) {
        // Account is disabled but not deleted
        showError('This account is disabled. Please contact support.');
    }
}
```

#### Step 2: Show Reactivation Dialog

If `can_reactivate` is true, show a modal explaining the situation:

```javascript
function showReactivationOption(email, fullName, password) {
    const confirmed = confirm(
        'Welcome Back!\n\n' +
        'We found that you previously had an account with this email that was deleted.\n\n' +
        'Would you like to reactivate your account?\n\n' +
        '✓ You\'ll get a fresh start with a new trial period\n' +
        '✓ Your previous data was removed for privacy\n' +
        '✓ You can set a new password\n\n' +
        'Click OK to reactivate or Cancel to use a different email.'
    );

    if (confirmed) {
        reactivateAccount(email, fullName, password);
    }
}
```

#### Step 3: Call Reactivation API

```javascript
async function reactivateAccount(email, fullName, password) {
    try {
        const response = await fetch('/api/method/oropendola_ai.api.account_deletion.reactivate_deleted_account', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                full_name: fullName,
                password: password
            })
        });

        const result = await response.json();
        const data = result.message;

        if (data.success) {
            // Show success message
            alert(data.message);
            // Redirect to login
            window.location.href = '/login?email=' + encodeURIComponent(email);
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        console.error('Reactivation error:', error);
        alert('Failed to reactivate account. Please contact support.');
    }
}
```

## API Endpoints

### 1. Check Account Status

**Endpoint**: `/api/method/oropendola_ai.api.account_deletion.check_and_reactivate_account`

**Method**: POST

**Parameters**:
- `email` (required): User's email address

**Response Examples**:

```json
// Email available for signup
{
    "message": {
        "success": true,
        "account_exists": false,
        "can_signup": true,
        "message": "Email available for signup"
    }
}

// Deleted account - can reactivate
{
    "message": {
        "success": true,
        "account_exists": true,
        "is_deleted": true,
        "can_reactivate": true,
        "message": "This email was previously registered but the account was deleted. You can reactivate it.",
        "email": "user@example.com"
    }
}

// Active account exists
{
    "message": {
        "success": true,
        "account_exists": true,
        "is_active": true,
        "can_signup": false,
        "message": "This email is already registered. Please login instead."
    }
}

// Disabled account (not deleted)
{
    "message": {
        "success": true,
        "account_exists": true,
        "is_disabled": true,
        "can_reactivate": false,
        "message": "This account is disabled. Please contact support for assistance."
    }
}
```

### 2. Reactivate Deleted Account

**Endpoint**: `/api/method/oropendola_ai.api.account_deletion.reactivate_deleted_account`

**Method**: POST

**Parameters**:
- `email` (required): User's email address
- `full_name` (required): User's new full name
- `password` (required): New password for the account

**Response**:

```json
// Success
{
    "message": {
        "success": true,
        "message": "Your account has been successfully reactivated. You can now login with your new credentials.",
        "email": "user@example.com"
    }
}

// Error
{
    "message": {
        "success": false,
        "message": "Failed to reactivate account. Please contact support."
    }
}
```

## What Gets Reset/Restored

### On Account Deletion:
- ✓ Full name → "Deleted User"
- ✓ Personal info → Cleared (phone, location, bio)
- ✓ Account → Disabled (enabled = 0)
- ✓ API Keys → Deleted
- ✓ Subscriptions → Cancelled
- ✓ Email → **KEPT** for audit trail

### On Account Reactivation:
- ✓ Full name → Set to new provided name
- ✓ Personal info → Reset to defaults
- ✓ Account → Re-enabled (enabled = 1)
- ✓ New trial subscription → Created
- ✓ Password → Set to new password
- ✓ Comment → Added to track reactivation

## User Experience Flow

```
User tries to sign up with email@example.com
         ↓
System checks: Does this email exist?
         ↓
    ┌────┴────┐
    ↓         ↓
   NO        YES
    ↓         ↓
Proceed   Is account deleted?
to signup    ↓
        ┌────┴────┐
        ↓         ↓
       YES       NO
        ↓         ↓
  Show         Is enabled?
reactivation    ↓
  dialog    ┌───┴───┐
    ↓       ↓       ↓
  User    YES      NO
confirms   ↓       ↓
    ↓   Show    Show
Reactivate error:  error:
account  "Already contact
    ↓   registered" support
Success!
```

## Security Considerations

1. **Email Verification**: Consider adding email verification to confirm the user owns the email
2. **Rate Limiting**: Implement rate limiting on reactivation attempts
3. **Audit Trail**: All reactivations are logged in User comments
4. **Password Reset**: New password is required - old password is not reused
5. **Trial Reset**: User gets a new trial subscription

## Testing

### Test Scenario 1: Normal Signup
- Email: new@example.com
- Expected: Normal signup flow

### Test Scenario 2: Reactivation
1. Create account → Delete account → Wait for anonymization
2. Try to signup again with same email
3. Expected: Reactivation dialog appears
4. Confirm reactivation
5. Expected: Account reactivated, can login with new password

### Test Scenario 3: Existing Active Account
- Email: existing@example.com (already has active account)
- Expected: Error message "already registered"

## Future Enhancements

1. **Email Verification**: Send verification email before reactivation
2. **Grace Period Check**: Prevent reactivation during 30-day grace period
3. **Data Recovery**: Option to recover some data if within grace period
4. **Admin Approval**: Require admin approval for reactivation
5. **Notification**: Email notification when account is reactivated
