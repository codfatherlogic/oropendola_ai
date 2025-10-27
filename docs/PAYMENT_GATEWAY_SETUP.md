# Oropendola AI - Environment Configuration Guide

## Payment Gateway Configuration

### Option 1: Razorpay (Recommended for India)

**Sign up:** https://razorpay.com/

```bash
# Test/Sandbox Credentials
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=your_test_secret_key
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

# Production Credentials
RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=your_live_secret_key
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret
```

**Setup Steps:**
1. Create account at https://razorpay.com/
2. Go to Settings → API Keys
3. Generate Test/Live Keys
4. Copy Key ID and Key Secret
5. Go to Settings → Webhooks
6. Add webhook URL: `https://yourdomain.com/api/method/oropendola_ai.services.razorpay_gateway.razorpay_webhook`
7. Select events: `payment.captured`, `payment.failed`
8. Copy Webhook Secret

### Option 2: PayU (Alternative for India)

**Sign up:** https://payu.in/

```bash
# Test/Sandbox Credentials
PAYU_MERCHANT_KEY=your_test_merchant_key
PAYU_MERCHANT_SALT=your_test_salt
PAYU_MODE=test

# Production Credentials
PAYU_MERCHANT_KEY=your_live_merchant_key
PAYU_MERCHANT_SALT=your_live_salt
PAYU_MODE=live
```

**Setup Steps:**
1. Create merchant account at https://payu.in/
2. Complete KYC verification
3. Get test credentials from dashboard
4. Configure return URLs:
   - Success URL: `https://yourdomain.com/api/method/oropendola_ai.services.payu_gateway.payment_success`
   - Failure URL: `https://yourdomain.com/api/method/oropendola_ai.services.payu_gateway.payment_failure`
5. For production, request live credentials after testing

### Default Gateway Selection

```bash
# Set default payment gateway (razorpay or payu)
DEFAULT_PAYMENT_GATEWAY=razorpay
```

**Note:** System will auto-detect available gateways based on configured credentials.

## Complete .env File Template

```bash
# ============================================
# OROPENDOLA AI - ENVIRONMENT CONFIGURATION
# ============================================

# -----------------
# Frappe Settings
# -----------------
FRAPPE_SITE_NAME=oropendola.local
FRAPPE_ENV=production

# -----------------
# Database
# -----------------
DB_HOST=localhost
DB_PORT=3306
DB_NAME=oropendola_db
DB_USER=frappe
DB_PASSWORD=your_secure_db_password
DB_ROOT_PASSWORD=your_mysql_root_password

# -----------------
# Redis
# -----------------
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE=redis://localhost:6379/1
REDIS_QUEUE=redis://localhost:6379/2
REDIS_PASSWORD=your_redis_password  # Optional

# -----------------
# Payment Gateways
# -----------------

# Primary Gateway
DEFAULT_PAYMENT_GATEWAY=razorpay

# Razorpay Configuration
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=your_razorpay_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

# PayU Configuration (Optional)
PAYU_MERCHANT_KEY=your_payu_merchant_key
PAYU_MERCHANT_SALT=your_payu_salt
PAYU_MODE=test

# -----------------
# AI Model Endpoints
# -----------------

# DeepSeek
DEEPSEEK_ENDPOINT=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_API_KEY=your_deepseek_api_key

# Grok (X.AI)
GROK_ENDPOINT=https://api.x.ai/v1/chat/completions
GROK_API_KEY=your_grok_api_key

# Claude (Anthropic)
CLAUDE_ENDPOINT=https://api.anthropic.com/v1/messages
CLAUDE_API_KEY=your_claude_api_key

# GPT-4 (OpenAI) - Optional
OPENAI_ENDPOINT=https://api.openai.com/v1/chat/completions
OPENAI_API_KEY=your_openai_api_key

# Gemini (Google) - Optional
GEMINI_ENDPOINT=https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent
GEMINI_API_KEY=your_gemini_api_key

# -----------------
# Routing Weights
# -----------------
# Adjust these to optimize model selection
WEIGHT_LATENCY=1.0      # Higher = prioritize faster models
WEIGHT_CAPACITY=0.5     # Higher = prioritize models with more capacity
WEIGHT_COST=1.5         # Higher = prioritize cheaper models
WEIGHT_PRIORITY=2.0     # Higher = prioritize subscription tier

# -----------------
# Security
# -----------------
ENCRYPTION_KEY=your_32_char_encryption_key_here
SESSION_TIMEOUT=3600
API_RATE_LIMIT_GLOBAL=1000  # Requests per hour

# -----------------
# Email (SMTP)
# -----------------
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=noreply@yourdomain.com

# -----------------
# Monitoring
# -----------------
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
GRAFANA_ENABLED=true
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD=your_grafana_password

# -----------------
# Logging
# -----------------
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
SENTRY_DSN=your_sentry_dsn  # Optional error tracking

# -----------------
# Application URLs
# -----------------
APP_URL=https://yourdomain.com
API_URL=https://api.yourdomain.com
ADMIN_URL=https://admin.yourdomain.com

# -----------------
# Deployment
# -----------------
ENVIRONMENT=production  # development, staging, production
WORKERS=4
ENABLE_SCHEDULER=true
ENABLE_BACKGROUND_WORKERS=true
```

