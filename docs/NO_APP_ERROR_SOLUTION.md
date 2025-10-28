# "No App" Error - Complete Solution Guide

## Problem Summary
After login, users are being redirected to `/app` (Frappe Desk) but don't have any desk apps installed, causing the "No App" error. This happens because Frappe defaults to redirecting authenticated users to the desk.

## Root Cause
The user `sammish@oropendola.ai` has the role "AI Assistant User" which may have desk permissions enabled. Even though we've implemented multiple redirect layers, Frappe's client-side code is executing the redirect before our hooks can intercept.

---

## Implemented Solutions (5 Layers)

### Layer 1: Custom Login Override
**File**: `oropendola_ai/api/auth.py`
**Hook**: `override_whitelisted_methods = {"login": "..."}`
**Status**: ✅ Implemented
**Issue**: May not be called if Frappe's login flow bypasses it

### Layer 2: Session Creation Hook
**File**: `oropendola_ai/utils/session_utils.py`
**Hook**: `on_session_creation`
**Status**: ✅ Implemented
**Issue**: Runs after login, may be too late

### Layer 3: Boot Info Override
**File**: `oropendola_ai/utils/session_utils.py`
**Hook**: `extend_bootinfo`
**Status**: ✅ Implemented
**Issue**: Client-side redirect may happen before boot info is processed

### Layer 4: Frontend Redirect
**File**: `www/login/index.html`
**Method**: `window.location.replace('/')`
**Status**: ✅ Implemented
**Issue**: Frappe's `handleLogin` may override

### Layer 5: JavaScript Guard
**File**: `public/js/force_redirect.js`
**Method**: Client-side detection of `/app` access
**Status**: ✅ Implemented
**Issue**: Executes after page load, "No App" error appears first

---

## FINAL SOLUTION: Disable Desk Access for Role

The most reliable solution is to ensure the user's role doesn't have desk access.

### Step 1: Check Role Permissions

```bash
# Check what roles the user has
bench --site oropendola.ai mariadb
```

```sql
SELECT u.name, u.email, GROUP_CONCAT(ur.role) as roles 
FROM tabUser u 
LEFT JOIN `tabHas Role` ur ON u.name = ur.parent 
WHERE u.email = 'sammish@oropendola.ai' 
GROUP BY u.name;
```

**Result**: User has "AI Assistant User" role

### Step 2: Disable Desk Access for "AI Assistant User" Role

```sql
-- Update the role to disable desk access
UPDATE `tabRole` 
SET desk_access = 0 
WHERE name = 'AI Assistant User';
```

### Step 3: Clear Sessions and Cache

```bash
# Exit MariaDB (Ctrl+D)
bench --site oropendola.ai clear-cache
bench restart
```

---

## Alternative: Create Website-Only Role

If you want to keep "AI Assistant User" with desk access for some users, create a new role:

### Option A: Via Frappe UI (Admin Panel)

1. Login as Administrator
2. Go to: Setup → User and Permissions → Role
3. Create new role: "Website Customer"
4. Set: Desk Access = 0
5. Assign to user

### Option B: Via SQL

```sql
-- Create website-only role
INSERT INTO `tabRole` (name, role_name, desk_access, disabled)
VALUES ('Website Customer', 'Website Customer', 0, 0);

-- Remove AI Assistant User role from user
DELETE FROM `tabHas Role` 
WHERE parent = 'sammish@oropendola.ai' 
AND role = 'AI Assistant User';

-- Add Website Customer role
INSERT INTO `tabHas Role` (name, parent, parenttype, parentfield, role)
VALUES (
    UUID(),
    'sammish@oropendola.ai',
    'User',
    'roles',
    'Website Customer'
);
```

---

## Immediate Fix (Recommended)

Run these commands now:

```bash
cd /home/frappe/frappe-bench

# Disable desk access for AI Assistant User role
echo "UPDATE \`tabRole\` SET desk_access = 0 WHERE name = 'AI Assistant User';" | bench --site oropendola.ai mariadb

# Clear cache and restart
bench --site oropendola.ai clear-cache
bench restart
```

---

## Verification

After applying the fix, verify:

1. **Check Role Settings**:
```sql
SELECT name, desk_access FROM `tabRole` WHERE name = 'AI Assistant User';
```
Should show: `desk_access = 0`

2. **Test Login**:
   - Go to: https://oropendola.ai/login
   - Login with: sammish@oropendola.ai / frappe
   - Should redirect to: https://oropendola.ai/ (homepage)
   - Should NOT see: "No App" error

---

## Why This Works

When a role has `desk_access = 0`:
- ✅ Frappe won't try to redirect to `/app`
- ✅ User stays on website
- ✅ No "No App" error
- ✅ All 5 protection layers become backup safety nets

---

## If Error Persists

If the error still appears after disabling desk access:

### Check User Permissions:
```sql
SELECT parent as user, role 
FROM `tabHas Role` 
WHERE parent = 'sammish@oropendola.ai';
```

### Check for System Permissions:
```sql
SELECT name, desk_access 
FROM `tabRole` 
WHERE name IN (
    SELECT role FROM `tabHas Role` 
    WHERE parent = 'sammish@oropendola.ai'
);
```

All roles should have `desk_access = 0`

---

## Long-term Solution

For all new website users:

1. Create default "Website User" role with `desk_access = 0`
2. Update user creation hook to assign this role
3. Remove any default desk roles

**File**: `oropendola_ai/utils/user_utils.py`

```python
def create_default_subscription(doc, method):
    """Called after User creation"""
    
    # Ensure user has Website User role, not desk roles
    if not frappe.db.exists("Has Role", {"parent": doc.name, "role": "Website User"}):
        doc.append("roles", {"role": "Website User"})
        
    # Remove desk roles
    desk_roles = ["Desk User", "System Manager"]
    for role in doc.roles[:]:
        if role.role in desk_roles:
            doc.remove(role)
    
    doc.save(ignore_permissions=True)
```

---

## Summary

**Quick Fix**: 
```bash
echo "UPDATE \`tabRole\` SET desk_access = 0 WHERE name = 'AI Assistant User';" | bench --site oropendola.ai mariadb && bench restart
```

**Permanent Solution**: Ensure all website user roles have `desk_access = 0`

**All 5 layers** of protection we implemented will then work as intended, providing defense-in-depth against any edge cases.

---

**Last Updated**: 2025-10-28
**Status**: Awaiting database role update to complete fix
