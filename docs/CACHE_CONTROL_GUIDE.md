# Cache Control Guide

## Overview

This document explains the cache-busting mechanisms implemented in the Oropendola AI application to prevent aggressive browser caching during development and testing.

---

## Problem

During development, browsers aggressively cache HTML, CSS, and JavaScript files. This causes:
- ❌ Changes not visible without hard refresh
- ❌ Need to open incognito/private browsing windows
- ❌ Inefficient development workflow
- ❌ Testing difficulties

---

## Solution Implemented

### 1. **Developer Mode Enabled**

```bash
bench --site oropendola.ai set-config developer_mode 1
```

**Effect**: 
- Enables auto-reload for Python changes
- Disables some caching mechanisms
- Shows more detailed error messages

---

### 2. **HTTP Cache Headers** ([utils/cache_utils.py](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/oropendola_ai/utils/cache_utils.py))

Added `before_request` hook that sets cache headers based on environment:

#### **Development Mode** (current):
```http
Cache-Control: no-cache, no-store, must-revalidate, max-age=0
Pragma: no-cache
Expires: 0
```

**Result**: Browser MUST revalidate on every request

#### **Production Mode**:
```http
Cache-Control: public, max-age=3600, must-revalidate
Vary: Accept-Encoding
```

**Result**: Cache for 1 hour with validation

---

### 3. **HTML Meta Tags**

Added to all HTML pages ([index.html](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/www/index.html), [login/index.html](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/www/login/index.html), [pricing/index.html](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/www/pricing/index.html)):

```html
<!-- Cache Control -->
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
```

---

## How to Use

### **During Development**

✅ **Changes now visible immediately!**

Just refresh the page (F5 or Cmd+R):
- No need for hard refresh (Ctrl+F5)
- No need for incognito mode
- No need to clear cache manually

### **Testing Changes**

1. Make code changes
2. Run: `bench build --app oropendola_ai && bench restart`
3. Refresh browser (F5)
4. ✅ See changes immediately!

---

## Production Deployment

### **Before Going Live**

Disable developer mode for production:

```bash
bench --site oropendola.ai set-config developer_mode 0
bench restart
```

**Why?**
- Enables caching for better performance
- Hides detailed error messages
- Optimizes resource delivery

---

## Cache-Busting Utility

