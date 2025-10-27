# 🎨 Visual Authentication Flow - Oropendola AI

## Quick Visual Reference for User Sign-In Process

---

## 🔄 **Complete Flow: Registration to API Usage**

```mermaid
graph TB
    Start([User Visits Website]) --> Signup[Sign Up Form]
    Signup --> CreateUser[Frappe Creates User]
    CreateUser --> EmailVerif[Email Verification Sent]
    EmailVerif --> UserClick[User Clicks Verify Link]
    UserClick --> EnableUser[User Account Enabled]
    
    EnableUser --> Hook{Hook Triggered:<br/>after_insert}
    Hook --> CheckType{User Type?}
    CheckType -->|Website User| CreateSub[Create AI Subscription]
    CheckType -->|System User| Skip[Skip - Admin User]
    
    CreateSub --> InitSub[Initialize Subscription]
    InitSub --> SetDates[Set Start/End Dates]
    SetDates --> SetQuota[Set Daily Quota]
    SetQuota --> SetBudget[Initialize Monthly Budget]
    SetBudget --> GenKey[Generate API Key]
    
    GenKey --> GenRandom[Generate Random 32-byte Key]
    GenRandom --> HashKey[SHA-256 Hash]
    HashKey --> CreateKeyDoc[Create AI API Key Doc]
    CreateKeyDoc --> CacheKey[Cache Raw Key - 5 min]
    
    CacheKey --> UserLogin[User Logs In]
    UserLogin --> ValidateCreds[Validate Credentials]
    ValidateCreds --> CreateSession[Create Session]
    CreateSession --> SetCookie[Set HTTP-only Cookie]
    SetCookie --> Dashboard[Redirect to Dashboard]
    
    Dashboard --> GetKey[Request API Key]
    GetKey --> CheckCache{Cache Available?}
    CheckCache -->|Yes| ShowKey[Display Full API Key]
    CheckCache -->|No| ShowPrefix[Show Prefix Only]
    
    ShowKey --> UserCopy[User Copies Key]
    UserCopy --> VSCode[Paste to VS Code]
    VSCode --> APIRequest[API Request with Key]
    
    APIRequest --> ValidateKey[Validate API Key Hash]
    ValidateKey --> CheckQuota{Quota Available?}
    CheckQuota -->|Yes| CheckBudget{Budget Available?}
    CheckQuota -->|No| QuotaError[Quota Exceeded Error]
    CheckBudget -->|Yes| Process[Process Request]
    CheckBudget -->|No| BudgetError[Budget Exceeded Error]
    
    Process --> UpdateUsage[Update Usage Stats]
    UpdateUsage --> LogUsage[Log to AI Usage Log]
    LogUsage --> Response[Return Response]
    
    Response --> End([End])
    QuotaError --> End
    BudgetError --> End
    Skip --> End
    ShowPrefix --> End
    
    style Start fill:#e1f5e1
    style End fill:#ffe1e1
    style CreateSub fill:#fff3cd
    style GenKey fill:#cfe2ff
    style UserLogin fill:#d1ecf1
    style Process fill:#d4edda
```

---

## 🏗️ **System Architecture**

```mermaid
graph LR
    subgraph "User Layer"
        U[Frappe User]
    end
    
    subgraph "Subscription Layer"
        S[AI Subscription]
        P[AI Plan]
    end
    
    subgraph "Security Layer"
        K[AI API Key]
        H[SHA-256 Hash]
    end
    
    subgraph "Tracking Layer"
        L[AI Usage Log]
        Q[Quota Tracker]
        B[Budget Tracker]
    end
    
    subgraph "Cache Layer"
        R[Redis Cache]
        SK[Session Store]
    end
    
    U -->|user field| S
    S -->|plan field| P
    S -->|api_key_link| K
    K -->|stores| H
    K -->|cached in| R
    S -->|tracks in| L
    S -->|manages| Q
    S -->|manages| B
    U -->|session in| SK
    
    style U fill:#e7f3ff
    style S fill:#fff3cd
    style K fill:#d4edda
    style R fill:#f8d7da
```