## Installation Instructions

### 1. Install Dependencies

```bash
# Install Python packages
pip install razorpay redis prometheus-client requests

# For PayU support
# No additional package needed (uses direct HTTP API)
```

### 2. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit with your credentials
nano .env

# Or use script
chmod +x scripts/setup_env.sh
./scripts/setup_env.sh
```

### 3. Initialize Payment Gateways

```bash
# Test Razorpay connection
bench --site oropendola.local console
>>> from oropendola_ai.services.razorpay_gateway import get_gateway
>>> gateway = get_gateway()
>>> print("Razorpay configured successfully!")

# Test PayU connection
>>> from oropendola_ai.services.payu_gateway import get_payu_gateway
>>> gateway = get_payu_gateway()
>>> print("PayU configured successfully!")
```

### 4. Setup Webhooks

#### Razorpay Webhooks:
1. Login to Razorpay Dashboard
2. Go to Settings → Webhooks
3. Click "Add New Webhook"
4. Webhook URL: `https://yourdomain.com/api/method/oropendola_ai.services.razorpay_gateway.razorpay_webhook`
5. Select Events:
   - `payment.captured`
   - `payment.failed`
   - `payment.authorized`
6. Set Active: Yes
7. Copy the Webhook Secret to your `.env` file

#### PayU Webhooks:
PayU uses return URLs instead of webhooks:
- Success URL: `https://yourdomain.com/api/method/oropendola_ai.services.payu_gateway.payment_success`
- Failure URL: `https://yourdomain.com/api/method/oropendola_ai.services.payu_gateway.payment_failure`

These are automatically configured when creating payment requests.

## Testing Payment Gateways

### Test Razorpay

```python
# In Frappe console
from oropendola_ai.services.payment_manager import create_payment_order

# Create test invoice first
invoice = frappe.get_doc({
    "doctype": "AI Invoice",
    "customer": "Test Customer",
    "amount_due": 199,
    "currency": "INR",
    "status": "Draft"
})
invoice.insert()

# Create payment order
result = create_payment_order(invoice.name, gateway="razorpay")
print(result)
```

### Test PayU

```python
# Create payment request
result = create_payment_order(invoice.name, gateway="payu")
print(result)

# You'll get a payment URL and form data
# Open the URL in browser to test
```

### Razorpay Test Cards

```
Card Number: 4111 1111 1111 1111
CVV: Any 3 digits
Expiry: Any future date
```

### PayU Test Cards

```
Success Card: 5123 4567 8901 2346
CVV: 123
Expiry: 05/2026

Failure Card: 5123 4567 8901 2347
CVV: 123
Expiry: 05/2026
```

## Troubleshooting

### Razorpay Issues