The [get_cache_buster()](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/oropendola_ai/utils/cache_utils.py#L54-L63) function can be used for asset versioning:

```python
from oropendola_ai.oropendola_ai.utils.cache_utils import get_cache_buster

# In templates
version = get_cache_buster()
script_url = f"/assets/js/app.js?v={version}"
```

---

## Troubleshooting

### **Changes Still Not Visible?**

1. **Check developer mode**:
```bash
bench --site oropendola.ai console
```
```python
>>> frappe.conf.developer_mode
1  # Should be 1 for development
```

2. **Hard refresh** (just once):
   - Windows/Linux: `Ctrl + F5`
   - Mac: `Cmd + Shift + R`

3. **Clear browser cache**:
   - Chrome: Settings → Privacy → Clear browsing data
   - Firefox: Settings → Privacy → Clear Data

4. **Verify headers**:
   - Open DevTools (F12)
   - Network tab
   - Reload page
   - Check response headers for `Cache-Control`

### **Assets Not Loading?**

```bash
# Rebuild assets
bench build --app oropendola_ai

# Check if assets linked
ls -la sites/assets/oropendola_ai

# If missing, run
bench setup nginx
sudo service nginx reload
```

---

## Technical Details

### **Hook Registration** ([hooks.py](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/hooks.py#L208-L208))

```python
before_request = ["oropendola_ai.oropendola_ai.utils.cache_utils.set_cache_headers"]
```

### **Request Flow**

```
Browser Request
    ↓
Frappe receives request
    ↓
before_request hook fires
    ↓
set_cache_headers() executed
    ↓
Cache-Control headers set
    ↓
Response sent with headers
    ↓
Browser stores/ignores based on headers
```

---

## Best Practices

### **Development**
- ✅ Keep developer_mode = 1
- ✅ Use regular refresh (F5)
- ✅ Monitor Network tab in DevTools
- ✅ Build after changes: `bench build --app oropendola_ai`

### **Production**
- ✅ Set developer_mode = 0
- ✅ Enable caching for performance
- ✅ Use versioned assets
- ✅ Configure CDN if needed

---

## Files Modified

1. **[hooks.py](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/hooks.py)** - Added before_request hook
2. **[cache_utils.py](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/oropendola_ai/utils/cache_utils.py)** - Created cache control utility
3. **[index.html](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/www/index.html)** - Added cache meta tags
4. **[login/index.html](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/www/login/index.html)** - Added cache meta tags
5. **[pricing/index.html](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/www/pricing/index.html)** - Added cache meta tags
6. **Site Config** - Enabled developer_mode

---

## Summary

✅ **Developer mode enabled**
✅ **HTTP cache headers configured**
✅ **HTML meta tags added**
✅ **Utility functions created**
✅ **Production-ready configuration**

**Result**: No more incognito mode needed! Just refresh and see your changes. 🎉

---

**Last Updated**: 2025-10-28
**Status**: ✅ Active and working
# Cache Control Guide

## Overview

This document explains the cache-busting mechanisms implemented in the Oropendola AI application to prevent aggressive browser caching during development and testing.

---

## Problem

During development, browsers aggressively cache HTML, CSS, and JavaScript files. This causes:
- ❌ Changes not visible without hard refresh
- ❌ Need to open incognito/private browsing windows
- ❌ Inefficient development workflow
- ❌ Testing difficulties

---

## Solution Implemented

### 1. **Developer Mode Enabled**

```bash
bench --site oropendola.ai set-config developer_mode 1
```

**Effect**: 
- Enables auto-reload for Python changes
- Disables some caching mechanisms
- Shows more detailed error messages

---

### 2. **HTTP Cache Headers** ([utils/cache_utils.py](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/oropendola_ai/utils/cache_utils.py))

Added `before_request` hook that sets cache headers based on environment:

#### **Development Mode** (current):
```http
Cache-Control: no-cache, no-store, must-revalidate, max-age=0
Pragma: no-cache
Expires: 0
```

**Result**: Browser MUST revalidate on every request

#### **Production Mode**:
```http
Cache-Control: public, max-age=3600, must-revalidate
Vary: Accept-Encoding
```

**Result**: Cache for 1 hour with validation

---

### 3. **HTML Meta Tags**

Added to all HTML pages ([index.html](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/www/index.html), [login/index.html](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/www/login/index.html), [pricing/index.html](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/www/pricing/index.html)):

```html
<!-- Cache Control -->
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
```

---

## How to Use

### **During Development**

✅ **Changes now visible immediately!**

Just refresh the page (F5 or Cmd+R):
- No need for hard refresh (Ctrl+F5)
- No need for incognito mode
- No need to clear cache manually

### **Testing Changes**

1. Make code changes
2. Run: `bench build --app oropendola_ai && bench restart`
3. Refresh browser (F5)
4. ✅ See changes immediately!

---

## Production Deployment

### **Before Going Live**

Disable developer mode for production:

```bash
bench --site oropendola.ai set-config developer_mode 0
bench restart
```

**Why?**
- Enables caching for better performance
- Hides detailed error messages
- Optimizes resource delivery

---

## Cache-Busting Utility

The [get_cache_buster()](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/oropendola_ai/utils/cache_utils.py#L54-L63) function can be used for asset versioning:

```python
from oropendola_ai.oropendola_ai.utils.cache_utils import get_cache_buster

# In templates
version = get_cache_buster()
script_url = f"/assets/js/app.js?v={version}"
```

---

## Troubleshooting

### **Changes Still Not Visible?**

1. **Check developer mode**:
```bash
bench --site oropendola.ai console
```
```python
>>> frappe.conf.developer_mode
1  # Should be 1 for development
```

2. **Hard refresh** (just once):
   - Windows/Linux: `Ctrl + F5`
   - Mac: `Cmd + Shift + R`

3. **Clear browser cache**:
   - Chrome: Settings → Privacy → Clear browsing data
   - Firefox: Settings → Privacy → Clear Data

4. **Verify headers**:
   - Open DevTools (F12)
   - Network tab
   - Reload page
   - Check response headers for `Cache-Control`

### **Assets Not Loading?**

```bash
# Rebuild assets
bench build --app oropendola_ai

# Check if assets linked
ls -la sites/assets/oropendola_ai

# If missing, run
bench setup nginx
sudo service nginx reload
```

---

## Technical Details

### **Hook Registration** ([hooks.py](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/hooks.py#L208-L208))

```python
before_request = ["oropendola_ai.oropendola_ai.utils.cache_utils.set_cache_headers"]
```

### **Request Flow**

```
Browser Request
    ↓
Frappe receives request
    ↓
before_request hook fires
    ↓
set_cache_headers() executed
    ↓
Cache-Control headers set
    ↓
Response sent with headers
    ↓
Browser stores/ignores based on headers
```

---

## Best Practices

### **Development**
- ✅ Keep developer_mode = 1
- ✅ Use regular refresh (F5)
- ✅ Monitor Network tab in DevTools
- ✅ Build after changes: `bench build --app oropendola_ai`

### **Production**
- ✅ Set developer_mode = 0
- ✅ Enable caching for performance
- ✅ Use versioned assets
- ✅ Configure CDN if needed

---

## Files Modified

1. **[hooks.py](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/hooks.py)** - Added before_request hook
2. **[cache_utils.py](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/oropendola_ai/utils/cache_utils.py)** - Created cache control utility
3. **[index.html](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/www/index.html)** - Added cache meta tags
4. **[login/index.html](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/www/login/index.html)** - Added cache meta tags
5. **[pricing/index.html](file:///home/frappe/frappe-bench/apps/oropendola_ai/oropendola_ai/www/pricing/index.html)** - Added cache meta tags
6. **Site Config** - Enabled developer_mode

---

## Summary

✅ **Developer mode enabled**
✅ **HTTP cache headers configured**
✅ **HTML meta tags added**
✅ **Utility functions created**
✅ **Production-ready configuration**

**Result**: No more incognito mode needed! Just refresh and see your changes. 🎉

---

**Last Updated**: 2025-10-28
**Status**: ✅ Active and working
