# Oropendola AI - VS Code Extension API Documentation

Complete API reference for building VS Code extensions with Oropendola AI.

---

## Base URL

```
https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.
```

---

## Authentication

All API endpoints (except health_check) require an API key. Pass it as a parameter or in the request body.

### Get Your API Key

1. Log in to Oropendola AI dashboard
2. Navigate to **API Keys**
3. Create a new key for "VS Code Extension"
4. Copy and store securely

---

## API Endpoints

### 1. **Health Check**

Check if the API is available.

**Endpoint:** `health_check`

**Method:** `GET` or `POST`

**Authentication:** None required

**Example:**

```bash
curl https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.health_check
```

**Response:**

```json
{
  "status": "healthy",
  "service": "Oropendola AI",
  "version": "1.0.0",
  "timestamp": "2025-10-27 22:00:00"
}
```

---

### 2. **Validate API Key**

Validate your API key and get subscription details.

**Endpoint:** `validate_api_key`

**Method:** `POST`

**Parameters:**
- `api_key` (string, required): Your API key

**Example:**

```bash
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.validate_api_key \
  -H "Content-Type: application/json" \
  -d '{"api_key": "your-api-key-here"}'
```

**Response (Success):**

```json
{
  "valid": true,
  "subscription_id": "SUB-00001",
  "customer": "John Doe",
  "plan_id": "Pro Plan",
  "daily_quota_remaining": 9500,
  "allowed_models": ["GPT-4", "Claude", "Gemini"],
  "status": "Active"
}
```

**Response (Invalid):**

```json
{
  "valid": false,
  "error": "Invalid or expired API key"
}
```

---

### 3. **Chat Completion**

Send chat messages and get AI responses.

**Endpoint:** `chat_completion`

**Method:** `POST`

**Parameters:**
- `api_key` (string, required): Your API key
- `messages` (string/JSON, required): Array of message objects
- `model` (string, optional): Preferred model name
- `temperature` (float, optional): Creativity level (0.0 - 2.0)
- `max_tokens` (int, optional): Maximum response tokens

**Example:**

```bash
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.chat_completion \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your-api-key-here",
    "messages": "[{\"role\":\"user\",\"content\":\"Explain async/await in JavaScript\"}]",
    "model": "GPT-4",
    "temperature": 0.7
  }'
```

**Response:**

```json
{
  "status": 200,
  "model": "GPT-4",
  "response": {
    "content": "Async/await is a modern JavaScript feature...",
    "tokens_used": 150
  },
  "latency_ms": 1200,
  "total_time_ms": 1250
}
```

---

### 4. **Code Completion**

Get AI-powered code completions.

**Endpoint:** `code_completion`

**Method:** `POST`

**Parameters:**
- `api_key` (string, required): Your API key
- `code` (string, required): Incomplete code
- `language` (string, required): Programming language
- `context` (string, optional): Additional context

**Example:**

```bash
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.code_completion \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your-api-key-here",
    "code": "function fibonacci(n) {",
    "language": "javascript",
    "context": "Implement recursive fibonacci function"
  }'
```

**Response:**

```json
{
  "status": 200,
  "model": "GPT-4",
  "response": {
    "content": "function fibonacci(n) {\n  if (n <= 1) return n;\n  return fibonacci(n - 1) + fibonacci(n - 2);\n}",
    "tokens_used": 85
  }
}
```

---

### 5. **Code Explanation**

Get explanations for code snippets.

**Endpoint:** `code_explanation`

**Method:** `POST`

**Parameters:**
- `api_key` (string, required): Your API key
- `code` (string, required): Code to explain
- `language` (string, required): Programming language

**Example:**

```bash
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.code_explanation \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your-api-key-here",
    "code": "const result = await Promise.all(promises);",
    "language": "javascript"
  }'
```

**Response:**

```json
{
  "status": 200,
  "response": {
    "content": "This code uses Promise.all() to execute multiple promises concurrently..."
  }
}
```

---

### 6. **Code Refactoring**

Get refactored code based on instructions.

**Endpoint:** `code_refactor`

**Method:** `POST`

**Parameters:**
- `api_key` (string, required): Your API key
- `code` (string, required): Code to refactor
- `language` (string, required): Programming language
- `instructions` (string, required): Refactoring instructions

**Example:**

```bash
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.code_refactor \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your-api-key-here",
    "code": "if (x == 1) { return true; } else { return false; }",
    "language": "javascript",
    "instructions": "Simplify this conditional"
  }'
```

