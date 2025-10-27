# 🚀 Oropendola AI - VS Code Extension API Quick Reference

## Base URL
```
https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.
```

---

## 📋 API Endpoints Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `health_check` | GET/POST | ❌ No | Check API health |
| `validate_api_key` | POST | ✅ Yes | Validate API key |
| `chat_completion` | POST | ✅ Yes | Chat with AI |
| `code_completion` | POST | ✅ Yes | Complete code |
| `code_explanation` | POST | ✅ Yes | Explain code |
| `code_refactor` | POST | ✅ Yes | Refactor code |
| `get_available_models` | POST | ✅ Yes | List available models |
| `get_usage_stats` | POST | ✅ Yes | Get usage/quota info |
| `get_api_keys` | POST | ✅ Yes | List user's API keys |
| `create_api_key` | POST | ✅ Yes | Create new API key |

---

## 🔑 Quick Examples

### 1. Health Check
```bash
curl https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.health_check
```

### 2. Chat Completion
```bash
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.chat_completion \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "YOUR_API_KEY",
    "messages": "[{\"role\":\"user\",\"content\":\"Hello!\"}]"
  }'
```

### 3. Code Completion
```bash
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.code_completion \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "YOUR_API_KEY",
    "code": "function add(a, b) {",
    "language": "javascript"
  }'
```

### 4. Get Usage
```bash
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.get_usage_stats \
  -H "Content-Type: application/json" \
  -d '{"api_key": "YOUR_API_KEY"}'
```

---

## 📝 TypeScript Integration

```typescript
const OROPENDOLA_BASE = 'https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

async function chatCompletion(apiKey: string, messages: Message[]) {
  const response = await fetch(`${OROPENDOLA_BASE}.chat_completion`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      api_key: apiKey,
      messages: JSON.stringify(messages)
    })
  });
  
  return await response.json();
}
```

---

## 🎯 Common Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | ✅ | Your API key |
| `messages` | string/JSON | Varies | Chat messages array |
| `model` | string | ❌ | Preferred model |
| `code` | string | Varies | Code snippet |
| `language` | string | Varies | Programming language |
| `temperature` | float | ❌ | Creativity (0.0-2.0) |
| `max_tokens` | int | ❌ | Max response tokens |

---

## ⚡ Response Format

**Success:**
```json
{
  "status": 200,
  "model": "GPT-4",
  "response": {
    "content": "...",
    "tokens_used": 150
  },
  "latency_ms": 1200
}
```

**Error:**
```json
{
  "status": 429,
  "error": "Rate limit exceeded",
  "message": "..."
}
```

---

## 🛡️ Error Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `401` | Invalid API key |
| `429` | Rate/quota limit |
| `500` | Server error |
| `503` | Service unavailable |

---

## 📊 Available Models

- **GPT-4** (OpenAI) - General purpose, multimodal
- **Claude** (Anthropic) - Analysis, coding
- **Gemini** (Google) - Long context, multimodal
- **DeepSeek** (DeepSeek) - Reasoning, chat
- **Grok** (xAI) - Realtime, chat

---

## 🔗 Full Documentation

📖 [Complete API Docs](./VSCODE_EXTENSION_API.md)

---

**Questions?** support@oropendola.ai
