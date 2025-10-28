# Oropendola AI VS Code Extension - Quick Start

> **Fast track guide to building the VS Code extension**

---

## 🚀 5-Minute Setup

### 1. Get API Key
```
1. Visit https://oropendola.ai/my-profile
2. Click "Generate API Key"
3. Copy key: oro_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2. Test API
```bash
curl https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension/health_check
```

### 3. Create Extension
```bash
npm install -g yo generator-code
yo code
# Select: New Extension (TypeScript)
# Name: oropendola-ai
```

---

## 📡 API Endpoints Cheat Sheet

**Base URL:**
```
https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension
```

**Auth Header:**
```http
Authorization: token oro_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Core Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health_check` | GET | API health |
| `/validate_api_key` | POST | Verify key |
| `/code_completion` | POST | Get completions |
| `/code_explanation` | POST | Explain code |
| `/code_refactor` | POST | Refactor code |
| `/get_available_models` | GET | List models |
| `/get_usage_stats` | GET | Usage stats |
| `/chat_completion` | POST | AI chat |

---

## 💻 Essential Code Snippets

### API Client
```typescript
import axios from 'axios';

const client = axios.create({
  baseURL: 'https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension',
  headers: {
    'Authorization': `token ${apiKey}`,
    'Content-Type': 'application/json'
  }
});

// Code completion
const completion = await client.post('/code_completion', {
  prompt: 'def fibonacci(n):',
  language: 'python',
  max_tokens: 150
});
```

### Completion Provider
```typescript
export class CompletionProvider implements vscode.CompletionItemProvider {
  async provideCompletionItems(doc, pos) {
    const code = doc.getText(new vscode.Range(pos.line - 10, 0, pos.line, pos.character));
    const response = await client.post('/code_completion', {
      prompt: code,
      language: doc.languageId
    });
    return [new vscode.CompletionItem(response.data.message.completion)];
  }
}
```

### Extension Activation
```typescript
export function activate(context: vscode.ExtensionContext) {
  const provider = vscode.languages.registerCompletionItemProvider(
    { scheme: 'file' },
    new CompletionProvider(),
    '\n', ' '
  );
  context.subscriptions.push(provider);
}
```

---

## 🧪 Test Commands

### Health Check
```bash
curl https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension/health_check
```

### Validate Key
```bash
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension/validate_api_key \
  -H "Authorization: token oro_xxx" \
  -H "Content-Type: application/json" \
  -d '{"api_key": "oro_xxx"}'
```

### Code Completion
```bash
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension/code_completion \
  -H "Authorization: token oro_xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "function add(a, b) {",
    "language": "javascript",
    "max_tokens": 100
  }'
```

---

## 📦 Package.json Minimal

```json
{
  "name": "oropendola-ai",
  "displayName": "Oropendola AI",
  "version": "1.0.0",
  "engines": { "vscode": "^1.80.0" },
  "activationEvents": ["onLanguage:*"],
  "main": "./out/extension.js",
  "contributes": {
    "configuration": {
      "properties": {
        "oropendola.apiKey": {
          "type": "string",
          "description": "API Key"
        }
      }
    },
    "commands": [
      {
        "command": "oropendola.explain",
        "title": "Explain Code"
      }
    ]
  }
}
```

---

## 🎯 Request/Response Examples

### Code Completion Request
```json
{
  "prompt": "def calculate_sum(numbers):",
  "language": "python",
  "context": "# Math utilities\n",
  "max_tokens": 150,
  "temperature": 0.2
}
```

### Code Completion Response
```json
{
  "message": {
    "success": true,
    "completion": "\n    total = 0\n    for num in numbers:\n        total += num\n    return total",
    "model_used": "gpt-4",
    "tokens_used": 28,
    "cost": 0.00084
  }
}
```

### Explain Code Request
```json
{
  "code": "const debounce = (fn, ms) => { let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); }; }",
  "language": "javascript"
}
```

### Explain Code Response
```json
{
  "message": {
    "success": true,
    "explanation": "This is a debounce function that delays execution...",
    "key_concepts": ["Closure", "setTimeout", "Higher-order function"],
    "model_used": "gpt-4"
  }
}
```

---

## 🔧 Common Issues

| Issue | Solution |
|-------|----------|
| Invalid API key | Regenerate from dashboard |
| Quota exceeded | Upgrade plan or wait for reset |
| Network timeout | Increase timeout to 30s |
| Model not available | Check plan includes model |

---

## 📚 Full Documentation

- **Complete Guide:** `VSCODE_EXTENSION_GUIDE.md`
- **API Reference:** `VSCODE_EXTENSION_API.md`
- **Architecture:** `ARCHITECTURE.md`

---

## 🎓 Resources

- Dashboard: https://oropendola.ai/my-profile
- API Docs: https://oropendola.ai/docs
- Support: hello@oropendola.ai

---

**Ready to build!** 🚀
