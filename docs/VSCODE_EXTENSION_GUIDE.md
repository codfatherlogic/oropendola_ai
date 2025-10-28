# Oropendola AI - VS Code Extension Developer Guide

> **Complete Guide for Building and Integrating the Oropendola AI VS Code Extension**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [API Reference](#api-reference)
4. [Authentication](#authentication)
5. [Extension Development](#extension-development)
6. [API Endpoints](#api-endpoints)
7. [Code Examples](#code-examples)
8. [Testing](#testing)
9. [Publishing](#publishing)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The Oropendola AI VS Code Extension provides developers with AI-powered code assistance directly in their editor. It integrates with our backend API to deliver:

- **Intelligent Code Completion** - Context-aware suggestions
- **Code Explanation** - Natural language explanations of code
- **Code Refactoring** - Automated code improvements
- **Multi-Model Support** - GPT-4, Claude, Gemini Pro
- **Usage Tracking** - Monitor your API quota and costs

### Key Features

✅ Real-time code completions  
✅ Inline code explanations  
✅ Automated refactoring suggestions  
✅ Multi-language support (50+ languages)  
✅ Secure API key management  
✅ Usage statistics dashboard  
✅ Smart model routing  

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  VS Code Extension                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Code Lens   │  │  Completion  │  │  Commands    │  │
│  │  Provider    │  │  Provider    │  │  Handler     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│           │                │                │           │
│           └────────────────┴────────────────┘           │
│                         │                                │
│                   API Client                             │
└────────────────────────│────────────────────────────────┘
                         │
                    HTTPS/TLS
                         │
┌────────────────────────▼────────────────────────────────┐
│              Oropendola AI Backend                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ API Gateway  │→ │ Smart Router │→ │  AI Models   │  │
│  │ (Frappe)     │  │              │  │ (OpenAI etc) │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Data Flow

```mermaid
sequenceDiagram
    participant User
    participant VSCode
    participant Extension
    participant API
    participant SmartRouter
    participant AIModel

    User->>VSCode: Type code
    VSCode->>Extension: Trigger completion
    Extension->>API: POST /code_completion
    API->>API: Validate API key
    API->>SmartRouter: Route request
    SmartRouter->>AIModel: Select best model
    AIModel-->>SmartRouter: Generate completion
    SmartRouter-->>API: Return result
    API-->>Extension: Send completion
    Extension-->>VSCode: Display suggestion
    VSCode-->>User: Show completion
```

---

## 🔐 Authentication

### API Key Generation

Users must generate an API key from their dashboard:

**Step 1: Login to Dashboard**
```
https://oropendola.ai/my-profile
```

**Step 2: Generate API Key**
```
Dashboard → API Keys → Generate New Key
```

**Step 3: Copy API Key**
```
Format: oro_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### API Key Usage

**Extension Configuration:**
```json
{
  "oropendola.apiKey": "oro_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "oropendola.apiUrl": "https://oropendola.ai/api/method"
}
```

**Authentication Header:**
```http
Authorization: token oro_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Content-Type: application/json
```

---

## 🔌 API Reference

### Base URL

```
https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension
```

### Common Headers

```http
Authorization: token <API_KEY>
Content-Type: application/json
Accept: application/json
```

---

## 📡 API Endpoints

### 1. Health Check

**Check if the API is available**

```http
GET /health_check
```

**Response:**
```json
{
  "message": {
    "success": true,
    "status": "healthy",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

---

### 2. Validate API Key

**Verify your API key is valid**

```http
POST /validate_api_key
```

**Request Body:**
```json
{
  "api_key": "oro_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

**Response (Success):**
```json
{
  "message": {
    "valid": true,
    "user": "user@example.com",
    "plan": "Pro Plan",
    "quota_remaining": 4850,
    "quota_limit": 5000
  }
}
```

**Response (Invalid):**
```json
{
  "message": {
    "valid": false,
    "error": "Invalid API key"
  }
}
```

---

### 3. Code Completion

**Get AI-powered code completions**

```http
POST /code_completion
```

**Request Body:**
```json
{
  "prompt": "def calculate_fibonacci(n):",
  "language": "python",
  "context": "# Fibonacci calculator\n",
  "max_tokens": 150,
  "temperature": 0.2
}
```

**Parameters:**
- `prompt` (required): Code prefix to complete
- `language` (required): Programming language (python, javascript, etc.)
- `context` (optional): Surrounding code for better context
- `max_tokens` (optional): Maximum tokens to generate (default: 150)
- `temperature` (optional): Creativity level 0.0-1.0 (default: 0.2)

**Response:**
```json
{
  "message": {
    "success": true,
    "completion": "\n    if n <= 1:\n        return n\n    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)",
    "model_used": "gpt-4",
    "tokens_used": 45,
    "cost": 0.0018
  }
}
```

---

### 4. Code Explanation

**Get natural language explanation of code**

```http
POST /code_explanation
```

**Request Body:**
```json
{
  "code": "const debounce = (fn, delay) => {\n  let timeoutId;\n  return (...args) => {\n    clearTimeout(timeoutId);\n    timeoutId = setTimeout(() => fn(...args), delay);\n  };\n}",
  "language": "javascript"
}
```

**Response:**
```json
{
  "message": {
    "success": true,
    "explanation": "This is a debounce function that delays the execution of a callback function...",
    "key_concepts": [
      "Closure",
      "Higher-order function",
      "setTimeout",
      "Event throttling"
    ],
    "model_used": "gpt-4"
  }
}
```

---

### 5. Code Refactoring

**Get refactoring suggestions**

```http
POST /code_refactor
```

**Request Body:**
```json
{
  "code": "function add(a,b){return a+b}\nfunction sub(a,b){return a-b}",
  "language": "javascript",
  "refactor_type": "improve_readability"
}
```

**Refactor Types:**
- `improve_readability` - Better formatting and naming
- `optimize_performance` - Performance improvements
- `modernize_syntax` - Use modern language features
- `add_error_handling` - Add error checks
- `simplify` - Reduce complexity

**Response:**
```json
{
  "message": {
    "success": true,
    "refactored_code": "/**\n * Add two numbers\n */\nconst add = (a, b) => a + b;\n\n/**\n * Subtract two numbers\n */\nconst subtract = (a, b) => a - b;",
    "changes": [
      "Converted to ES6 arrow functions",
      "Added JSDoc comments",
      "Improved naming (sub → subtract)"
    ],
    "model_used": "gpt-4"
  }
}
```

---

### 6. Get Available Models

**List all AI models you have access to**

```http
GET /get_available_models
```

**Response:**
```json
{
  "message": {
    "success": true,
    "models": [
      {
        "name": "gpt-4",
        "provider": "openai",
        "capabilities": ["completion", "chat", "refactor"],
        "cost_per_1k_tokens": 0.03
      },
      {
        "name": "claude-3-sonnet",
        "provider": "anthropic",
        "capabilities": ["completion", "chat", "explanation"],
        "cost_per_1k_tokens": 0.015
      },
      {
        "name": "gemini-pro",
        "provider": "google",
        "capabilities": ["completion", "chat"],
        "cost_per_1k_tokens": 0.00025
      }
    ]
  }
}
```

---

### 7. Get Usage Statistics

**Get your current usage stats**

```http
GET /get_usage_stats
```

**Response:**
```json
{
  "message": {
    "success": true,
    "stats": {
      "today": {
        "requests": 150,
        "quota_limit": 5000,
        "quota_remaining": 4850,
        "tokens_used": 45000,
        "cost": 1.35
      },
      "this_month": {
        "requests": 3240,
        "tokens_used": 980000,
        "cost": 29.40
      },
      "plan": {
        "name": "Pro Plan",
        "daily_limit": 5000,
        "monthly_budget": 100.00,
        "budget_used": 29.40,
        "budget_remaining": 70.60
      }
    }
  }
}
```

---

### 8. Chat Completion

**Multi-turn conversation with AI**

```http
POST /chat_completion
```

**Request Body:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "How do I implement a binary search in Python?"
    }
  ],
  "model": "gpt-4",
  "max_tokens": 500
}
```

**Response:**
```json
{
  "message": {
    "success": true,
    "response": "Here's how to implement binary search in Python:\n\n```python\ndef binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    ...",
    "model_used": "gpt-4",
    "tokens_used": 234
  }
}
```

---

## 💻 Extension Development

### Project Structure

```
oropendola-vscode/
├── src/
│   ├── extension.ts          # Main entry point
│   ├── api/
│   │   ├── client.ts          # API client
│   │   └── types.ts           # TypeScript types
│   ├── providers/
│   │   ├── completion.ts      # Completion provider
│   │   ├── codeLens.ts        # CodeLens provider
│   │   └── hover.ts           # Hover provider
│   ├── commands/
│   │   ├── explain.ts         # Explain code command
│   │   ├── refactor.ts        # Refactor command
│   │   └── chat.ts            # Chat command
│   └── utils/
│       ├── config.ts          # Configuration
│       └── logger.ts          # Logging
├── package.json               # Extension manifest
├── tsconfig.json             # TypeScript config
└── README.md                 # Documentation
```

### package.json Configuration

```json
{
  "name": "oropendola-ai",
  "displayName": "Oropendola AI",
  "description": "AI-powered code assistant",
  "version": "1.0.0",
  "publisher": "codfatherlogic",
  "engines": {
    "vscode": "^1.80.0"
  },
  "categories": [
    "Programming Languages",
    "Machine Learning",
    "Other"
  ],
  "activationEvents": [
    "onLanguage:javascript",
    "onLanguage:typescript",
    "onLanguage:python",
    "onCommand:oropendola.explain",
    "onCommand:oropendola.refactor"
  ],
  "main": "./out/extension.js",
  "contributes": {
    "configuration": {
      "title": "Oropendola AI",
      "properties": {
        "oropendola.apiKey": {
          "type": "string",
          "default": "",
          "description": "Your Oropendola AI API key"
        },
        "oropendola.enableCompletion": {
          "type": "boolean",
          "default": true,
          "description": "Enable code completion"
        },
        "oropendola.preferredModel": {
          "type": "string",
          "enum": ["auto", "gpt-4", "claude-3-sonnet", "gemini-pro"],
          "default": "auto",
          "description": "Preferred AI model"
        }
      }
    },
    "commands": [
      {
        "command": "oropendola.explain",
        "title": "Explain Code",
        "category": "Oropendola AI"
      },
      {
        "command": "oropendola.refactor",
        "title": "Refactor Code",
        "category": "Oropendola AI"
      },
      {
        "command": "oropendola.chat",
        "title": "Open AI Chat",
        "category": "Oropendola AI"
      }
    ]
  }
}
```

---

## 📝 Code Examples

### API Client (TypeScript)

```typescript
// src/api/client.ts
import * as vscode from 'vscode';
import axios, { AxiosInstance } from 'axios';

export class OropendolaClient {
  private client: AxiosInstance;
  private apiKey: string;
  private baseUrl: string = 'https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension';

  constructor() {
    const config = vscode.workspace.getConfiguration('oropendola');
    this.apiKey = config.get('apiKey') || '';
    
    this.client = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Authorization': `token ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      timeout: 30000
    });
  }

  async validateApiKey(): Promise<boolean> {
    try {
      const response = await this.client.post('/validate_api_key', {
        api_key: this.apiKey
      });
      return response.data.message.valid;
    } catch (error) {
      return false;
    }
  }

  async getCodeCompletion(
    prompt: string,
    language: string,
    context?: string
  ): Promise<string> {
    const response = await this.client.post('/code_completion', {
      prompt,
      language,
      context,
      max_tokens: 150,
      temperature: 0.2
    });

    if (response.data.message.success) {
      return response.data.message.completion;
    }

    throw new Error('Completion failed');
  }

  async explainCode(code: string, language: string): Promise<string> {
    const response = await this.client.post('/code_explanation', {
      code,
      language
    });

    if (response.data.message.success) {
      return response.data.message.explanation;
    }

    throw new Error('Explanation failed');
  }

  async refactorCode(
    code: string,
    language: string,
    type: string = 'improve_readability'
  ): Promise<{ code: string; changes: string[] }> {
    const response = await this.client.post('/code_refactor', {
      code,
      language,
      refactor_type: type
    });

    if (response.data.message.success) {
      return {
        code: response.data.message.refactored_code,
        changes: response.data.message.changes
      };
    }

    throw new Error('Refactoring failed');
  }

  async getUsageStats(): Promise<any> {
    const response = await this.client.get('/get_usage_stats');
    return response.data.message.stats;
  }
}
```

### Completion Provider

```typescript
// src/providers/completion.ts
import * as vscode from 'vscode';
import { OropendolaClient } from '../api/client';

export class OropendolaCompletionProvider implements vscode.CompletionItemProvider {
  private client: OropendolaClient;

  constructor(client: OropendolaClient) {
    this.client = client;
  }

  async provideCompletionItems(
    document: vscode.TextDocument,
    position: vscode.Position,
    token: vscode.CancellationToken
  ): Promise<vscode.CompletionItem[]> {
    const linePrefix = document.lineAt(position).text.substr(0, position.character);
    
    // Get context (previous 10 lines)
    const startLine = Math.max(0, position.line - 10);
    const contextRange = new vscode.Range(startLine, 0, position.line, position.character);
    const context = document.getText(contextRange);

    try {
      const completion = await this.client.getCodeCompletion(
        linePrefix,
        document.languageId,
        context
      );

      const item = new vscode.CompletionItem(
        completion,
        vscode.CompletionItemKind.Snippet
      );
      
      item.detail = 'Oropendola AI';
      item.documentation = new vscode.MarkdownString('AI-generated completion');
      item.insertText = completion;

      return [item];
    } catch (error) {
      console.error('Completion error:', error);
      return [];
    }
  }
}
```

### Explain Code Command

```typescript
// src/commands/explain.ts
import * as vscode from 'vscode';
import { OropendolaClient } from '../api/client';

export async function explainCodeCommand(client: OropendolaClient) {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showErrorMessage('No active editor');
    return;
  }

  const selection = editor.selection;
  const code = editor.document.getText(selection);

  if (!code) {
    vscode.window.showErrorMessage('No code selected');
    return;
  }

  try {
    vscode.window.withProgress({
      location: vscode.ProgressLocation.Notification,
      title: 'Explaining code...',
      cancellable: false
    }, async () => {
      const explanation = await client.explainCode(
        code,
        editor.document.languageId
      );

      // Show in new editor
      const doc = await vscode.workspace.openTextDocument({
        content: explanation,
        language: 'markdown'
      });

      await vscode.window.showTextDocument(doc, vscode.ViewColumn.Beside);
    });
  } catch (error) {
    vscode.window.showErrorMessage(`Error: ${error.message}`);
  }
}
```

### Extension Activation

```typescript
// src/extension.ts
import * as vscode from 'vscode';
import { OropendolaClient } from './api/client';
import { OropendolaCompletionProvider } from './providers/completion';
import { explainCodeCommand } from './commands/explain';
import { refactorCodeCommand } from './commands/refactor';

export function activate(context: vscode.ExtensionContext) {
  console.log('Oropendola AI extension activated');

  const client = new OropendolaClient();

  // Validate API key on activation
  client.validateApiKey().then(valid => {
    if (!valid) {
      vscode.window.showWarningMessage(
        'Invalid Oropendola AI API key. Please configure in settings.'
      );
    }
  });

  // Register completion provider
  const completionProvider = vscode.languages.registerCompletionItemProvider(
    { scheme: 'file', language: '*' },
    new OropendolaCompletionProvider(client),
    '\n', ' ', '.'
  );

  // Register commands
  const explainCmd = vscode.commands.registerCommand(
    'oropendola.explain',
    () => explainCodeCommand(client)
  );

  const refactorCmd = vscode.commands.registerCommand(
    'oropendola.refactor',
    () => refactorCodeCommand(client)
  );

  context.subscriptions.push(
    completionProvider,
    explainCmd,
    refactorCmd
  );
}

export function deactivate() {}
```

---

## 🧪 Testing

### Test API Connection

```bash
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension/health_check \
  -H "Content-Type: application/json"
```

### Test API Key

```bash
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension/validate_api_key \
  -H "Authorization: token oro_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"api_key": "oro_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}'
```

### Test Code Completion

```bash
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension/code_completion \
  -H "Authorization: token oro_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "def fibonacci(n):",
    "language": "python",
    "max_tokens": 150
  }'
```

---

## 📦 Publishing

### Build Extension

```bash
# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Package extension
vsce package
```

### Publish to Marketplace

```bash
# Login
vsce login codfatherlogic

# Publish
vsce publish
```

---

## 🔧 Troubleshooting

### Common Issues

**1. API Key Invalid**
```
Error: Invalid API key
Solution: Generate new key from dashboard
```

**2. Rate Limit Exceeded**
```
Error: Daily quota exceeded
Solution: Upgrade plan or wait for quota reset
```

**3. Network Timeout**
```
Error: Request timeout
Solution: Check internet connection, increase timeout
```

**4. Model Not Available**
```
Error: Model not accessible
Solution: Check subscription plan includes model access
```

---

## 📞 Support

**Email:** hello@oropendola.ai  
**Documentation:** https://oropendola.ai/docs  
**Dashboard:** https://oropendola.ai/my-profile  

---

**Last Updated:** January 15, 2025  
**Version:** 1.0.0
# Oropendola AI - VS Code Extension Developer Guide

> **Complete Guide for Building and Integrating the Oropendola AI VS Code Extension**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [API Reference](#api-reference)
4. [Authentication](#authentication)
5. [Extension Development](#extension-development)
6. [API Endpoints](#api-endpoints)
7. [Code Examples](#code-examples)
8. [Testing](#testing)
9. [Publishing](#publishing)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The Oropendola AI VS Code Extension provides developers with AI-powered code assistance directly in their editor. It integrates with our backend API to deliver:

- **Intelligent Code Completion** - Context-aware suggestions
- **Code Explanation** - Natural language explanations of code
- **Code Refactoring** - Automated code improvements
- **Multi-Model Support** - GPT-4, Claude, Gemini Pro
- **Usage Tracking** - Monitor your API quota and costs

### Key Features

✅ Real-time code completions  
✅ Inline code explanations  
✅ Automated refactoring suggestions  
✅ Multi-language support (50+ languages)  
✅ Secure API key management  
✅ Usage statistics dashboard  
✅ Smart model routing  

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  VS Code Extension                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Code Lens   │  │  Completion  │  │  Commands    │  │
│  │  Provider    │  │  Provider    │  │  Handler     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│           │                │                │           │
│           └────────────────┴────────────────┘           │
│                         │                                │
│                   API Client                             │
└────────────────────────│────────────────────────────────┘
                         │
                    HTTPS/TLS
                         │
┌────────────────────────▼────────────────────────────────┐
│              Oropendola AI Backend                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ API Gateway  │→ │ Smart Router │→ │  AI Models   │  │
│  │ (Frappe)     │  │              │  │ (OpenAI etc) │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Data Flow

```mermaid
sequenceDiagram
    participant User
    participant VSCode
    participant Extension
    participant API
    participant SmartRouter
    participant AIModel

    User->>VSCode: Type code
    VSCode->>Extension: Trigger completion
    Extension->>API: POST /code_completion
    API->>API: Validate API key
    API->>SmartRouter: Route request
    SmartRouter->>AIModel: Select best model
    AIModel-->>SmartRouter: Generate completion
    SmartRouter-->>API: Return result
    API-->>Extension: Send completion
    Extension-->>VSCode: Display suggestion
    VSCode-->>User: Show completion
```

---

## 🔐 Authentication

### API Key Generation

Users must generate an API key from their dashboard:

**Step 1: Login to Dashboard**
```
https://oropendola.ai/my-profile
```

**Step 2: Generate API Key**
```
Dashboard → API Keys → Generate New Key
```

**Step 3: Copy API Key**
```
Format: oro_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### API Key Usage

**Extension Configuration:**
```json
{
  "oropendola.apiKey": "oro_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "oropendola.apiUrl": "https://oropendola.ai/api/method"
}
```

**Authentication Header:**
```http
Authorization: token oro_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Content-Type: application/json
```

---

## 🔌 API Reference

### Base URL

```
https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension
```

### Common Headers

```http
Authorization: token <API_KEY>
Content-Type: application/json
Accept: application/json
```

---

## 📡 API Endpoints

### 1. Health Check

**Check if the API is available**

```http
GET /health_check
```

**Response:**
```json
{
  "message": {
    "success": true,
    "status": "healthy",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

---

### 2. Validate API Key

**Verify your API key is valid**

```http
POST /validate_api_key
```

**Request Body:**
```json
{
  "api_key": "oro_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

**Response (Success):**
```json
{
  "message": {
    "valid": true,
    "user": "user@example.com",
    "plan": "Pro Plan",
    "quota_remaining": 4850,
    "quota_limit": 5000
  }
}
```

**Response (Invalid):**
```json
{
  "message": {
    "valid": false,
    "error": "Invalid API key"
  }
}
```

---

### 3. Code Completion

**Get AI-powered code completions**

```http
POST /code_completion
```

**Request Body:**
```json
{
  "prompt": "def calculate_fibonacci(n):",
  "language": "python",
  "context": "# Fibonacci calculator\n",
  "max_tokens": 150,
  "temperature": 0.2
}
```

**Parameters:**
- `prompt` (required): Code prefix to complete
- `language` (required): Programming language (python, javascript, etc.)
- `context` (optional): Surrounding code for better context
- `max_tokens` (optional): Maximum tokens to generate (default: 150)
- `temperature` (optional): Creativity level 0.0-1.0 (default: 0.2)

**Response:**
```json
{
  "message": {
    "success": true,
    "completion": "\n    if n <= 1:\n        return n\n    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)",
    "model_used": "gpt-4",
    "tokens_used": 45,
    "cost": 0.0018
  }
}
```

---

### 4. Code Explanation

**Get natural language explanation of code**

```http
POST /code_explanation
```

**Request Body:**
```json
{
  "code": "const debounce = (fn, delay) => {\n  let timeoutId;\n  return (...args) => {\n    clearTimeout(timeoutId);\n    timeoutId = setTimeout(() => fn(...args), delay);\n  };\n}",
  "language": "javascript"
}
```

**Response:**
```json
{
  "message": {
    "success": true,
    "explanation": "This is a debounce function that delays the execution of a callback function...",
    "key_concepts": [
      "Closure",
      "Higher-order function",
      "setTimeout",
      "Event throttling"
    ],
    "model_used": "gpt-4"
  }
}
```

---

### 5. Code Refactoring

**Get refactoring suggestions**

```http
POST /code_refactor
```

**Request Body:**
```json
{
  "code": "function add(a,b){return a+b}\nfunction sub(a,b){return a-b}",
  "language": "javascript",
  "refactor_type": "improve_readability"
}
```

**Refactor Types:**
- `improve_readability` - Better formatting and naming
- `optimize_performance` - Performance improvements
- `modernize_syntax` - Use modern language features
- `add_error_handling` - Add error checks
- `simplify` - Reduce complexity

**Response:**
```json
{
  "message": {
    "success": true,
    "refactored_code": "/**\n * Add two numbers\n */\nconst add = (a, b) => a + b;\n\n/**\n * Subtract two numbers\n */\nconst subtract = (a, b) => a - b;",
    "changes": [
      "Converted to ES6 arrow functions",
      "Added JSDoc comments",
      "Improved naming (sub → subtract)"
    ],
    "model_used": "gpt-4"
  }
}
```

---

### 6. Get Available Models

**List all AI models you have access to**

```http
GET /get_available_models
```

**Response:**
```json
{
  "message": {
    "success": true,
    "models": [
      {
        "name": "gpt-4",
        "provider": "openai",
        "capabilities": ["completion", "chat", "refactor"],
        "cost_per_1k_tokens": 0.03
      },
      {
        "name": "claude-3-sonnet",
        "provider": "anthropic",
        "capabilities": ["completion", "chat", "explanation"],
        "cost_per_1k_tokens": 0.015
      },
      {
        "name": "gemini-pro",
        "provider": "google",
        "capabilities": ["completion", "chat"],
        "cost_per_1k_tokens": 0.00025
      }
    ]
  }
}
```

---

### 7. Get Usage Statistics

**Get your current usage stats**

```http
GET /get_usage_stats
```

**Response:**
```json
{
  "message": {
    "success": true,
    "stats": {
      "today": {
        "requests": 150,
        "quota_limit": 5000,
        "quota_remaining": 4850,
        "tokens_used": 45000,
        "cost": 1.35
      },
      "this_month": {
        "requests": 3240,
        "tokens_used": 980000,
        "cost": 29.40
      },
      "plan": {
        "name": "Pro Plan",
        "daily_limit": 5000,
        "monthly_budget": 100.00,
        "budget_used": 29.40,
        "budget_remaining": 70.60
      }
    }
  }
}
```

---

### 8. Chat Completion

**Multi-turn conversation with AI**

```http
POST /chat_completion
```

**Request Body:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "How do I implement a binary search in Python?"
    }
  ],
  "model": "gpt-4",
  "max_tokens": 500
}
```

**Response:**
```json
{
  "message": {
    "success": true,
    "response": "Here's how to implement binary search in Python:\n\n```python\ndef binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    ...",
    "model_used": "gpt-4",
    "tokens_used": 234
  }
}
```

---

## 💻 Extension Development

### Project Structure

```
oropendola-vscode/
├── src/
│   ├── extension.ts          # Main entry point
│   ├── api/
│   │   ├── client.ts          # API client
│   │   └── types.ts           # TypeScript types
│   ├── providers/
│   │   ├── completion.ts      # Completion provider
│   │   ├── codeLens.ts        # CodeLens provider
│   │   └── hover.ts           # Hover provider
│   ├── commands/
│   │   ├── explain.ts         # Explain code command
│   │   ├── refactor.ts        # Refactor command
│   │   └── chat.ts            # Chat command
│   └── utils/
│       ├── config.ts          # Configuration
│       └── logger.ts          # Logging
├── package.json               # Extension manifest
├── tsconfig.json             # TypeScript config
└── README.md                 # Documentation
```

### package.json Configuration

```json
{
  "name": "oropendola-ai",
  "displayName": "Oropendola AI",
  "description": "AI-powered code assistant",
  "version": "1.0.0",
  "publisher": "codfatherlogic",
  "engines": {
    "vscode": "^1.80.0"
  },
  "categories": [
    "Programming Languages",
    "Machine Learning",
    "Other"
  ],
  "activationEvents": [
    "onLanguage:javascript",
    "onLanguage:typescript",
    "onLanguage:python",
    "onCommand:oropendola.explain",
    "onCommand:oropendola.refactor"
  ],
  "main": "./out/extension.js",
  "contributes": {
    "configuration": {
      "title": "Oropendola AI",
      "properties": {
        "oropendola.apiKey": {
          "type": "string",
          "default": "",
          "description": "Your Oropendola AI API key"
        },
        "oropendola.enableCompletion": {
          "type": "boolean",
          "default": true,
          "description": "Enable code completion"
        },
        "oropendola.preferredModel": {
          "type": "string",
          "enum": ["auto", "gpt-4", "claude-3-sonnet", "gemini-pro"],
          "default": "auto",
          "description": "Preferred AI model"
        }
      }
    },
    "commands": [
      {
        "command": "oropendola.explain",
        "title": "Explain Code",
        "category": "Oropendola AI"
      },
      {
        "command": "oropendola.refactor",
        "title": "Refactor Code",
        "category": "Oropendola AI"
      },
      {
        "command": "oropendola.chat",
        "title": "Open AI Chat",
        "category": "Oropendola AI"
      }
    ]
  }
}
```

---

## 📝 Code Examples

### API Client (TypeScript)

```typescript
// src/api/client.ts
import * as vscode from 'vscode';
import axios, { AxiosInstance } from 'axios';

