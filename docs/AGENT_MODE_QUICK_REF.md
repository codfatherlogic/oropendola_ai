# 🤖 Agent Mode - Quick Reference

## 🎯 One Simple Rule

**Users don't select models. Oropendola does it automatically.**

---

## 🚀 Primary Endpoint

```
https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.agent
```

### Usage

```bash
curl -X POST .../agent \
  -d '{"api_key":"KEY", "prompt":"Your question"}'
```

### Response

```json
{
  "status": 200,
  "model": "Claude",          // Auto-selected
  "agent_mode": true,
  "selection_reason": "Optimized for cost, performance, and availability",
  "response": { "content": "..." }
}
```

---

## 📋 All Endpoints (Agent Mode)

| Endpoint | Purpose | Model Selection |
|----------|---------|-----------------|
| `agent` | General AI queries | ✅ Automatic |
| `code_completion` | Complete code | ✅ Automatic |
| `code_explanation` | Explain code | ✅ Automatic |
| `code_refactor` | Refactor code | ✅ Automatic |

**All specialized endpoints use Agent Mode internally**

---

## 💡 Quick Examples

### 1. Simple Question

```javascript
fetch(`${BASE_URL}.agent`, {
  method: 'POST',
  body: JSON.stringify({
    api_key: API_KEY,
    prompt: "What is a closure?"
  })
})
```

### 2. Code Completion

```javascript
fetch(`${BASE_URL}.code_completion`, {
  method: 'POST',
  body: JSON.stringify({
    api_key: API_KEY,
    code: "function add(a, b) {",
    language: "javascript"
  })
})
```

### 3. Code Explanation

```javascript
fetch(`${BASE_URL}.code_explanation`, {
  method: 'POST',
  body: JSON.stringify({
    api_key: API_KEY,
    code: "async/await code here",
    language: "javascript"
  })
})
```

---

## 🎛️ How It Works

```
Your Request 
    ↓
Oropendola Backend
    ↓
Evaluates: Cost Weights + Performance + Availability
    ↓
Selects: Best Model (DeepSeek/Grok/Claude/GPT-4/Gemini)
    ↓
Returns: Response + Model Used
```

---

## ✅ Routing Factors

1. **Cost Weight** (from your plan)
2. **Performance Score** (model capability)
3. **Availability** (health status)
4. **Latency** (response time)
5. **Success Rate** (reliability)

---

## 📊 Available Models

- **DeepSeek** - Low cost, good reasoning
- **Grok** - Real-time, medium cost
- **Claude** - Excellent for analysis/coding
- **GPT-4** - Premium quality, higher cost
- **Gemini** - Long context, multimodal

**You never choose - Oropendola picks the best one!**

---

## 🔑 Essential Endpoints

```bash
# Health Check
curl .../health_check

# Validate Key
curl -X POST .../validate_api_key -d '{"api_key":"KEY"}'

# Usage Stats
curl -X POST .../get_usage_stats -d '{"api_key":"KEY"}'
```

---

## ⚡ Rate Limits

| Plan | Rate Limit |
|------|------------|
| Free | 10/min |
| Pro | 60/min |
| Enterprise | 300/min |

---

## 💻 TypeScript Integration

```typescript
const API = 'https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension';

async function ask(prompt: string) {
  const res = await fetch(`${API}.agent`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({api_key: KEY, prompt})
  });
  
  return await res.json();
}
```

---

## 📖 Full Documentation

[Complete Agent Mode API Docs](./VSCODE_AGENT_MODE_API.md)

---

**Simple. Intelligent. Automatic.** 🚀