---

## 🔐 **Authentication & Authorization States**

```mermaid
stateDiagram-v2
    [*] --> Guest
    Guest --> Registered : Sign Up
    Registered --> PendingVerification : Email Sent
    PendingVerification --> Verified : Click Email Link
    Verified --> SubscriptionCreated : Hook Triggered
    SubscriptionCreated --> APIKeyGenerated : Auto-Create Key
    APIKeyGenerated --> LoggedOut : Verification Complete
    
    LoggedOut --> LoggedIn : Login with Password
    LoggedIn --> Authenticated : Session Created
    Authenticated --> APIKeyRetrieved : Get API Key
    APIKeyRetrieved --> ActiveUser : Key Stored
    
    ActiveUser --> MakingRequests : Use API
    MakingRequests --> QuotaChecked : Validate Quota
    QuotaChecked --> BudgetChecked : Validate Budget
    BudgetChecked --> Processing : Both OK
    Processing --> MakingRequests : Continue Usage
    
    QuotaChecked --> QuotaExceeded : No Quota
    BudgetChecked --> BudgetExceeded : No Budget
    
    QuotaExceeded --> [*]
    BudgetExceeded --> [*]
    
    ActiveUser --> LoggedOut : Logout/Session Timeout
    LoggedOut --> [*]
```

---

## 📊 **Data Flow: Login to API Request**

```mermaid
sequenceDiagram
    autonumber
    
    actor User
    participant Browser
    participant Frappe
    participant Session
    participant Subscription
    participant APIKey
    participant Redis
    participant VSCode
    
    rect rgb(230, 245, 255)
        Note over User,Frappe: Login Phase
        User->>Browser: Enter email/password
        Browser->>Frappe: POST /login
        Frappe->>Frappe: Validate BCrypt hash
        Frappe->>Session: Create session
        Session->>Redis: Store session data
        Frappe->>Browser: Set HTTP-only cookie
        Browser->>User: Redirect to /dashboard
    end
    
    rect rgb(255, 243, 205)
        Note over User,APIKey: API Key Retrieval Phase
        User->>Browser: Click "Get API Key"
        Browser->>Frappe: GET /api/user_api.get_my_api_key
        Frappe->>Session: Validate session cookie
        Session->>Frappe: Session valid
        Frappe->>Subscription: Get subscription by user
        Subscription->>APIKey: Get linked API key
        APIKey->>Redis: Check cache for raw key
        Redis->>APIKey: Return raw key (if < 5 min)
        APIKey->>Frappe: Return key data
        Frappe->>Browser: JSON response
        Browser->>User: Display API key
        User->>User: Copy to clipboard
    end
    
    rect rgb(212, 237, 218)
        Note over User,VSCode: API Usage Phase
        User->>VSCode: Paste API key
        VSCode->>VSCode: Store in secure storage
        VSCode->>Frappe: POST /api/chat_completion<br/>Authorization: Bearer <key>
        Frappe->>Frappe: Hash provided key (SHA-256)
        Frappe->>APIKey: Check hash in database
        APIKey->>Subscription: Get subscription
        Subscription->>Subscription: Check quota
        Subscription->>Subscription: Check budget
        Subscription->>Frappe: Validation passed
        Frappe->>Frappe: Process AI request
        Frappe->>Subscription: Update usage
        Subscription->>Subscription: Log to AI Usage Log
        Frappe->>VSCode: Return AI response
        VSCode->>User: Display result
    end
```

---

## 🔑 **API Key Lifecycle**