export class OropendolaClient {
  private client: AxiosInstance;
  private apiKey: string;
  private baseUrl: string = 'https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension';

  constructor() {
    const config = vscode.workspace.getConfiguration('oropendola');
    this.apiKey = config.get('apiKey') || '';
    
    this.client = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Authorization': `token ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      timeout: 30000
    });
  }

  async validateApiKey(): Promise<boolean> {
    try {
      const response = await this.client.post('/validate_api_key', {
        api_key: this.apiKey
      });
      return response.data.message.valid;
    } catch (error) {
      return false;
    }
  }

  async getCodeCompletion(
    prompt: string,
    language: string,
    context?: string
  ): Promise<string> {
    const response = await this.client.post('/code_completion', {
      prompt,
      language,
      context,
      max_tokens: 150,
      temperature: 0.2
    });

    if (response.data.message.success) {
      return response.data.message.completion;
    }

    throw new Error('Completion failed');
  }

  async explainCode(code: string, language: string): Promise<string> {
    const response = await this.client.post('/code_explanation', {
      code,
      language
    });

    if (response.data.message.success) {
      return response.data.message.explanation;
    }

    throw new Error('Explanation failed');
  }

  async refactorCode(
    code: string,
    language: string,
    type: string = 'improve_readability'
  ): Promise<{ code: string; changes: string[] }> {
    const response = await this.client.post('/code_refactor', {
      code,
      language,
      refactor_type: type
    });

    if (response.data.message.success) {
      return {
        code: response.data.message.refactored_code,
        changes: response.data.message.changes
      };
    }

    throw new Error('Refactoring failed');
  }

  async getUsageStats(): Promise<any> {
    const response = await this.client.get('/get_usage_stats');
    return response.data.message.stats;
  }
}
```

### Completion Provider

```typescript
// src/providers/completion.ts
import * as vscode from 'vscode';
import { OropendolaClient } from '../api/client';