**Error: "Invalid API Key"**
```bash
# Check credentials
echo $RAZORPAY_KEY_ID
echo $RAZORPAY_KEY_SECRET

# Verify in Razorpay dashboard
# Ensure using test keys in test mode
```

**Webhook not receiving events:**
1. Check webhook URL is publicly accessible
2. Verify SSL certificate is valid
3. Check webhook secret matches
4. Review Razorpay dashboard logs

### PayU Issues

**Error: "Invalid Hash"**
```bash
# Verify merchant salt is correct
# Hash generation is case-sensitive
# Check all parameters are in correct order
```

**Payment redirect not working:**
1. Ensure return URLs are publicly accessible
2. Check merchant key is correct
3. Verify mode (test/live) matches credentials

## Production Checklist

- [ ] Switch to live API keys (Razorpay/PayU)
- [ ] Configure production database
- [ ] Setup Redis with password
- [ ] Enable SSL/TLS for all endpoints
- [ ] Configure production webhooks
- [ ] Setup monitoring (Prometheus + Grafana)
- [ ] Configure email notifications
- [ ] Enable rate limiting
- [ ] Setup automated backups
- [ ] Configure CDN for static assets
- [ ] Test payment flows end-to-end
- [ ] Setup error tracking (Sentry)
- [ ] Configure log aggregation

## Security Best Practices

1. **Never commit `.env` file to version control**
2. **Use strong passwords** for all services
3. **Enable 2FA** on payment gateway accounts
4. **Rotate API keys** regularly (every 90 days)
5. **Monitor webhook failures** and retry failed payments
6. **Validate all payment signatures** before processing
7. **Use HTTPS only** for all payment endpoints
8. **Implement IP whitelisting** for admin endpoints
9. **Regular security audits** of payment flows
10. **PCI DSS compliance** for card data (if handling directly)

## Support

For payment gateway issues:
- **Razorpay:** support@razorpay.com | https://razorpay.com/support/
- **PayU:** merchantsupport@payu.in | https://payu.in/contact-us

For Oropendola AI issues:
- GitHub: https://github.com/your-org/oropendola_ai/issues
- Email: support@yourdomain.com
# Oropendola AI - Environment Configuration Guide

## Payment Gateway Configuration

### Option 1: Razorpay (Recommended for India)

**Sign up:** https://razorpay.com/

```bash
# Test/Sandbox Credentials
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=your_test_secret_key
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

# Production Credentials
RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=your_live_secret_key
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret
```

**Setup Steps:**
1. Create account at https://razorpay.com/
2. Go to Settings → API Keys
3. Generate Test/Live Keys
4. Copy Key ID and Key Secret
5. Go to Settings → Webhooks
6. Add webhook URL: `https://yourdomain.com/api/method/oropendola_ai.services.razorpay_gateway.razorpay_webhook`
7. Select events: `payment.captured`, `payment.failed`
8. Copy Webhook Secret

### Option 2: PayU (Alternative for India)

**Sign up:** https://payu.in/

```bash
# Test/Sandbox Credentials
PAYU_MERCHANT_KEY=your_test_merchant_key
PAYU_MERCHANT_SALT=your_test_salt
PAYU_MODE=test

# Production Credentials
PAYU_MERCHANT_KEY=your_live_merchant_key
PAYU_MERCHANT_SALT=your_live_salt
PAYU_MODE=live
```

**Setup Steps:**
1. Create merchant account at https://payu.in/
2. Complete KYC verification
3. Get test credentials from dashboard
4. Configure return URLs:
   - Success URL: `https://yourdomain.com/api/method/oropendola_ai.services.payu_gateway.payment_success`
   - Failure URL: `https://yourdomain.com/api/method/oropendola_ai.services.payu_gateway.payment_failure`
5. For production, request live credentials after testing

### Default Gateway Selection

```bash
# Set default payment gateway (razorpay or payu)
DEFAULT_PAYMENT_GATEWAY=razorpay
```

**Note:** System will auto-detect available gateways based on configured credentials.

## Complete .env File Template

