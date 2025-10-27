# 🧠 Smart Routing Modes - Complete Guide

## Overview

Oropendola AI now features **Smart Routing Modes** that dynamically switch between AI models (DeepSeek, Grok, Claude, GPT-4, Gemini) based on:

✅ **Task Complexity** - Automatic detection from prompt content  
✅ **Session Continuity** - Maintains model consistency for coherent conversations  
✅ **Cost Optimization** - Budget-aware routing (~INR 1,200/month target)  
✅ **Real-time Performance** - Adapts to system load and model health  

---

## 🎯 Four Routing Modes

### 1. **Auto Mode** (Recommended)

**Philosophy**: Smart balance between cost and quality

**Logic**:
- Analyzes task complexity automatically
- Routes simple tasks to DeepSeek (cheap)
- Routes reasoning tasks to Grok (fast)
- Routes complex tasks to Claude (high quality)
- Routes multimodal tasks to Gemini (1M context)

**Cost Impact**: ~INR 1,000/month  
**Best For**: General development (80%+ of use cases)

**Model Distribution**:
```
Simple Tasks (80%):     DeepSeek 80%, Others 20%
Reasoning Tasks (10%):  Grok 40%, DeepSeek 40%, Others 20%
Complex Tasks (7%):     Claude 50%, GPT-4 25%, Others 25%
Multimodal (3%):        Gemini 70%, Others 30%
```

---

### 2. **Performance Mode**

**Philosophy**: Quality-first, cost-second

**Logic**:
- Prioritizes Claude 4 Sonnet for all complex tasks
- Falls back to GPT-4 if Claude is rate-limited
- Ignores DeepSeek unless absolutely necessary

**Cost Impact**: ~INR 2,000-3,000/month (over budget)  
**Best For**: High-stakes coding, production code reviews  
**Limitation**: Use for 5-10% of requests max

**Model Distribution**:
```
All Tasks: Claude 60%, GPT-4 30%, Gemini 8%, Grok 2%, DeepSeek 0%
```

---

### 3. **Efficient Mode**

**Philosophy**: Cost-first, quality-second

**Logic**:
- Defaults to DeepSeek for 90% of tasks
- Uses Grok-fast only for reasoning under high load
- Avoids Claude/Gemini unless critical

**Cost Impact**: ~INR 700-900/month  
**Best For**: Unit tests, documentation, daily Q&A  
**Target**: 80%+ of routing for budget compliance

**Model Distribution**:
```
Simple Tasks (90%):     DeepSeek 90%, Grok 8%, Others 2%
Reasoning Tasks (10%):  DeepSeek 60%, Grok 35%, Others 5%
```

---

### 4. **Lite Mode**

**Philosophy**: Free-tier only

**Logic**:
- Uses Grok free tier (via X/grok.com) if available
- Falls back to DeepSeek's cheapest tier
- Minimal token usage, no premium models

**Cost Impact**: ~$0-INR 200/month  
**Best For**: Quick queries, one-off snippets  
**Limitation**: 5% of requests or free tier quotas

**Model Distribution**:
```
All Tasks: Grok 70% (free), DeepSeek 30%, Others 0%
```

---

## 🔍 Task Complexity Detection

### Automatic Analysis

The system analyzes prompts using pattern matching and token counting:

#### **Simple** (→ DeepSeek)
- **Patterns**: "what is", "explain briefly", "todo", "list", "quick"
- **Token Count**: < 5,000 tokens
- **Prompt Length**: < 100 characters
- **Examples**:
  - "What is a closure?"
  - "Create a TODO list"
  - "Explain briefly what async/await does"

#### **Reasoning** (→ Grok)
- **Patterns**: "debug", "test", "unit test", "algorithm", "logic"
- **Token Count**: 5,000 - 10,000 tokens
- **Prompt Length**: 100-500 characters
- **Examples**:
  - "Debug this function"
  - "Write unit tests for this class"
  - "Calculate the time complexity"

#### **Complex** (→ Claude)
- **Patterns**: "review", "architecture", "design pattern", "refactor", "optimize"
- **Token Count**: > 10,000 tokens
- **Prompt Length**: > 500 characters
- **Examples**:
  - "Review this pull request"
  - "Design a microservices architecture"
  - "Refactor this monolithic codebase"

#### **Multimodal** (→ Gemini)
- **Patterns**: "visualize", "diagram", "chart", "image", "screenshot"
- **Special**: Includes images/files or requires visual output
- **Examples**:
  - "Create a Mermaid diagram"
  - "Visualize this architecture"
  - "Generate a flowchart"

---