export class OropendolaCompletionProvider implements vscode.CompletionItemProvider {
  private client: OropendolaClient;

  constructor(client: OropendolaClient) {
    this.client = client;
  }

  async provideCompletionItems(
    document: vscode.TextDocument,
    position: vscode.Position,
    token: vscode.CancellationToken
  ): Promise<vscode.CompletionItem[]> {
    const linePrefix = document.lineAt(position).text.substr(0, position.character);
    
    // Get context (previous 10 lines)
    const startLine = Math.max(0, position.line - 10);
    const contextRange = new vscode.Range(startLine, 0, position.line, position.character);
    const context = document.getText(contextRange);

    try {
      const completion = await this.client.getCodeCompletion(
        linePrefix,
        document.languageId,
        context
      );

      const item = new vscode.CompletionItem(
        completion,
        vscode.CompletionItemKind.Snippet
      );
      
      item.detail = 'Oropendola AI';
      item.documentation = new vscode.MarkdownString('AI-generated completion');
      item.insertText = completion;

      return [item];
    } catch (error) {
      console.error('Completion error:', error);
      return [];
    }
  }
}
```

### Explain Code Command

```typescript
// src/commands/explain.ts
import * as vscode from 'vscode';
import { OropendolaClient } from '../api/client';

export async function explainCodeCommand(client: OropendolaClient) {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showErrorMessage('No active editor');
    return;
  }

  const selection = editor.selection;
  const code = editor.document.getText(selection);

  if (!code) {
    vscode.window.showErrorMessage('No code selected');
    return;
  }

  try {
    vscode.window.withProgress({
      location: vscode.ProgressLocation.Notification,
      title: 'Explaining code...',
      cancellable: false
    }, async () => {
      const explanation = await client.explainCode(
        code,
        editor.document.languageId
      );

      // Show in new editor
      const doc = await vscode.workspace.openTextDocument({
        content: explanation,
        language: 'markdown'
      });

      await vscode.window.showTextDocument(doc, vscode.ViewColumn.Beside);
    });
  } catch (error) {
    vscode.window.showErrorMessage(`Error: ${error.message}`);
  }
}
```

### Extension Activation

```typescript
// src/extension.ts
import * as vscode from 'vscode';
import { OropendolaClient } from './api/client';
import { OropendolaCompletionProvider } from './providers/completion';
import { explainCodeCommand } from './commands/explain';
import { refactorCodeCommand } from './commands/refactor';