```bash
# ============================================
# OROPENDOLA AI - ENVIRONMENT CONFIGURATION
# ============================================

# -----------------
# Frappe Settings
# -----------------
FRAPPE_SITE_NAME=oropendola.local
FRAPPE_ENV=production

# -----------------
# Database
# -----------------
DB_HOST=localhost
DB_PORT=3306
DB_NAME=oropendola_db
DB_USER=frappe
DB_PASSWORD=your_secure_db_password
DB_ROOT_PASSWORD=your_mysql_root_password

# -----------------
# Redis
# -----------------
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE=redis://localhost:6379/1
REDIS_QUEUE=redis://localhost:6379/2
REDIS_PASSWORD=your_redis_password  # Optional

# -----------------
# Payment Gateways
# -----------------

# Primary Gateway
DEFAULT_PAYMENT_GATEWAY=razorpay

# Razorpay Configuration
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=your_razorpay_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

# PayU Configuration (Optional)
PAYU_MERCHANT_KEY=your_payu_merchant_key
PAYU_MERCHANT_SALT=your_payu_salt
PAYU_MODE=test

# -----------------
# AI Model Endpoints
# -----------------

# DeepSeek
DEEPSEEK_ENDPOINT=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_API_KEY=your_deepseek_api_key

# Grok (X.AI)
GROK_ENDPOINT=https://api.x.ai/v1/chat/completions
GROK_API_KEY=your_grok_api_key

# Claude (Anthropic)
CLAUDE_ENDPOINT=https://api.anthropic.com/v1/messages
CLAUDE_API_KEY=your_claude_api_key

# GPT-4 (OpenAI) - Optional
OPENAI_ENDPOINT=https://api.openai.com/v1/chat/completions
OPENAI_API_KEY=your_openai_api_key

# Gemini (Google) - Optional
GEMINI_ENDPOINT=https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent
GEMINI_API_KEY=your_gemini_api_key

# -----------------
# Routing Weights
# -----------------
# Adjust these to optimize model selection
WEIGHT_LATENCY=1.0      # Higher = prioritize faster models
WEIGHT_CAPACITY=0.5     # Higher = prioritize models with more capacity
WEIGHT_COST=1.5         # Higher = prioritize cheaper models
WEIGHT_PRIORITY=2.0     # Higher = prioritize subscription tier

# -----------------
# Security
# -----------------
ENCRYPTION_KEY=your_32_char_encryption_key_here
SESSION_TIMEOUT=3600
API_RATE_LIMIT_GLOBAL=1000  # Requests per hour

# -----------------
# Email (SMTP)
# -----------------
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=noreply@yourdomain.com

# -----------------
# Monitoring
# -----------------
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
GRAFANA_ENABLED=true
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD=your_grafana_password

# -----------------
# Logging
# -----------------
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
SENTRY_DSN=your_sentry_dsn  # Optional error tracking

# -----------------
# Application URLs
# -----------------
APP_URL=https://yourdomain.com
API_URL=https://api.yourdomain.com
ADMIN_URL=https://admin.yourdomain.com

# -----------------
# Deployment
# -----------------
ENVIRONMENT=production  # development, staging, production
WORKERS=4
ENABLE_SCHEDULER=true
ENABLE_BACKGROUND_WORKERS=true
```

## Installation Instructions

### 1. Install Dependencies

```bash
# Install Python packages
pip install razorpay redis prometheus-client requests

# For PayU support
# No additional package needed (uses direct HTTP API)
```

### 2. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit with your credentials
nano .env

# Or use script
chmod +x scripts/setup_env.sh
./scripts/setup_env.sh
```

### 3. Initialize Payment Gateways

```bash
# Test Razorpay connection
bench --site oropendola.local console
>>> from oropendola_ai.services.razorpay_gateway import get_gateway
>>> gateway = get_gateway()
>>> print("Razorpay configured successfully!")