```mermaid
graph TD
    subgraph Creation
        A[Subscription Created] --> B[Generate Random Key]
        B --> C[Hash with SHA-256]
        C --> D[Store Hash in DB]
        D --> E[Cache Raw Key - 5 min]
    end
    
    subgraph Retrieval
        E --> F{User Requests Key}
        F -->|Within 5 min| G[Return Raw Key]
        F -->|After 5 min| H[Return Prefix Only]
        G --> I[User Copies Key]
        H --> J[User Must Regenerate]
    end
    
    subgraph Usage
        I --> K[Store in Client]
        K --> L[Include in API Requests]
        L --> M[Server Hashes Key]
        M --> N[Compare with DB Hash]
        N -->|Match| O[Authorize Request]
        N -->|No Match| P[Reject Request]
    end
    
    subgraph Invalidation
        O --> Q{User Regenerates?}
        Q -->|Yes| R[Revoke Old Key]
        R --> B
        Q -->|No| S[Keep Using]
        S --> L
    end
    
    style B fill:#cfe2ff
    style C fill:#fff3cd
    style G fill:#d4edda
    style P fill:#f8d7da
```

---

## 📈 **Session Management Timeline**

```mermaid
gantt
    title User Session Lifecycle
    dateFormat HH:mm
    axisFormat %H:%M
    
    section Login
    User submits credentials    :a1, 09:00, 1m
    Frappe validates password   :a2, after a1, 1m
    Session created             :a3, after a2, 1m
    Cookie set in browser       :a4, after a3, 1m
    
    section Active Session
    User browses dashboard      :b1, after a4, 30m
    Session auto-renewed        :b2, after b1, 1m
    User makes API request      :b3, after b2, 15m
    Session still valid         :b4, after b3, 1m
    
    section Inactivity
    User idle                   :c1, after b4, 4h
    Session expires warning     :c2, after c1, 1m
    Session timeout             :crit, c3, after c2, 1m
    
    section Re-login
    User returns                :d1, after c3, 10m
    Must login again            :d2, after d1, 2m
    New session created         :d3, after d2, 1m
```

---

## 🎯 **Quota & Budget Decision Tree**

```mermaid
graph TD
    Start([API Request Received]) --> Auth{API Key Valid?}
    Auth -->|No| Reject[401 Unauthorized]
    Auth -->|Yes| GetSub[Get Subscription]
    
    GetSub --> CheckStatus{Subscription Active?}
    CheckStatus -->|No| SubExpired[403 Subscription Expired]
    CheckStatus -->|Yes| CheckQuota{Daily Quota?}
    
    CheckQuota -->|Unlimited| CheckBudget
    CheckQuota -->|Limited| HasQuota{Quota Remaining?}
    HasQuota -->|No| QuotaErr[429 Daily Quota Exceeded]
    HasQuota -->|Yes| CheckBudget{Monthly Budget?}
    
    CheckBudget -->|Unlimited| Process
    CheckBudget -->|Limited| EstCost[Estimate Request Cost]
    EstCost --> HasBudget{Budget Remaining?}
    HasBudget -->|No| BudgetErr[402 Budget Exceeded]
    HasBudget -->|Yes| CheckAlert{Near Alert Threshold?}
    
    CheckAlert -->|Yes| SendAlert[Send Budget Alert Email]
    CheckAlert -->|No| Process
    SendAlert --> Process[Process AI Request]
    
    Process --> Success[Return AI Response]
    Success --> UpdateQuota[Decrement Daily Quota]
    UpdateQuota --> UpdateBudget[Add to Monthly Budget Used]
    UpdateBudget --> LogUsage[Create AI Usage Log]
    LogUsage --> Done([Complete])
    
    Reject --> Done
    SubExpired --> Done
    QuotaErr --> Done
    BudgetErr --> Done
    
    style Start fill:#e1f5e1
    style Process fill:#cfe2ff
    style Success fill:#d4edda
    style Reject fill:#f8d7da
    style QuotaErr fill:#f8d7da
    style BudgetErr fill:#f8d7da
    style Done fill:#ffe1e1
```

---

## 🔄 **Hook Execution Flow**

