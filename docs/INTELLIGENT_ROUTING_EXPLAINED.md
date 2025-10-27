# 🧠 Oropendola AI - Intelligent Routing System Explained

## Overview

Oropendola's **Agent Mode** uses a sophisticated multi-factor routing algorithm that automatically selects the optimal AI model for each request. This document explains how all factors work together to make intelligent routing decisions.

---

## 📊 Routing Decision Factors

### 1. **Cost Weight** (Plan-Based)

**What it is:** A multiplier assigned to each model within a specific AI Plan that influences model selection preference.

**Purpose:** Controls how frequently each model is selected based on the user's subscription tier and cost optimization goals.

**How it works:**
- Higher Cost Weight = Model is more likely to be selected
- Lower Cost Weight = Model is less likely to be selected
- Configured per plan (Free, Pro, Enterprise)

**Example from your screenshot:**

| Model | Cost Weight | Meaning |
|-------|-------------|---------|
| DeepSeek | 60 | **Highly preferred** - 6x more likely than others |
| Grok | 10 | Standard preference |
| Gemini | 10 | Standard preference |
| Claude | 10 | Standard preference |
| GPT-4 | 10 | Standard preference |

This configuration prioritizes **DeepSeek** (most cost-effective) while keeping other premium models available.

---

### 2. **Context Window Size**

**What it is:** Maximum number of tokens (words/characters) the model can process in a single request.

**From your screenshot:** Context Window Size = **1** (likely in thousands, so 1K tokens for this trial plan)

**How it's used in routing:**

```python
# Check if request exceeds model's context window
if estimated_tokens > model.max_context_window:
    # Exclude this model from selection
    continue
else:
    # Model can handle this request
    eligible_models.append(model)
```

**Model Context Windows:**
- DeepSeek: 128,000 tokens
- Grok: 131,072 tokens
- Claude: 200,000 tokens ⭐ (Largest)
- GPT-4: 128,000 tokens
- Gemini: 1,000,000 tokens ⭐⭐ (Massive)

**Routing Logic:**
1. Estimate request token count
2. Filter out models that can't handle the request size
3. Only route to models with sufficient context window

---

### 3. **Rate Limit (Queries Per Second - QPS)**

**What it is:** Maximum number of requests allowed per second for a user's subscription.

**Purpose:** Prevents API abuse and ensures fair usage across all users.

**How it's enforced:**

```python
# Token Bucket Algorithm (in model_router.py)
def check_rate_limit(subscription_id, qps_limit):
    bucket_key = f"ratelimit:{subscription_id}"
    
    # Check if tokens available
    current_tokens = redis.get(bucket_key) or qps_limit
    
    if current_tokens > 0:
        redis.decr(bucket_key)  # Consume one token
        redis.expire(bucket_key, 1)  # Reset after 1 second
        return True  # Request allowed
    else:
        return False  # Rate limit exceeded
```

**Routing Impact:**
- If rate limit exceeded: Request is rejected with `429 Rate Limit Exceeded`
- If within limit: Request proceeds to model selection

**Example:**
- Free Plan: 10 QPS (10 requests/second)
- Pro Plan: 60 QPS
- Enterprise: 300 QPS

---

### 4. **Requests Limit Per Day (Daily Quota)**

**What it is:** Maximum total number of requests allowed per day.

**Purpose:** Controls monthly costs and prevents quota exhaustion.

**How it's enforced:**

```python
def check_quota(subscription_id, cost_units):
    today = time.strftime("%Y-%m-%d")
    quota_key = f"quota:{subscription_id}:{today}"
    
    remaining = redis.get(quota_key)
    
    if remaining is None:
        # Initialize from database
        subscription = frappe.get_doc("AI Subscription", subscription_id)
        remaining = subscription.daily_quota_limit
        redis.setex(quota_key, 86400, remaining)  # 24 hours
    
    if remaining == -1:
        return True  # Unlimited quota
    
    if remaining < cost_units:
        return False  # Quota exceeded
    
    # Consume quota
    redis.decr(quota_key, cost_units)
    return True
```

**Routing Impact:**
- **Before routing:** Check if user has remaining quota
- If quota exceeded: Return `429 Quota Exceeded` error
- If quota available: Deduct cost and proceed