# Test PayU connection
>>> from oropendola_ai.services.payu_gateway import get_payu_gateway
>>> gateway = get_payu_gateway()
>>> print("PayU configured successfully!")
```

### 4. Setup Webhooks

#### Razorpay Webhooks:
1. Login to Razorpay Dashboard
2. Go to Settings → Webhooks
3. Click "Add New Webhook"
4. Webhook URL: `https://yourdomain.com/api/method/oropendola_ai.services.razorpay_gateway.razorpay_webhook`
5. Select Events:
   - `payment.captured`
   - `payment.failed`
   - `payment.authorized`
6. Set Active: Yes
7. Copy the Webhook Secret to your `.env` file

#### PayU Webhooks:
PayU uses return URLs instead of webhooks:
- Success URL: `https://yourdomain.com/api/method/oropendola_ai.services.payu_gateway.payment_success`
- Failure URL: `https://yourdomain.com/api/method/oropendola_ai.services.payu_gateway.payment_failure`

These are automatically configured when creating payment requests.

## Testing Payment Gateways

### Test Razorpay

```python
# In Frappe console
from oropendola_ai.services.payment_manager import create_payment_order

# Create test invoice first
invoice = frappe.get_doc({
    "doctype": "AI Invoice",
    "customer": "Test Customer",
    "amount_due": 199,
    "currency": "INR",
    "status": "Draft"
})
invoice.insert()

# Create payment order
result = create_payment_order(invoice.name, gateway="razorpay")
print(result)
```

### Test PayU

```python
# Create payment request
result = create_payment_order(invoice.name, gateway="payu")
print(result)

# You'll get a payment URL and form data
# Open the URL in browser to test
```

### Razorpay Test Cards

```
Card Number: 4111 1111 1111 1111
CVV: Any 3 digits
Expiry: Any future date
```

### PayU Test Cards

```
Success Card: 5123 4567 8901 2346
CVV: 123
Expiry: 05/2026

Failure Card: 5123 4567 8901 2347
CVV: 123
Expiry: 05/2026
```

## Troubleshooting

### Razorpay Issues

**Error: "Invalid API Key"**
```bash
# Check credentials
echo $RAZORPAY_KEY_ID
echo $RAZORPAY_KEY_SECRET

# Verify in Razorpay dashboard
# Ensure using test keys in test mode
```

**Webhook not receiving events:**
1. Check webhook URL is publicly accessible
2. Verify SSL certificate is valid
3. Check webhook secret matches
4. Review Razorpay dashboard logs

### PayU Issues

**Error: "Invalid Hash"**
```bash
# Verify merchant salt is correct
# Hash generation is case-sensitive
# Check all parameters are in correct order
```

**Payment redirect not working:**
1. Ensure return URLs are publicly accessible
2. Check merchant key is correct
3. Verify mode (test/live) matches credentials

## Production Checklist

- [ ] Switch to live API keys (Razorpay/PayU)
- [ ] Configure production database
- [ ] Setup Redis with password
- [ ] Enable SSL/TLS for all endpoints
- [ ] Configure production webhooks
- [ ] Setup monitoring (Prometheus + Grafana)
- [ ] Configure email notifications
- [ ] Enable rate limiting
- [ ] Setup automated backups
- [ ] Configure CDN for static assets
- [ ] Test payment flows end-to-end
- [ ] Setup error tracking (Sentry)
- [ ] Configure log aggregation

## Security Best Practices

1. **Never commit `.env` file to version control**
2. **Use strong passwords** for all services
3. **Enable 2FA** on payment gateway accounts
4. **Rotate API keys** regularly (every 90 days)
5. **Monitor webhook failures** and retry failed payments
6. **Validate all payment signatures** before processing
7. **Use HTTPS only** for all payment endpoints
8. **Implement IP whitelisting** for admin endpoints
9. **Regular security audits** of payment flows
10. **PCI DSS compliance** for card data (if handling directly)

## Support

For payment gateway issues:
- **Razorpay:** support@razorpay.com | https://razorpay.com/support/
- **PayU:** merchantsupport@payu.in | https://payu.in/contact-us

For Oropendola AI issues:
- GitHub: https://github.com/your-org/oropendola_ai/issues
- Email: support@yourdomain.com
