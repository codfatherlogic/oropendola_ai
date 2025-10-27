# Creating Default AI Model Profiles

This document explains how to create default AI Model Profiles for Oropendola AI.

## Default Models

The following AI Model Profiles are created by default:

1. **DeepSeek**
   - Provider: DeepSeek
   - Endpoint: `https://api.deepseek.com/v1/chat/completions`
   - API Key Env: `DEEPSEEK_API_KEY`
   - Features: Chat, Completion, Reasoning

2. **Grok**
   - Provider: xAI
   - Endpoint: `https://api.x.ai/v1/chat/completions`
   - API Key Env: `GROK_API_KEY`
   - Features: Chat, Completion, Realtime

3. **Claude**
   - Provider: Anthropic
   - Endpoint: `https://api.anthropic.com/v1/messages`
   - API Key Env: `ANTHROPIC_API_KEY`
   - Features: Chat, Completion, Analysis, Coding

4. **GPT-4**
   - Provider: OpenAI
   - Endpoint: `https://api.openai.com/v1/chat/completions`
   - API Key Env: `OPENAI_API_KEY`
   - Features: Chat, Completion, Multimodal

5. **Gemini**
   - Provider: Google
   - Endpoint: `https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent`
   - API Key Env: `GOOGLE_API_KEY`
   - Features: Chat, Completion, Multimodal, Long-context

## Automatic Creation (New Installations)

Default profiles are automatically created when you install the app:

```bash
bench get-app https://github.com/codfatherlogic/oropendola_ai.git --branch develop
bench install-app oropendola_ai
```

## Manual Creation (Existing Installations)

### Option 1: Using Frappe Console

```bash
cd /path/to/frappe-bench
bench --site your-site-name console
```

Then in the console:

```python
from oropendola_ai.install import create_default_model_profiles
create_default_model_profiles()
```

### Option 2: Using API Call (from logged-in session)

Navigate to your site and open the browser console, then execute:

```javascript
frappe.call({
    method: 'oropendola_ai.install.setup_default_profiles',
    callback: function(r) {
        console.log('Profiles created successfully');
    }
});
```

### Option 3: Using bench execute

```bash
bench --site your-site-name execute oropendola_ai.install.create_default_model_profiles
```

## Configuration

After creating the profiles, you need to:

1. **Set API Keys**: Configure the environment variables for each model's API key
   - Add them to your `site_config.json` or system environment

2. **Verify Endpoints**: Check that the endpoint URLs are correct for your region/version

3. **Adjust Settings**: Modify capacity scores, costs, and other parameters as needed

4. **Activate Models**: Ensure the models you want to use have `is_active` checked

## Checking Created Profiles

View created profiles:

```bash
bench --site your-site-name console
```

```python
import frappe
profiles = frappe.get_all('AI Model Profile', fields=['*'])
for p in profiles:
    print(f"{p.model_name}: {p.endpoint_url} (Active: {p.is_active})")
```

## Notes

- Profiles are only created if they don't already exist (safe to run multiple times)
- You can customize the default values in `oropendola_ai/install.py`
- All profiles are created with `is_active = 1` by default
- Health checks will be performed automatically by the scheduler