```mermaid
graph LR
    subgraph "Frappe Core"
        A[User.insert] --> B[User.after_insert]
    end
    
    subgraph "Hook Registry"
        B --> C{hooks.py<br/>doc_events}
        C --> D[User: after_insert]
    end
    
    subgraph "User Utils"
        D --> E[create_default_subscription]
        E --> F{Check User Type}
        F -->|Website User| G[Continue]
        F -->|System User| H[Skip]
        G --> I{User Enabled?}
        I -->|Yes| J[Find Free Plan]
        I -->|No| H
    end
    
    subgraph "Subscription Creation"
        J --> K[Create AI Subscription]
        K --> L[before_insert hook]
        L --> M[set_dates]
        M --> N[set_quota]
        N --> O[initialize_monthly_budget]
        O --> P[Save to DB]
        P --> Q[after_insert hook]
        Q --> R[create_api_key]
    end
    
    subgraph "API Key Creation"
        R --> S[Generate Random Key]
        S --> T[Hash with SHA-256]
        T --> U[Create AI API Key Doc]
        U --> V[Cache Raw Key]
        V --> W[Link to Subscription]
    end
    
    W --> X([Complete])
    H --> X
    
    style A fill:#e7f3ff
    style K fill:#fff3cd
    style R fill:#cfe2ff
    style W fill:#d4edda
```

---

## 📱 **Multi-Device Session Management**

```mermaid
graph TB
    User([User Account]) --> D1[Desktop Browser]
    User --> D2[Mobile Browser]
    User --> D3[VS Code Extension]
    User --> D4[Tablet Browser]
    
    D1 --> S1[Session 1<br/>sid=abc123...]
    D2 --> S2[Session 2<br/>sid=def456...]
    D3 --> S3[API Key Auth<br/>key=xyz789...]
    D4 --> S4[Session 3<br/>sid=ghi012...]
    
    S1 --> R[Redis Session Store]
    S2 --> R
    S4 --> R
    S3 --> K[API Key Validation]
    
    R --> Sub[AI Subscription]
    K --> Sub
    
    Sub --> Track[Usage Tracking]
    
    style User fill:#e7f3ff
    style Sub fill:#fff3cd
    style Track fill:#d4edda
```

---

## 🛡️ **Security Layers**

```mermaid
graph TD
    subgraph "Layer 1: Transport"
        HTTPS[HTTPS/TLS 1.3]
    end
    
    subgraph "Layer 2: Authentication"
        BCrypt[BCrypt Password Hash]
        Session[HTTP-only Session Cookie]
        CSRF[CSRF Token]
    end
    
    subgraph "Layer 3: Authorization"
        APIHash[SHA-256 API Key Hash]
        SubCheck[Subscription Status]
        QuotaCheck[Quota Validation]
    end
    
    subgraph "Layer 4: Rate Limiting"
        QPSLimit[QPS Rate Limit]
        DailyQuota[Daily Request Quota]
        BudgetLimit[Monthly Budget Limit]
    end
    
    subgraph "Layer 5: Monitoring"
        UsageLog[AI Usage Log]
        ErrorLog[Error Logging]
        Alert[Budget Alert System]
    end
    
    HTTPS --> BCrypt
    BCrypt --> Session
    Session --> CSRF
    CSRF --> APIHash
    APIHash --> SubCheck
    SubCheck --> QuotaCheck
    QuotaCheck --> QPSLimit
    QPSLimit --> DailyQuota
    DailyQuota --> BudgetLimit
    BudgetLimit --> UsageLog
    UsageLog --> ErrorLog
    ErrorLog --> Alert
    
    style HTTPS fill:#e7f3ff
    style BCrypt fill:#fff3cd
    style APIHash fill:#cfe2ff
    style QPSLimit fill:#d4edda
    style UsageLog fill:#f8d7da
```

---

## 📚 **Related Documentation**

- [Complete User Sign-In Workflow](./USER_SIGNIN_WORKFLOW.md) - Detailed explanation
- [User API Quick Reference](./USER_API_QUICK_REF.md) - API endpoints
- [Frappe User Refactoring](./FRAPPE_USER_REFACTORING.md) - Architecture decisions

---

**Visual guide to understand the complete authentication and authorization flow in Oropendola AI!** 🚀
# 🎨 Visual Authentication Flow - Oropendola AI

