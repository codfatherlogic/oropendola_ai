# API Key Migration to Site Config - Complete ✅

## Migration Summary

Successfully migrated API keys from AI Model Profile database storage to `site_config.json` for enhanced security.

---

## What Was Changed

### 1. **Site Configuration** ✅
Added API keys to `/home/frappe/frappe-bench/sites/oropendola.ai/site_config.json`:

```json
{
  "DEEPSEEK_API_KEY": "sk-83c910a70218495a81266e9f02f10ac2",
  "GROK_API_KEY": "xai-OTnX8TNMbN7pBIV2wcFEmbs0ZRmHRjeO4XJI3P2AY2Ex1dS1b069Y7M9AftDtogPCc3J0kQBOxuF8B0R",
  "ANTHROPIC_API_KEY": "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",
  "OPENAI_API_KEY": "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",
  "GOOGLE_API_KEY": "AIzaSyAGfC6H9zN4PyBTaIePRTDNEHW2fg4uSgg"
}
```

### 2. **AI Model Profiles** ✅
Updated database to store only environment variable names:

| Model | `api_key_env_var` (Before) | `api_key_env_var` (After) |
|-------|---------------------------|---------------------------|
| DeepSeek | `sk-83c910a...` (actual key) | `DEEPSEEK_API_KEY` |
| Grok | `xai-OTnX8...` (actual key) | `GROK_API_KEY` |
| Claude | `sk-ant-api...` (actual key) | `ANTHROPIC_API_KEY` |
| GPT-4 | `sk-proj-5I...` (actual key) | `OPENAI_API_KEY` |
| Gemini | `AIzaSyAGf...` (actual key) | `GOOGLE_API_KEY` |

### 3. **Code Changes** ✅

#### `ai_model_profile.py`
Added `get_api_key()` method to retrieve keys from config:

```python
def get_api_key(self):
    """Get API key from site config or environment variable"""
    if not self.api_key_env_var:
        return None
    
    # Try to get from Frappe site config first
    api_key = frappe.conf.get(self.api_key_env_var)
    
    # Fallback to OS environment variable
    if not api_key:
        api_key = os.getenv(self.api_key_env_var)
    
    return api_key
```

#### `model_router.py`
Added `prepare_request_headers()` method to inject API keys:

```python
def prepare_request_headers(self, model_profile) -> dict:
    """Prepare request headers with API key from config"""
    headers = {"Content-Type": "application/json"}
    
    # Get API key from model profile (reads from site config)
    api_key = model_profile.get_api_key()
    
    if api_key:
        # Add authorization based on provider
        if model_profile.provider == "OpenAI":
            headers["Authorization"] = f"Bearer {api_key}"
        elif model_profile.provider == "Anthropic":
            headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"
        # ... etc
    
    return headers, api_key
```

Updated all `requests.post()` calls to include headers.

---

## Benefits

### Security Improvements ✅
- ✅ **API keys NOT in database** - Keys no longer exposed in database queries
- ✅ **API keys NOT in backups** - Database backups don't contain sensitive keys
- ✅ **Restricted access** - Only system administrators with server access can view keys
- ✅ **Industry best practice** - Follows 12-factor app methodology

### Operational Benefits ✅
- ✅ **Easy key rotation** - Update keys in `site_config.json` without touching database
- ✅ **Environment parity** - Same code works across dev/staging/prod with different keys
- ✅ **Centralized config** - All secrets in one place
- ✅ **Audit trail** - Can track config file changes via version control (if desired)

---

## How to Update API Keys

### Method 1: Using Bench Command (Recommended)
```bash
bench --site oropendola.ai set-config OPENAI_API_KEY "new-key-here"
```

### Method 2: Direct File Edit
Edit `/home/frappe/frappe-bench/sites/oropendola.ai/site_config.json`:
```json
{
  "OPENAI_API_KEY": "new-key-here"
}
```

Then restart the bench:
```bash
bench restart
```

---

## Verification

All API keys successfully retrieving from config:

```
✅ DeepSeek   : sk-83c910a70218495a8...9f02f10ac2
✅ Grok       : xai-OTnX8TNMbN7pBIV2...QBOxuF8B0R
✅ Claude     : sk-ant-api03-D5K9CiH...w-c9md9QAA
✅ GPT-4      : sk-proj-5INLaGGUKBu6...D5fdF7LlAA
✅ Gemini     : AIzaSyAGfC6H9zN4PyBT...HW2fg4uSgg
```

---

## Environment Variables Priority

The system checks in this order:

1. **Frappe site config** (`site_config.json`) - ⭐ Primary
2. **OS environment variables** - Fallback
3. **None** - If not found

---

## Migration Steps Completed

1. ✅ Extracted API keys from database
2. ✅ Added keys to `site_config.json` using `bench set-config`
3. ✅ Updated AI Model Profiles to store env var names only
4. ✅ Added `get_api_key()` method to AI Model Profile
5. ✅ Updated model router to use keys from config
6. ✅ Tested and verified all keys retrievable
7. ✅ Documentation created

---

## Production Checklist

When deploying to production:

- [ ] Set API keys in production `site_config.json`
- [ ] Verify keys work with test API calls
- [ ] Remove API keys from version control
- [ ] Set up key rotation schedule
- [ ] Document key management procedures
- [ ] Set restrictive file permissions on `site_config.json` (600)

---

## 🎉 Migration Complete!

Your API keys are now securely stored in `site_config.json` and follow industry best practices for secrets management.
