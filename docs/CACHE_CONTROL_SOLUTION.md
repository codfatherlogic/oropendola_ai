# Cache Control Solution Guide

## Problem
Browser caches were not clearing properly during development, requiring incognito mode to see changes.

## Complete Solution Implemented

### 1. Server-Side Cache Headers ✅
**File**: `/oropendola_ai/oropendola_ai/utils/cache_utils.py`

**What it does**:
- Sets HTTP headers on every response to prevent caching
- Automatically detects developer mode and applies aggressive no-cache policies
- Adds timestamp-based ETags to force cache invalidation

**Headers Applied** (in developer mode):
```
Cache-Control: no-cache, no-store, must-revalidate, max-age=0, s-maxage=0
Pragma: no-cache
Expires: 0
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
ETag: dev-{timestamp}
```

**Hooks Used**:
- `before_request`: Sets headers early in request lifecycle
- `after_request`: Ensures headers are set even if response is created late

### 2. HTML Meta Tags ✅
**Files Updated**:
- `/www/index.html` (Homepage)
- `/www/login/index.html` (Login page)
- `/www/pricing/index.html` (Pricing page)

**Meta Tags Added**:
```html
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
```

### 3. JavaScript Cache Buster ✅
**File**: `/public/js/cache-buster.js`

**Features**:
- Automatically adds timestamp query parameter to all API calls
- Overrides `fetch()` to inject no-cache headers
- Provides `window.forceReload()` helper function
- Supports keyboard shortcut: **Ctrl+Shift+R** for hard reload
- Logs cache buster status to console

**Auto-included in**:
- Homepage (`/`)
- Login page (`/login`)
- Pricing page (`/pricing`)

### 4. API Call Enhancements ✅
**File**: `/www/pricing/index.html`

**Improvements**:
- Cache-busting timestamp added to API calls
- Explicit no-cache headers on fetch requests
- Proper error handling for cached responses

## How to See Changes Without Incognito

### Method 1: Hard Refresh (Recommended) ⚡
- **Windows/Linux**: `Ctrl + Shift + R` or `Ctrl + F5`
- **Mac**: `Cmd + Shift + R`

This will:
- Bypass ALL browser caches
- Force download fresh copies
- Work 100% of the time

### Method 2: DevTools Empty Cache 🔧
1. Open browser DevTools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

### Method 3: Clear Browser Cache 🗑️
**Chrome/Edge**:
1. Press `Ctrl + Shift + Delete`
2. Select "Cached images and files"
3. Click "Clear data"

**Firefox**:
1. Press `Ctrl + Shift + Delete`
2. Select "Cache"
3. Click "Clear Now"

### Method 4: Use the Cache Buster Script 🚀
The cache-buster.js script runs automatically and:
- Adds `?_={timestamp}` to API calls
- Injects no-cache headers
- Console logs: `🚀 Cache Buster Active - timestamp: {number}`

**Verify it's working**:
1. Open DevTools Console (F12)
2. Look for: `🚀 Cache Buster Active - timestamp: 1234567890`
3. All API calls should have `?_=` parameter

### Method 5: Simple Refresh (Should Work Now!) ✨
After all implementations, a simple **F5** or browser refresh button should work because:
- Server sends no-cache headers
- HTML has meta tags preventing cache
- JavaScript adds timestamps
- Developer mode is enabled

## Verification Steps

### Check if Cache Control is Working:

**1. Check Response Headers**:
```bash
curl -I https://oropendola.ai/pricing
```

Expected output should include:
```
Cache-Control: no-cache, no-store, must-revalidate, max-age=0, s-maxage=0
Pragma: no-cache
Expires: 0
```

**2. Check Developer Mode**:
```bash
bench --site oropendola.ai show-config | grep developer_mode
```

Expected output:
```
| developer_mode | 1 |
```

**3. Check Browser Console**:
- Open DevTools (F12)
- Refresh the page
- Look for: `🚀 Cache Buster Active`
- Check Network tab → API calls should have `?_=` parameter