## Quick Visual Reference for User Sign-In Process

---

## 🔄 **Complete Flow: Registration to API Usage**

```mermaid
graph TB
    Start([User Visits Website]) --> Signup[Sign Up Form]
    Signup --> CreateUser[Frappe Creates User]
    CreateUser --> EmailVerif[Email Verification Sent]
    EmailVerif --> UserClick[User Clicks Verify Link]
    UserClick --> EnableUser[User Account Enabled]
    
    EnableUser --> Hook{Hook Triggered:<br/>after_insert}
    Hook --> CheckType{User Type?}
    CheckType -->|Website User| CreateSub[Create AI Subscription]
    CheckType -->|System User| Skip[Skip - Admin User]
    
    CreateSub --> InitSub[Initialize Subscription]
    InitSub --> SetDates[Set Start/End Dates]
    SetDates --> SetQuota[Set Daily Quota]
    SetQuota --> SetBudget[Initialize Monthly Budget]
    SetBudget --> GenKey[Generate API Key]
    
    GenKey --> GenRandom[Generate Random 32-byte Key]
    GenRandom --> HashKey[SHA-256 Hash]
    HashKey --> CreateKeyDoc[Create AI API Key Doc]
    CreateKeyDoc --> CacheKey[Cache Raw Key - 5 min]
    
    CacheKey --> UserLogin[User Logs In]
    UserLogin --> ValidateCreds[Validate Credentials]
    ValidateCreds --> CreateSession[Create Session]
    CreateSession --> SetCookie[Set HTTP-only Cookie]
    SetCookie --> Dashboard[Redirect to Dashboard]
    
    Dashboard --> GetKey[Request API Key]
    GetKey --> CheckCache{Cache Available?}
    CheckCache -->|Yes| ShowKey[Display Full API Key]
    CheckCache -->|No| ShowPrefix[Show Prefix Only]
    
    ShowKey --> UserCopy[User Copies Key]
    UserCopy --> VSCode[Paste to VS Code]
    VSCode --> APIRequest[API Request with Key]
    
    APIRequest --> ValidateKey[Validate API Key Hash]
    ValidateKey --> CheckQuota{Quota Available?}
    CheckQuota -->|Yes| CheckBudget{Budget Available?}
    CheckQuota -->|No| QuotaError[Quota Exceeded Error]
    CheckBudget -->|Yes| Process[Process Request]
    CheckBudget -->|No| BudgetError[Budget Exceeded Error]
    
    Process --> UpdateUsage[Update Usage Stats]
    UpdateUsage --> LogUsage[Log to AI Usage Log]
    LogUsage --> Response[Return Response]
    
    Response --> End([End])
    QuotaError --> End
    BudgetError --> End
    Skip --> End
    ShowPrefix --> End
    
    style Start fill:#e1f5e1
    style End fill:#ffe1e1
    style CreateSub fill:#fff3cd
    style GenKey fill:#cfe2ff
    style UserLogin fill:#d1ecf1
    style Process fill:#d4edda
```

---

## 🏗️ **System Architecture**

```mermaid
graph LR
    subgraph "User Layer"
        U[Frappe User]
    end
    
    subgraph "Subscription Layer"
        S[AI Subscription]
        P[AI Plan]
    end
    
    subgraph "Security Layer"
        K[AI API Key]
        H[SHA-256 Hash]
    end
    
    subgraph "Tracking Layer"
        L[AI Usage Log]
        Q[Quota Tracker]
        B[Budget Tracker]
    end
    
    subgraph "Cache Layer"
        R[Redis Cache]
        SK[Session Store]
    end
    
    U -->|user field| S
    S -->|plan field| P
    S -->|api_key_link| K
    K -->|stores| H
    K -->|cached in| R
    S -->|tracks in| L
    S -->|manages| Q
    S -->|manages| B
    U -->|session in| SK
    
    style U fill:#e7f3ff
    style S fill:#fff3cd
    style K fill:#d4edda
    style R fill:#f8d7da
```