**Cost Units:**
Different requests consume different amounts:
- Simple query: 1 unit
- Code completion: 2 units
- Large context: 5+ units

---

### 5. **Priority Score**

**What it is:** A numerical value (0-100) assigned to a subscription that influences routing speed and quality.

**From your screenshot:** The plan has a Priority Score configuration (visible in the header: "Higher priority gets faster routing and queue processing")

**How it's used:**

```python
def get_routing_score(model, subscription_priority):
    WEIGHT_PRIORITY = 2.0
    
    # Higher subscription priority boosts routing score
    priority_score = WEIGHT_PRIORITY * subscription_priority
    
    total_score += priority_score
    return total_score
```

**Priority Levels:**
- **Free Plan:** Priority = 0-10 (Basic service)
- **Pro Plan:** Priority = 50-70 (Faster routing)
- **Enterprise:** Priority = 90-100 (Top priority, best models)

**Impact on Routing:**
1. **Model Selection:** Higher priority users get access to premium models more often
2. **Queue Processing:** High priority requests jump the queue
3. **Fallback Behavior:** Better fallback model selection for premium users

---

## 🎯 The Complete Routing Algorithm

Here's how all factors work together:

### Step 1: Pre-Flight Checks

```python
def route_request(api_key, payload):
    # 1. Validate API Key
    subscription = validate_api_key(api_key)
    if not subscription:
        return {"error": "Invalid API key", "status": 401}
    
    # 2. Check Rate Limit (QPS)
    if not check_rate_limit(subscription.id, subscription.rate_limit_qps):
        return {"error": "Rate limit exceeded", "status": 429}
    
    # 3. Check Daily Quota
    if not check_quota(subscription.id, cost_units):
        return {"error": "Daily quota exceeded", "status": 429}
    
    # Proceed to model selection...
```

### Step 2: Get Eligible Models

```python
def get_eligible_models(subscription, request_tokens):
    # Get models allowed by plan
    allowed_models = subscription.plan.get_allowed_models()
    
    eligible_models = []
    for model_name in allowed_models:
        model = frappe.get_doc("AI Model Profile", model_name)
        
        # Check if model is active and healthy
        if not model.is_active or model.health_status == "Down":
            continue
        
        # Check context window capacity
        if request_tokens > model.max_context_window:
            continue
        
        # Check concurrent request limit
        if get_current_requests(model) >= model.max_concurrent_requests:
            continue
        
        eligible_models.append(model)
    
    return eligible_models
```

### Step 3: Calculate Routing Scores

```python
def calculate_routing_score(model, subscription):
    # Weight factors (configurable)
    WEIGHT_LATENCY = 1.0
    WEIGHT_CAPACITY = 0.5
    WEIGHT_COST = 1.5          # ⭐ Cost is heavily weighted
    WEIGHT_PRIORITY = 2.0       # ⭐ Priority has highest weight
    WEIGHT_SUCCESS = 0.3
    WEIGHT_COST_WEIGHT = 3.0    # ⭐ NEW: Plan's cost weight
    
    # 1. Latency Score (lower latency = higher score)
    latency_score = WEIGHT_LATENCY * (1.0 / (model.avg_latency_ms + 1))
    
    # 2. Capacity Score (model's capability rating)
    capacity_score = WEIGHT_CAPACITY * (model.capacity_score / 100.0)
    
    # 3. Cost Score (lower cost = higher score)
    cost_score = -WEIGHT_COST * float(model.cost_per_unit)
    
    # 4. Priority Score (from subscription)
    priority_score = WEIGHT_PRIORITY * subscription.priority_score
    
    # 5. Success Rate Score (reliability)
    success_score = WEIGHT_SUCCESS * (model.success_rate / 100.0)
    
    # 6. Cost Weight Score (from Plan's Model Access) ⭐⭐⭐
    plan_cost_weight = get_plan_cost_weight(subscription.plan, model.name)
    cost_weight_score = WEIGHT_COST_WEIGHT * (plan_cost_weight / 10.0)
    
    # 7. Health penalty
    health_penalty = -10 if model.health_status == "Degraded" else 0
    
    # Total Score
    total_score = (latency_score + capacity_score + cost_score + 
                   priority_score + success_score + cost_weight_score + 
                   health_penalty)
    
    return total_score
```