## Troubleshooting

### Issue: Still seeing old content
**Solution**: Do a **hard refresh** (Ctrl+Shift+R)

### Issue: Cache buster not loading
**Solution**: 
```bash
bench build --app oropendola_ai
bench restart
```

### Issue: Changes not appearing after hard refresh
**Check**:
1. Developer mode enabled: `bench --site oropendola.ai show-config`
2. Server restarted: `bench restart`
3. Assets built: `bench build --app oropendola_ai`

### Issue: API calls still cached
**Solution**: 
- Check Network tab in DevTools
- Verify `?_={timestamp}` is appended
- Check request headers include `Cache-Control: no-cache`

## Production Considerations

When you deploy to production, the system automatically switches to proper caching:

**To enable production mode**:
```bash
bench --site oropendola.ai set-config developer_mode 0
bench restart
```

**Production cache headers**:
```
Cache-Control: public, max-age=3600, must-revalidate
Vary: Accept-Encoding
```

This gives you:
- ✅ 1-hour cache for better performance
- ✅ Revalidation on each access
- ✅ Proper CDN support

## Quick Reference Commands

```bash
# Enable developer mode (no caching)
bench --site oropendola.ai set-config developer_mode 1

# Disable developer mode (production caching)
bench --site oropendola.ai set-config developer_mode 0

# Build assets
bench build --app oropendola_ai

# Restart server
bench restart

# Clear cache
bench --site oropendola.ai clear-cache

# Full rebuild and restart
bench build --app oropendola_ai && bench restart
```

## Summary