---

## 🔐 **Authentication & Authorization States**

```mermaid
stateDiagram-v2
    [*] --> Guest
    Guest --> Registered : Sign Up
    Registered --> PendingVerification : Email Sent
    PendingVerification --> Verified : Click Email Link
    Verified --> SubscriptionCreated : Hook Triggered
    SubscriptionCreated --> APIKeyGenerated : Auto-Create Key
    APIKeyGenerated --> LoggedOut : Verification Complete
    
    LoggedOut --> LoggedIn : Login with Password
    LoggedIn --> Authenticated : Session Created
    Authenticated --> APIKeyRetrieved : Get API Key
    APIKeyRetrieved --> ActiveUser : Key Stored
    
    ActiveUser --> MakingRequests : Use API
    MakingRequests --> QuotaChecked : Validate Quota
    QuotaChecked --> BudgetChecked : Validate Budget
    BudgetChecked --> Processing : Both OK
    Processing --> MakingRequests : Continue Usage
    
    QuotaChecked --> QuotaExceeded : No Quota
    BudgetChecked --> BudgetExceeded : No Budget
    
    QuotaExceeded --> [*]
    BudgetExceeded --> [*]
    
    ActiveUser --> LoggedOut : Logout/Session Timeout
    LoggedOut --> [*]
```

---

## 📊 **Data Flow: Login to API Request**

```mermaid
sequenceDiagram
    autonumber
    
    actor User
    participant Browser
    participant Frappe
    participant Session
    participant Subscription
    participant APIKey
    participant Redis
    participant VSCode
    
    rect rgb(230, 245, 255)
        Note over User,Frappe: Login Phase
        User->>Browser: Enter email/password
        Browser->>Frappe: POST /login
        Frappe->>Frappe: Validate BCrypt hash
        Frappe->>Session: Create session
        Session->>Redis: Store session data
        Frappe->>Browser: Set HTTP-only cookie
        Browser->>User: Redirect to /dashboard
    end
    
    rect rgb(255, 243, 205)
        Note over User,APIKey: API Key Retrieval Phase
        User->>Browser: Click "Get API Key"
        Browser->>Frappe: GET /api/user_api.get_my_api_key
        Frappe->>Session: Validate session cookie
        Session->>Frappe: Session valid
        Frappe->>Subscription: Get subscription by user
        Subscription->>APIKey: Get linked API key
        APIKey->>Redis: Check cache for raw key
        Redis->>APIKey: Return raw key (if < 5 min)
        APIKey->>Frappe: Return key data
        Frappe->>Browser: JSON response
        Browser->>User: Display API key
        User->>User: Copy to clipboard
    end
    
    rect rgb(212, 237, 218)
        Note over User,VSCode: API Usage Phase
        User->>VSCode: Paste API key
        VSCode->>VSCode: Store in secure storage
        VSCode->>Frappe: POST /api/chat_completion<br/>Authorization: Bearer <key>
        Frappe->>Frappe: Hash provided key (SHA-256)
        Frappe->>APIKey: Check hash in database
        APIKey->>Subscription: Get subscription
        Subscription->>Subscription: Check quota
        Subscription->>Subscription: Check budget
        Subscription->>Frappe: Validation passed
        Frappe->>Frappe: Process AI request
        Frappe->>Subscription: Update usage
        Subscription->>Subscription: Log to AI Usage Log
        Frappe->>VSCode: Return AI response
        VSCode->>User: Display result
    end
```

---

## 🔑 **API Key Lifecycle**