export function activate(context: vscode.ExtensionContext) {
  console.log('Oropendola AI extension activated');

  const client = new OropendolaClient();

  // Validate API key on activation
  client.validateApiKey().then(valid => {
    if (!valid) {
      vscode.window.showWarningMessage(
        'Invalid Oropendola AI API key. Please configure in settings.'
      );
    }
  });

  // Register completion provider
  const completionProvider = vscode.languages.registerCompletionItemProvider(
    { scheme: 'file', language: '*' },
    new OropendolaCompletionProvider(client),
    '\n', ' ', '.'
  );

  // Register commands
  const explainCmd = vscode.commands.registerCommand(
    'oropendola.explain',
    () => explainCodeCommand(client)
  );

  const refactorCmd = vscode.commands.registerCommand(
    'oropendola.refactor',
    () => refactorCodeCommand(client)
  );

  context.subscriptions.push(
    completionProvider,
    explainCmd,
    refactorCmd
  );
}

export function deactivate() {}
```

---

## 🧪 Testing

### Test API Connection

```bash
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension/health_check \
  -H "Content-Type: application/json"
```

### Test API Key

```bash
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension/validate_api_key \
  -H "Authorization: token oro_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"api_key": "oro_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}'
```

### Test Code Completion

```bash
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension/code_completion \
  -H "Authorization: token oro_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "def fibonacci(n):",
    "language": "python",
    "max_tokens": 150
  }'
```

---

## 📦 Publishing

### Build Extension

```bash
# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Package extension
vsce package
```

### Publish to Marketplace

```bash
# Login
vsce login codfatherlogic

# Publish
vsce publish
```

---

## 🔧 Troubleshooting

### Common Issues

**1. API Key Invalid**
```
Error: Invalid API key
Solution: Generate new key from dashboard
```

**2. Rate Limit Exceeded**
```
Error: Daily quota exceeded
Solution: Upgrade plan or wait for quota reset
```

**3. Network Timeout**
```
Error: Request timeout
Solution: Check internet connection, increase timeout
```

**4. Model Not Available**
```
Error: Model not accessible
Solution: Check subscription plan includes model access
```

---

## 📞 Support

**Email:** hello@oropendola.ai  
**Documentation:** https://oropendola.ai/docs  
**Dashboard:** https://oropendola.ai/my-profile  

---

**Last Updated:** January 15, 2025  
**Version:** 1.0.0