### Step 4: Select Best Model

```python
def select_best_model(eligible_models, subscription):
    scored_models = []
    
    for model in eligible_models:
        score = calculate_routing_score(model, subscription)
        scored_models.append({
            "model": model,
            "score": score
        })
    
    # Sort by score (highest first)
    scored_models.sort(key=lambda x: x["score"], reverse=True)
    
    # Return the winner
    return scored_models[0]["model"]
```

---

## 💡 Real-World Example

Let's walk through a complete routing decision:

### Scenario

**User:** VS Code user with "1 Day Trial" plan (from your screenshot)  
**Request:** "Explain Python decorators" (estimated 500 tokens)  
**Time:** 3:00 PM, 50 requests made today (quota: 100/day)  

### Plan Configuration

From your screenshot:
- **Priority Score:** Medium (let's say 30)
- **Rate Limit:** 10 QPS
- **Daily Quota:** 100 requests/day
- **Context Window:** 1,000 tokens
- **Model Access:**
  - DeepSeek: Cost Weight 60 ✅
  - Grok: Cost Weight 10 ✅
  - Gemini: Cost Weight 10 ✅
  - Claude: Cost Weight 10 ✅
  - GPT-4: Cost Weight 10 ✅

### Step-by-Step Routing

#### 1. Pre-Flight Checks ✅

```
✓ API Key: Valid
✓ Rate Limit: 2 requests this second (limit: 10) → PASS
✓ Daily Quota: 50 used, 50 remaining → PASS
✓ Request Size: 500 tokens → PASS
```

#### 2. Get Eligible Models

```
Checking DeepSeek:
  ✓ Is Active: Yes
  ✓ Health Status: Up
  ✓ Context Window: 128,000 > 500 → PASS
  ✓ Concurrent Requests: 5/20 → PASS
  → DeepSeek is ELIGIBLE

Checking Grok:
  ✓ Is Active: Yes
  ✓ Health Status: Up
  ✓ Context Window: 131,072 > 500 → PASS
  ✓ Concurrent Requests: 8/15 → PASS
  → Grok is ELIGIBLE

Checking Claude:
  ✓ Is Active: Yes
  ✓ Health Status: Up
  ✓ Context Window: 200,000 > 500 → PASS
  ✓ Concurrent Requests: 12/25 → PASS
  → Claude is ELIGIBLE

Checking GPT-4:
  ✓ Is Active: Yes
  ✓ Health Status: Up
  ✓ Context Window: 128,000 > 500 → PASS
  ✓ Concurrent Requests: 15/30 → PASS
  → GPT-4 is ELIGIBLE

Checking Gemini:
  ✓ Is Active: Yes
  ✓ Health Status: Up
  ✓ Context Window: 1,000,000 > 500 → PASS
  ✓ Concurrent Requests: 10/20 → PASS
  → Gemini is ELIGIBLE

All 5 models are eligible!
```

#### 3. Calculate Scores

```python
DeepSeek Score:
  Latency:       1.0 * (1/101) = 0.0099
  Capacity:      0.5 * (85/100) = 0.425
  Cost:          -1.5 * 0.0014 = -0.0021
  Priority:      2.0 * 30 = 60.0
  Success:       0.3 * (98/100) = 0.294
  Cost Weight:   3.0 * (60/10) = 18.0  ⭐ HUGE BOOST
  Health:        0
  TOTAL:         78.73  ⭐⭐⭐

Grok Score:
  Latency:       1.0 * (1/121) = 0.0083
  Capacity:      0.5 * (80/100) = 0.4
  Cost:          -1.5 * 0.002 = -0.003
  Priority:      2.0 * 30 = 60.0
  Success:       0.3 * (95/100) = 0.285
  Cost Weight:   3.0 * (10/10) = 3.0
  Health:        0
  TOTAL:         63.69

Claude Score:
  Latency:       1.0 * (1/91) = 0.011
  Capacity:      0.5 * (95/100) = 0.475
  Cost:          -1.5 * 0.003 = -0.0045
  Priority:      2.0 * 30 = 60.0
  Success:       0.3 * (99/100) = 0.297
  Cost Weight:   3.0 * (10/10) = 3.0
  Health:        0
  TOTAL:         63.78

GPT-4 Score:
  Latency:       1.0 * (1/111) = 0.009
  Capacity:      0.5 * (90/100) = 0.45
  Cost:          -1.5 * 0.03 = -0.045
  Priority:      2.0 * 30 = 60.0
  Success:       0.3 * (97/100) = 0.291
  Cost Weight:   3.0 * (10/10) = 3.0
  Health:        0
  TOTAL:         63.71

Gemini Score:
  Latency:       1.0 * (1/106) = 0.0094
  Capacity:      0.5 * (88/100) = 0.44
  Cost:          -1.5 * 0.00125 = -0.00188
  Priority:      2.0 * 30 = 60.0
  Success:       0.3 * (96/100) = 0.288
  Cost Weight:   3.0 * (10/10) = 3.0
  Health:        0
  TOTAL:         63.74
```

#### 4. Selection Result

```
Ranking:
  1. DeepSeek: 78.73  ⭐ WINNER
  2. Claude:   63.78
  3. Gemini:   63.74
  4. GPT-4:    63.71
  5. Grok:     63.69

Selected Model: DeepSeek
Reason: Highest Cost Weight (60) dramatically boosted its score
```

#### 5. Response to User

```json
{
  "status": 200,
  "model": "DeepSeek",
  "agent_mode": true,
  "auto_selected": true,
  "selection_reason": "Optimized for cost (Weight: 60), performance, and availability",
  "response": {
    "content": "Python decorators are...",
    "tokens_used": 450
  },
  "latency_ms": 850,
  "total_time_ms": 900,
  "routing_score": 78.73,
  "quota_remaining": 49
}
```

---

## 🔄 Dynamic Cost Weight Adjustment

### Different Plans, Different Priorities

**Free Plan (Cost-Conscious):**
```
DeepSeek: 80  ⭐⭐⭐ (Maximize cost savings)
Grok: 15
Gemini: 10
Claude: 5
GPT-4: 1      (Minimize expensive calls)
```

**Pro Plan (Balanced):**
```
DeepSeek: 60  ⭐⭐
Grok: 40
Claude: 50    ⭐
Gemini: 45
GPT-4: 20
```

**Enterprise Plan (Quality-First):**
```
DeepSeek: 30
Grok: 40
Claude: 80    ⭐⭐⭐
GPT-4: 90     ⭐⭐⭐ (Best quality available)
Gemini: 70    ⭐⭐
```

---

## 📈 Benefits of This System

### For Users (VS Code Extension)

✅ **No Model Selection Needed** - Just send requests  
✅ **Cost-Optimized** - Automatically uses cheaper models when possible  
✅ **High Quality** - Premium users get better models  
✅ **Fair Usage** - Quota and rate limits prevent abuse  
✅ **Transparent** - Response shows which model was used and why  

### For System (Backend)

✅ **Load Balancing** - Distributes requests across models  
✅ **Cost Control** - Minimizes infrastructure costs  
✅ **Failover** - Automatically switches if a model is down  
✅ **Scalable** - Can add/remove models without API changes  
✅ **Configurable** - Adjust weights per plan dynamically  

---

## 🎓 Summary

The Oropendola routing algorithm uses a **multi-dimensional scoring system** where:

1. **Cost Weight** (from AI Plan) - Primary cost optimization factor
2. **Priority Score** (from Subscription) - Service tier differentiation
3. **Context Window** - Request size compatibility filter
4. **Rate Limit** - Per-second traffic control
5. **Daily Quota** - Long-term usage management
6. **Model Attributes** - Latency, capacity, success rate, cost per unit
7. **Health Status** - Real-time availability

**Formula:**
```
Routing Score = (
    Latency Score +
    Capacity Score +
    Cost Score +
    Priority Score +
    Success Rate Score +
    Cost Weight Score ⭐ [Most Important] +
    Health Penalty
)
```

The model with the **highest total score wins** and processes the request.

This creates an intelligent, self-optimizing system that balances:
- **User Experience** (fast, quality responses)
- **Cost Efficiency** (use cheaper models when appropriate)
- **Fairness** (enforce quotas and rate limits)
- **Reliability** (avoid overloaded or unhealthy models)

---

**Result:** VS Code users get a seamless AI experience without worrying about model selection! 🚀