**Response:**

```json
{
  "status": 200,
  "response": {
    "content": "return x === 1;"
  }
}
```

---

### 7. **Get Available Models**

List AI models available for your subscription.

**Endpoint:** `get_available_models`

**Method:** `POST`

**Parameters:**
- `api_key` (string, required): Your API key

**Example:**

```bash
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.get_available_models \
  -H "Content-Type: application/json" \
  -d '{"api_key": "your-api-key-here"}'
```

**Response:**

```json
{
  "models": [
    {
      "model_name": "GPT-4",
      "provider": "OpenAI",
      "capacity_score": 90,
      "max_context_window": 128000,
      "supports_streaming": true
    },
    {
      "model_name": "Claude",
      "provider": "Anthropic",
      "capacity_score": 95,
      "max_context_window": 200000,
      "supports_streaming": true
    }
  ],
  "default_model": "GPT-4"
}
```

---

### 8. **Get Usage Statistics**

Get your current usage and quota information.

**Endpoint:** `get_usage_stats`

**Method:** `POST`

**Parameters:**
- `api_key` (string, required): Your API key

**Example:**

```bash
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.get_usage_stats \
  -H "Content-Type: application/json" \
  -d '{"api_key": "your-api-key-here"}'
```

**Response:**

```json
{
  "daily_quota_limit": 10000,
  "daily_quota_remaining": 9500,
  "daily_quota_used": 500,
  "status": "Active",
  "plan": "Pro Plan"
}
```

---

## VS Code Extension Example

### TypeScript/JavaScript Example

```typescript
import axios from 'axios';

const BASE_URL = 'https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension';
const API_KEY = 'your-api-key-here';

// Chat Completion
async function chatCompletion(messages: any[]) {
  const response = await axios.post(`${BASE_URL}.chat_completion`, {
    api_key: API_KEY,
    messages: JSON.stringify(messages),
    model: 'GPT-4'
  });
  
  return response.data;
}

// Code Completion
async function codeCompletion(code: string, language: string) {
  const response = await axios.post(`${BASE_URL}.code_completion`, {
    api_key: API_KEY,
    code: code,
    language: language
  });
  
  return response.data;
}

// Usage Example
const messages = [
  { role: 'user', content: 'Explain closures in JavaScript' }
];

chatCompletion(messages).then(result => {
  console.log(result.response.content);
});
```

### Python Example

```python
import requests
import json

BASE_URL = 'https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension'
API_KEY = 'your-api-key-here'

def chat_completion(messages, model='GPT-4'):
    response = requests.post(
        f'{BASE_URL}.chat_completion',
        json={
            'api_key': API_KEY,
            'messages': json.dumps(messages),
            'model': model
        }
    )
    return response.json()

# Usage
messages = [
    {'role': 'user', 'content': 'Explain list comprehensions in Python'}
]

result = chat_completion(messages)
print(result['response']['content'])
```

---

## Error Handling

All endpoints return standard HTTP status codes:

- `200` - Success
- `401` - Unauthorized (invalid API key)
- `429` - Rate limit or quota exceeded
- `500` - Internal server error
- `503` - Service unavailable

**Error Response Format:**

```json
{
  "status": 429,
  "error": "Rate limit exceeded",
  "message": "You have exceeded your requests per second limit"
}
```

---

## Rate Limits

Rate limits depend on your subscription plan:

- **Free Plan**: 10 requests/minute
- **Pro Plan**: 60 requests/minute
- **Enterprise Plan**: 300 requests/minute

---

## Best Practices

1. **Cache API Key**: Store securely in VS Code settings
2. **Handle Errors**: Implement retry logic with exponential backoff
3. **Monitor Quota**: Check remaining quota before requests
4. **Use Streaming**: Enable streaming for real-time responses
5. **Model Selection**: Let the system auto-select for best performance

---

## Support

- **Documentation**: https://docs.oropendola.ai
- **Email**: support@oropendola.ai
- **Discord**: https://discord.gg/oropendola-ai

---

## Quick Start Checklist

- [ ] Get API key from dashboard
- [ ] Test with `health_check` endpoint
- [ ] Validate API key with `validate_api_key`
- [ ] Make first `chat_completion` request
- [ ] Check usage with `get_usage_stats`
- [ ] Implement error handling
- [ ] Build your VS Code extension!

---

**Happy Coding! 🚀**