You now have **4 layers of cache prevention**:
1. ✅ **Server-side HTTP headers** (before_request + after_request hooks)
2. ✅ **HTML meta tags** (in all pages)
3. ✅ **JavaScript cache buster** (automatic timestamp injection)
4. ✅ **Developer mode** (Frappe's built-in cache prevention)

**Result**: Changes should appear with a simple F5 refresh, no incognito mode needed! 🎉

For maximum effectiveness, always use **Ctrl+Shift+R** for hard refresh during development.
# Cache Control Solution Guide

## Problem
Browser caches were not clearing properly during development, requiring incognito mode to see changes.

## Complete Solution Implemented

### 1. Server-Side Cache Headers ✅
**File**: `/oropendola_ai/oropendola_ai/utils/cache_utils.py`

**What it does**:
- Sets HTTP headers on every response to prevent caching
- Automatically detects developer mode and applies aggressive no-cache policies
- Adds timestamp-based ETags to force cache invalidation

**Headers Applied** (in developer mode):
```
Cache-Control: no-cache, no-store, must-revalidate, max-age=0, s-maxage=0
Pragma: no-cache
Expires: 0
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
ETag: dev-{timestamp}
```

**Hooks Used**:
- `before_request`: Sets headers early in request lifecycle
- `after_request`: Ensures headers are set even if response is created late

### 2. HTML Meta Tags ✅
**Files Updated**:
- `/www/index.html` (Homepage)
- `/www/login/index.html` (Login page)
- `/www/pricing/index.html` (Pricing page)

**Meta Tags Added**:
```html
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
```

### 3. JavaScript Cache Buster ✅
**File**: `/public/js/cache-buster.js`

**Features**:
- Automatically adds timestamp query parameter to all API calls
- Overrides `fetch()` to inject no-cache headers
- Provides `window.forceReload()` helper function
- Supports keyboard shortcut: **Ctrl+Shift+R** for hard reload
- Logs cache buster status to console

**Auto-included in**:
- Homepage (`/`)
- Login page (`/login`)
- Pricing page (`/pricing`)

### 4. API Call Enhancements ✅
**File**: `/www/pricing/index.html`

**Improvements**:
- Cache-busting timestamp added to API calls
- Explicit no-cache headers on fetch requests
- Proper error handling for cached responses

## How to See Changes Without Incognito

### Method 1: Hard Refresh (Recommended) ⚡
- **Windows/Linux**: `Ctrl + Shift + R` or `Ctrl + F5`
- **Mac**: `Cmd + Shift + R`

This will:
- Bypass ALL browser caches
- Force download fresh copies
- Work 100% of the time

### Method 2: DevTools Empty Cache 🔧
1. Open browser DevTools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

### Method 3: Clear Browser Cache 🗑️
**Chrome/Edge**:
1. Press `Ctrl + Shift + Delete`
2. Select "Cached images and files"
3. Click "Clear data"

**Firefox**:
1. Press `Ctrl + Shift + Delete`
2. Select "Cache"
3. Click "Clear Now"

### Method 4: Use the Cache Buster Script 🚀
The cache-buster.js script runs automatically and:
- Adds `?_={timestamp}` to API calls
- Injects no-cache headers
- Console logs: `🚀 Cache Buster Active - timestamp: {number}`

**Verify it's working**:
1. Open DevTools Console (F12)
2. Look for: `🚀 Cache Buster Active - timestamp: 1234567890`
3. All API calls should have `?_=` parameter

### Method 5: Simple Refresh (Should Work Now!) ✨
After all implementations, a simple **F5** or browser refresh button should work because:
- Server sends no-cache headers
- HTML has meta tags preventing cache
- JavaScript adds timestamps
- Developer mode is enabled

## Verification Steps

### Check if Cache Control is Working:

**1. Check Response Headers**:
```bash
curl -I https://oropendola.ai/pricing
```

Expected output should include:
```
Cache-Control: no-cache, no-store, must-revalidate, max-age=0, s-maxage=0
Pragma: no-cache
Expires: 0
```

**2. Check Developer Mode**:
```bash
bench --site oropendola.ai show-config | grep developer_mode
```

Expected output:
```
| developer_mode | 1 |
```

**3. Check Browser Console**:
- Open DevTools (F12)
- Refresh the page
- Look for: `🚀 Cache Buster Active`
- Check Network tab → API calls should have `?_=` parameter

## Troubleshooting

### Issue: Still seeing old content
**Solution**: Do a **hard refresh** (Ctrl+Shift+R)

### Issue: Cache buster not loading
**Solution**: 
```bash
bench build --app oropendola_ai
bench restart
```

### Issue: Changes not appearing after hard refresh
**Check**:
1. Developer mode enabled: `bench --site oropendola.ai show-config`
2. Server restarted: `bench restart`
3. Assets built: `bench build --app oropendola_ai`

### Issue: API calls still cached
**Solution**: 
- Check Network tab in DevTools
- Verify `?_={timestamp}` is appended
- Check request headers include `Cache-Control: no-cache`

## Production Considerations

When you deploy to production, the system automatically switches to proper caching:

**To enable production mode**:
```bash
bench --site oropendola.ai set-config developer_mode 0
bench restart
```

**Production cache headers**:
```
Cache-Control: public, max-age=3600, must-revalidate
Vary: Accept-Encoding
```

This gives you:
- ✅ 1-hour cache for better performance
- ✅ Revalidation on each access
- ✅ Proper CDN support

## Quick Reference Commands

```bash
# Enable developer mode (no caching)
bench --site oropendola.ai set-config developer_mode 1

# Disable developer mode (production caching)
bench --site oropendola.ai set-config developer_mode 0

# Build assets
bench build --app oropendola_ai

# Restart server
bench restart

# Clear cache
bench --site oropendola.ai clear-cache

# Full rebuild and restart
bench build --app oropendola_ai && bench restart
```

## Summary

You now have **4 layers of cache prevention**:
1. ✅ **Server-side HTTP headers** (before_request + after_request hooks)
2. ✅ **HTML meta tags** (in all pages)
3. ✅ **JavaScript cache buster** (automatic timestamp injection)
4. ✅ **Developer mode** (Frappe's built-in cache prevention)

**Result**: Changes should appear with a simple F5 refresh, no incognito mode needed! 🎉

For maximum effectiveness, always use **Ctrl+Shift+R** for hard refresh during development.