```mermaid
graph TD
    subgraph Creation
        A[Subscription Created] --> B[Generate Random Key]
        B --> C[Hash with SHA-256]
        C --> D[Store Hash in DB]
        D --> E[Cache Raw Key - 5 min]
    end
    
    subgraph Retrieval
        E --> F{User Requests Key}
        F -->|Within 5 min| G[Return Raw Key]
        F -->|After 5 min| H[Return Prefix Only]
        G --> I[User Copies Key]
        H --> J[User Must Regenerate]
    end
    
    subgraph Usage
        I --> K[Store in Client]
        K --> L[Include in API Requests]
        L --> M[Server Hashes Key]
        M --> N[Compare with DB Hash]
        N -->|Match| O[Authorize Request]
        N -->|No Match| P[Reject Request]
    end
    
    subgraph Invalidation
        O --> Q{User Regenerates?}
        Q -->|Yes| R[Revoke Old Key]
        R --> B
        Q -->|No| S[Keep Using]
        S --> L
    end
    
    style B fill:#cfe2ff
    style C fill:#fff3cd
    style G fill:#d4edda
    style P fill:#f8d7da
```

---

## 📈 **Session Management Timeline**

```mermaid
gantt
    title User Session Lifecycle
    dateFormat HH:mm
    axisFormat %H:%M
    
    section Login
    User submits credentials    :a1, 09:00, 1m
    Frappe validates password   :a2, after a1, 1m
    Session created             :a3, after a2, 1m
    Cookie set in browser       :a4, after a3, 1m
    
    section Active Session
    User browses dashboard      :b1, after a4, 30m
    Session auto-renewed        :b2, after b1, 1m
    User makes API request      :b3, after b2, 15m
    Session still valid         :b4, after b3, 1m
    
    section Inactivity
    User idle                   :c1, after b4, 4h
    Session expires warning     :c2, after c1, 1m
    Session timeout             :crit, c3, after c2, 1m
    
    section Re-login
    User returns                :d1, after c3, 10m
    Must login again            :d2, after d1, 2m
    New session created         :d3, after d2, 1m
```

---

## 🎯 **Quota & Budget Decision Tree**

```mermaid
graph TD
    Start([API Request Received]) --> Auth{API Key Valid?}
    Auth -->|No| Reject[401 Unauthorized]
    Auth -->|Yes| GetSub[Get Subscription]
    
    GetSub --> CheckStatus{Subscription Active?}
    CheckStatus -->|No| SubExpired[403 Subscription Expired]
    CheckStatus -->|Yes| CheckQuota{Daily Quota?}
    
    CheckQuota -->|Unlimited| CheckBudget
    CheckQuota -->|Limited| HasQuota{Quota Remaining?}
    HasQuota -->|No| QuotaErr[429 Daily Quota Exceeded]
    HasQuota -->|Yes| CheckBudget{Monthly Budget?}
    
    CheckBudget -->|Unlimited| Process
    CheckBudget -->|Limited| EstCost[Estimate Request Cost]
    EstCost --> HasBudget{Budget Remaining?}
    HasBudget -->|No| BudgetErr[402 Budget Exceeded]
    HasBudget -->|Yes| CheckAlert{Near Alert Threshold?}
    
    CheckAlert -->|Yes| SendAlert[Send Budget Alert Email]
    CheckAlert -->|No| Process
    SendAlert --> Process[Process AI Request]
    
    Process --> Success[Return AI Response]
    Success --> UpdateQuota[Decrement Daily Quota]
    UpdateQuota --> UpdateBudget[Add to Monthly Budget Used]
    UpdateBudget --> LogUsage[Create AI Usage Log]
    LogUsage --> Done([Complete])
    
    Reject --> Done
    SubExpired --> Done
    QuotaErr --> Done
    BudgetErr --> Done
    
    style Start fill:#e1f5e1
    style Process fill:#cfe2ff
    style Success fill:#d4edda
    style Reject fill:#f8d7da
    style QuotaErr fill:#f8d7da
    style BudgetErr fill:#f8d7da
    style Done fill:#ffe1e1
```

---

## 🔄 **Hook Execution Flow**