## 🔗 Session Continuity

### How It Works

1. **Session ID**: VS Code extension generates unique session ID per conversation
2. **Context Correlation**: System compares consecutive prompts
3. **Model Caching**: If similarity > 70%, reuses same model
4. **Topic Shift Detection**: If similarity < 70%, re-evaluates model choice

### Benefits

✅ **Coherent Conversations**: Model maintains context understanding  
✅ **Better Responses**: Follow-up questions get relevant answers  
✅ **Cost Savings**: Reduces context switching overhead  

### Example

```
Session Start:
  User: "Explain Python decorators" 
  → Complexity: Simple → DeepSeek selected
  → Cached: session:abc123:model = "DeepSeek"

Follow-up (correlation: 85%):
  User: "Show me an example with @property"
  → Same topic detected → DeepSeek reused

Topic Shift (correlation: 30%):
  User: "Now review this entire codebase"
  → New topic detected → Re-evaluate → Claude selected
```

---

## 💰 Cost Optimization

### Budget Target: INR 1,200/month (~$14.29 USD)

#### Token Allocation

```
Total Requests: 7,200/month (10/hour, 24/7)
Average Tokens: 4,800 tokens/request
Total Tokens: 34.56M tokens/month
```

#### Blended Cost Model

| Mode | % Usage | Cost/M Tokens | Monthly Cost |
|------|---------|---------------|--------------|
| **Efficient** (DeepSeek) | 80% | $0.14 | ~$3.87 |
| **Auto** (Mixed) | 15% | $0.50 | ~$2.59 |
| **Performance** (Claude) | 5% | $3.00 | ~$5.18 |
| **Infrastructure** | - | - | ~INR 300 |
| **TOTAL** | 100% | ~$0.35 avg | **~INR 1,270** |

#### Cost Mitigation Strategies

1. **Increase Cache Hit Rate**: 70% → 75% saves ~INR 150
2. **Batch Claude/Gemini**: Delay non-urgent tasks → 50% savings
3. **Cap Performance Mode**: Limit to 5% of requests
4. **Use Grok Free Tier**: For Lite mode queries

---

## 🚀 API Usage

### Basic Agent Call (Auto Mode)

```bash
curl -X POST https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.agent \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "YOUR_API_KEY",
    "prompt": "Explain closures in JavaScript",
    "mode": "auto"
  }'
```

### With Session Continuity

```bash
curl -X POST .../agent \
  -d '{
    "api_key": "YOUR_API_KEY",
    "prompt": "Show me an example",
    "mode": "auto",
    "session_id": "vscode_session_12345"
  }'
```

### Performance Mode (Complex Task)

```bash
curl -X POST .../agent \
  -d '{
    "api_key": "YOUR_API_KEY",
    "prompt": "Review this entire microservices architecture and suggest improvements",
    "mode": "performance"
  }'
```

### Efficient Mode (Simple Task)

```bash
curl -X POST .../agent \
  -d '{
    "api_key": "YOUR_API_KEY",
    "prompt": "What is a Python list comprehension?",
    "mode": "efficient"
  }'
```

---

## 📊 Response Format

```json
{
  "status": 200,
  "model": "Claude",
  "agent_mode": true,
  "auto_selected": true,
  "smart_mode": "auto",
  "task_complexity": "complex",
  "selection_reason": "Optimized for complex tasks in auto mode",
  "mode_weights_applied": {
    "Claude": 50,
    "GPT-4": 25,
    "Gemini": 15,
    "Grok": 8,
    "DeepSeek": 2
  },
  "response": {
    "content": "...",
    "tokens_used": 450
  },
  "latency_ms": 1200,
  "total_time_ms": 1250
}
```

---

## 🔬 Feature Integration

### 1. **Unlimited Requests** (Efficient Mode)

```typescript
// VS Code Extension
for (let i = 0; i < 1000; i++) {
  await agent(prompt, { mode: "efficient" });
  // Routes to DeepSeek (fast, cheap)
}
```

**Cost**: ~INR 150 (10% Grok-fast for variety)

---

### 2. **Unit Test Generation** (Efficient Mode)

```typescript
const testCode = await agent(
  `Generate pytest tests for: ${code}`,
  { mode: "efficient" }
);
// Routes to Grok-fast (good at code generation)
```

**Cost**: ~INR 100 (10% routing)

---

### 3. **Code Review** (Performance Mode)

```typescript
const review = await agent(
  `Review this PR: ${prDiff}`,
  { mode: "performance" }
);
// Routes to Claude (best for reviews)
```

**Cost**: ~INR 200 (5% routing, high quality)

---