```mermaid
graph LR
    subgraph "Frappe Core"
        A[User.insert] --> B[User.after_insert]
    end
    
    subgraph "Hook Registry"
        B --> C{hooks.py<br/>doc_events}
        C --> D[User: after_insert]
    end
    
    subgraph "User Utils"
        D --> E[create_default_subscription]
        E --> F{Check User Type}
        F -->|Website User| G[Continue]
        F -->|System User| H[Skip]
        G --> I{User Enabled?}
        I -->|Yes| J[Find Free Plan]
        I -->|No| H
    end
    
    subgraph "Subscription Creation"
        J --> K[Create AI Subscription]
        K --> L[before_insert hook]
        L --> M[set_dates]
        M --> N[set_quota]
        N --> O[initialize_monthly_budget]
        O --> P[Save to DB]
        P --> Q[after_insert hook]
        Q --> R[create_api_key]
    end
    
    subgraph "API Key Creation"
        R --> S[Generate Random Key]
        S --> T[Hash with SHA-256]
        T --> U[Create AI API Key Doc]
        U --> V[Cache Raw Key]
        V --> W[Link to Subscription]
    end
    
    W --> X([Complete])
    H --> X
    
    style A fill:#e7f3ff
    style K fill:#fff3cd
    style R fill:#cfe2ff
    style W fill:#d4edda
```

---

## 📱 **Multi-Device Session Management**

```mermaid
graph TB
    User([User Account]) --> D1[Desktop Browser]
    User --> D2[Mobile Browser]
    User --> D3[VS Code Extension]
    User --> D4[Tablet Browser]
    
    D1 --> S1[Session 1<br/>sid=abc123...]
    D2 --> S2[Session 2<br/>sid=def456...]
    D3 --> S3[API Key Auth<br/>key=xyz789...]
    D4 --> S4[Session 3<br/>sid=ghi012...]
    
    S1 --> R[Redis Session Store]
    S2 --> R
    S4 --> R
    S3 --> K[API Key Validation]
    
    R --> Sub[AI Subscription]
    K --> Sub
    
    Sub --> Track[Usage Tracking]
    
    style User fill:#e7f3ff
    style Sub fill:#fff3cd
    style Track fill:#d4edda
```

---

## 🛡️ **Security Layers**

```mermaid
graph TD
    subgraph "Layer 1: Transport"
        HTTPS[HTTPS/TLS 1.3]
    end
    
    subgraph "Layer 2: Authentication"
        BCrypt[BCrypt Password Hash]
        Session[HTTP-only Session Cookie]
        CSRF[CSRF Token]
    end
    
    subgraph "Layer 3: Authorization"
        APIHash[SHA-256 API Key Hash]
        SubCheck[Subscription Status]
        QuotaCheck[Quota Validation]
    end
    
    subgraph "Layer 4: Rate Limiting"
        QPSLimit[QPS Rate Limit]
        DailyQuota[Daily Request Quota]
        BudgetLimit[Monthly Budget Limit]
    end
    
    subgraph "Layer 5: Monitoring"
        UsageLog[AI Usage Log]
        ErrorLog[Error Logging]
        Alert[Budget Alert System]
    end
    
    HTTPS --> BCrypt
    BCrypt --> Session
    Session --> CSRF
    CSRF --> APIHash
    APIHash --> SubCheck
    SubCheck --> QuotaCheck
    QuotaCheck --> QPSLimit
    QPSLimit --> DailyQuota
    DailyQuota --> BudgetLimit
    BudgetLimit --> UsageLog
    UsageLog --> ErrorLog
    ErrorLog --> Alert
    
    style HTTPS fill:#e7f3ff
    style BCrypt fill:#fff3cd
    style APIHash fill:#cfe2ff
    style QPSLimit fill:#d4edda
    style UsageLog fill:#f8d7da
```

---

## 📚 **Related Documentation**

- [Complete User Sign-In Workflow](./USER_SIGNIN_WORKFLOW.md) - Detailed explanation
- [User API Quick Reference](./USER_API_QUICK_REF.md) - API endpoints
- [Frappe User Refactoring](./FRAPPE_USER_REFACTORING.md) - Architecture decisions

---

**Visual guide to understand the complete authentication and authorization flow in Oropendola AI!** 🚀