### 4. **Project Visualization** (Auto Mode)

```typescript
const diagram = await agent(
  `Create architecture diagram for: ${codebase}`,
  { mode: "auto" }
);
// Detects "diagram" keyword → Routes to Gemini
```

**Cost**: ~INR 100 (5% Gemini multimodal)

---

### 5. **1M Context Window** (Auto Mode)

```typescript
const analysis = await agent(
  `Analyze entire codebase: ${largeCodebase}`,
  { mode: "auto" }
);
// Detects large token count → Routes to Gemini
```

**Cost**: ~INR 100 (5% Gemini long context)

---

### 6. **Smart TODO List** (Efficient Mode)

```typescript
const todos = await agent(
  `Generate smart TODOs from: ${projectFiles}`,
  { mode: "efficient", session_id: sessionId }
);
// Routes to DeepSeek (simple task)
```

**Cost**: ~INR 50 (80% DeepSeek)

---

## 📈 Real-World Example

### Scenario: Full Day Development Session

```
09:00 AM - Quick Question
  Prompt: "What is async/await?"
  Mode: auto → Detects: simple → Routes to: DeepSeek
  Cost: $0.0001

10:30 AM - Unit Test Request
  Prompt: "Write tests for UserService"
  Mode: auto → Detects: reasoning → Routes to: Grok
  Cost: $0.0005

12:00 PM - Architecture Discussion
  Prompt: "Design microservices for e-commerce"
  Mode: performance → Forced: complex → Routes to: Claude
  Cost: $0.015

02:00 PM - Code Review
  Prompt: "Review PR #123"
  Mode: auto → Detects: complex → Routes to: Claude
  Cost: $0.012

04:00 PM - Visualization
  Prompt: "Create system diagram"
  Mode: auto → Detects: multimodal → Routes to: Gemini
  Cost: $0.008

06:00 PM - Quick Fix
  Prompt: "Debug this function"
  Mode: efficient → Forced: simple → Routes to: DeepSeek
  Cost: $0.0002

Total Day Cost: ~$0.036 (~INR 3)
Monthly (30 days): ~INR 90 (well under budget!)
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Smart Routing Weights (optional overrides)
WEIGHT_LATENCY=1.0
WEIGHT_CAPACITY=0.5
WEIGHT_COST=1.5
WEIGHT_PRIORITY=2.0
WEIGHT_COST_WEIGHT=3.0

# Session Continuity
SESSION_TTL=3600  # 1 hour
CORRELATION_THRESHOLD=0.7

# Budget Controls
MONTHLY_BUDGET_INR=1200
ALERT_THRESHOLD=0.9  # Alert at 90% budget
```

---

## 🎯 Best Practices

### 1. **Use Auto Mode by Default**
```typescript
// ✅ Good
await agent(prompt, { mode: "auto" });

// ❌ Avoid
await agent(prompt, { mode: "performance" });  // Expensive!
```

### 2. **Enable Session Continuity**
```typescript
// ✅ Good - maintains context
const sessionId = generateSessionId();
await agent(prompt1, { session_id: sessionId });
await agent(prompt2, { session_id: sessionId });

// ❌ Avoid - loses context
await agent(prompt1);
await agent(prompt2);
```

### 3. **Use Performance Mode Sparingly**
```typescript
// ✅ Good - only for critical tasks
if (isProductionCodeReview) {
  await agent(prompt, { mode: "performance" });
} else {
  await agent(prompt, { mode: "auto" });
}
```

### 4. **Batch Non-Urgent Tasks**
```typescript
// ✅ Good - reduces costs
const batch = await Promise.all([
  agent(task1, { mode: "efficient" }),
  agent(task2, { mode: "efficient" })
]);
```

---

## 📚 Summary

| Mode | Cost | Quality | Use Case | % Recommended |
|------|------|---------|----------|---------------|
| **Auto** | Medium | High | General dev | 80% |
| **Performance** | High | Highest | Critical code | 5% |
| **Efficient** | Low | Medium | Bulk tasks | 15% |
| **Lite** | Minimal | Basic | Quick queries | Optional |

**Recommended Distribution**: 80% Auto, 15% Efficient, 5% Performance

**Expected Monthly Cost**: ~INR 1,000-1,300 (within budget!)

---

## 🚀 Next Steps

1. ✅ Smart Routing implemented
2. ✅ Task complexity detection ready
3. ✅ Session continuity enabled
4. ⏳ Budget tracking dashboard (TODO)
5. ⏳ Real-time cost monitoring (TODO)

---

**Experience intelligent, budget-aware AI routing!** 🎉
