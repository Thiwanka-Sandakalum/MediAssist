# Visual Diagrams

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      USER / CLIENT                          │
│                 (Web, Mobile, CLI, etc.)                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP Request
                         │ POST /agent/chat
                         │ {"message": "..."}
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    EXPRESS SERVER                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Controller Layer (api/)                   │  │
│  │  • Validate request (Zod)                           │  │
│  │  • Handle HTTP errors                               │  │
│  │  • Format responses                                 │  │
│  └────────────────────┬─────────────────────────────────┘  │
└─────────────────────────┼─────────────────────────────────┘
                          │
                          │ AgentRequest
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    AGENT LAYER (agent/)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  STEP 1: Safety Check                               │  │
│  │  • Check for dangerous keywords                     │  │
│  │  • Refuse if unsafe → Return immediately            │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│                       │ Safe to proceed                     │
│                       ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  STEP 2: REASON (Gemini)                            │  │
│  │  • Send system prompt + user message                │  │
│  │  • Gemini analyzes intent                           │  │
│  │  • Decides: Need tool? Yes/No                       │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│         ┌─────────────┴──────────────┐                     │
│         │                            │                     │
│    No tool needed              Tool needed                 │
│         │                            │                     │
│         │                            ▼                     │
│         │       ┌──────────────────────────────────────┐  │
│         │       │  STEP 3: ACT (Execute Tool)          │  │
│         │       │  • Extract function call params      │  │
│         │       │  • Call queryOpenFDA()               │  │
│         │       └────────────┬─────────────────────────┘  │
│         │                    │                            │
│         │                    │ Tool result                │
│         │                    ▼                            │
│         │       ┌──────────────────────────────────────┐  │
│         │       │  STEP 4: OBSERVE (Map Data)          │  │
│         │       │  • Parse FDA response                │  │
│         │       │  • Map to domain entities            │  │
│         │       │  • Create summary                    │  │
│         │       └────────────┬─────────────────────────┘  │
│         │                    │                            │
│         │                    │ Send result to Gemini      │
│         │                    ▼                            │
│         └───────────────────►┌─────────────────────────┐  │
│                              │  STEP 5: SYNTHESIZE      │  │
│                              │  • Gemini creates answer │  │
│                              │  • Add disclaimer        │  │
│                              │  • Return to user        │  │
│                              └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ AgentResponse
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  RESPONSE TO USER                           │
│  {                                                          │
│    "answer": "Based on FDA data, ibuprofen may cause...    │
│               ⚠️ SAFETY DISCLAIMER: ..."                   │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧠 ReAct Agent Loop (Detailed)

```
┌──────────────────────────────────────────────────────────────┐
│                      USER QUERY                              │
│        "What are the side effects of ibuprofen?"             │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────────┐
         │  1. REASON                        │
         │  ┌─────────────────────────────┐  │
         │  │ Gemini receives:            │  │
         │  │ • System prompt             │  │
         │  │ • User message              │  │
         │  │ • Available tools:          │  │
         │  │   - query_openfda_drug_label│  │
         │  └─────────────────────────────┘  │
         │                                   │
         │  ✅ Decision: Call FDA tool       │
         │  Function: query_openfda_drug_label│
         │  Params:                          │
         │    search_field: "openfda.generic_name"│
         │    search_term: "ibuprofen"       │
         │    limit: 2                       │
         └────────────────┬──────────────────┘
                          │
                          ▼
         ┌───────────────────────────────────┐
         │  2. ACT                           │
         │  ┌─────────────────────────────┐  │
         │  │ Execute queryOpenFDA():     │  │
         │  │ 1. Normalize drug name      │  │
         │  │ 2. Build FDA API URL        │  │
         │  │ 3. Make HTTP request        │  │
         │  │ 4. Handle errors            │  │
         │  └─────────────────────────────┘  │
         │                                   │
         │  🌐 Call: GET https://api.fda.gov/│
         │    drug/label.json?               │
         │    search=openfda.generic_name:   │
         │           "ibuprofen"&limit=2     │
         └────────────────┬──────────────────┘
                          │
                          ▼
         ┌───────────────────────────────────┐
         │  3. OBSERVE                       │
         │  ┌─────────────────────────────┐  │
         │  │ FDA Response received       │  │
         │  │ {                           │  │
         │  │   results: [{              │  │
         │  │     openfda: {...},        │  │
         │  │     adverse_reactions: [...],│  │
         │  │     warnings: [...],       │  │
         │  │     ...                    │  │
         │  │   }]                       │  │
         │  │ }                          │  │
         │  └─────────────────────────────┘  │
         │                                   │
         │  🔄 Map to DrugEntity             │
         │  📝 Create summary text           │
         │                                   │
         │  Result: {                        │
         │    success: true,                 │
         │    data: ["**Drug Name:** ..."]   │
         │  }                                │
         └────────────────┬──────────────────┘
                          │
                          │ Send result back
                          ▼
         ┌───────────────────────────────────┐
         │  4. SYNTHESIZE                    │
         │  ┌─────────────────────────────┐  │
         │  │ Gemini receives:            │  │
         │  │ • Original query            │  │
         │  │ • Tool result (FDA data)    │  │
         │  │                             │  │
         │  │ Creates human-friendly      │  │
         │  │ response:                   │  │
         │  │                             │  │
         │  │ "Based on FDA drug label    │  │
         │  │  data, ibuprofen may cause: │  │
         │  │  • Nausea                   │  │
         │  │  • Heartburn                │  │
         │  │  • Dizziness                │  │
         │  │  ...                        │  │
         │  │                             │  │
         │  │  ⚠️ SAFETY DISCLAIMER: ..."  │  │
         │  └─────────────────────────────┘  │
         └────────────────┬──────────────────┘
                          │
                          ▼
         ┌───────────────────────────────────┐
         │       RETURN TO USER              │
         └───────────────────────────────────┘
```

---

## 🛡️ Three-Layer Safety System

```
                    USER QUERY
                         │
                         ▼
┌────────────────────────────────────────────────────┐
│  LAYER 1: HARD REFUSAL (Before LLM)               │
│  ┌──────────────────────────────────────────────┐ │
│  │ Check message for keywords:                  │ │
│  │ • "child", "baby", "kid"                     │ │
│  │ • "how much should i take"                   │ │
│  │ • "pregnant", "breastfeeding"                │ │
│  │ • "liver disease", "kidney disease"          │ │
│  │ • "should i take", "can i take"              │ │
│  └──────────────────┬───────────────────────────┘ │
│                     │                             │
│         ┌───────────┴───────────┐                 │
│         │                       │                 │
│    Match found            No match               │
│         │                       │                 │
│         ▼                       │                 │
│   REFUSE IMMEDIATELY            │                 │
│   Return refusal template       │                 │
│   (Never reaches Gemini)        │                 │
└─────────────────────────────────┼─────────────────┘
                                  │
                                  ▼
┌────────────────────────────────────────────────────┐
│  LAYER 2: SYSTEM PROMPT (LLM Instruction)         │
│  ┌──────────────────────────────────────────────┐ │
│  │ System Prompt includes:                      │ │
│  │                                              │ │
│  │ "## CRITICAL SAFETY RULES                   │ │
│  │                                              │ │
│  │  ❌ NEVER provide:                           │ │
│  │  - Personal medical advice                  │ │
│  │  - Specific dosage recommendations          │ │
│  │  - Treatment recommendations                │ │
│  │  - Answers about pregnancy/children         │ │
│  │                                              │ │
│  │  ⚠️ REFUSE these queries immediately:       │ │
│  │  - 'How much should I take?'                │ │
│  │  - 'Can I give this to my child?'           │ │
│  │  - 'Is this safe during pregnancy?'         │ │
│  │  - 'Should I take this drug?'               │ │
│  │                                              │ │
│  │  ✅ RESPOND with refusal + escalation"      │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  Gemini is instructed to refuse unsafe queries    │
└────────────────────────────┬───────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────┐
│  LAYER 3: MANDATORY DISCLAIMER (Post-generation)   │
│  ┌──────────────────────────────────────────────┐ │
│  │ Every response MUST end with:                │ │
│  │                                              │ │
│  │ "⚠️ SAFETY DISCLAIMER:                       │ │
│  │  This information is from FDA drug labels   │ │
│  │  and is for educational purposes only.      │ │
│  │  It is NOT a substitute for professional    │ │
│  │  medical advice, diagnosis, or treatment.   │ │
│  │  Always consult your healthcare provider    │ │
│  │  before starting, stopping, or changing     │ │
│  │  any medication."                           │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  Protects against liability even if Layer 1&2 fail│
└────────────────────────────┬───────────────────────┘
                             │
                             ▼
                      SAFE RESPONSE
                       TO USER
```

---

## 📊 Data Flow

```
┌─────────────────────────────────────────────────────┐
│  USER MESSAGE                                       │
│  "What are the side effects of paracetamol?"        │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  NORMALIZATION                                      │
│  paracetamol → acetaminophen                        │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  FDA API QUERY                                      │
│  https://api.fda.gov/drug/label.json?               │
│    search=openfda.generic_name:"acetaminophen"      │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  RAW FDA DATA (messy)                               │
│  {                                                  │
│    results: [{                                      │
│      adverse_reactions: [                          │
│        "Nausea, vomiting, diarrhea\n\n             │
│         In clinical trials with 1000 patients..."  │
│      ],                                            │
│      ...                                           │
│    }]                                              │
│  }                                                  │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  DOMAIN ENTITY (structured)                         │
│  DrugEntity {                                       │
│    genericName: "acetaminophen",                    │
│    brandNames: ["Tylenol", "Panadol"],              │
│    adverseReactions: [                             │
│      "Nausea",                                     │
│      "Vomiting",                                   │
│      "Diarrhea"                                    │
│    ],                                              │
│    warnings: [...],                                │
│    ...                                             │
│  }                                                  │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  MAPPED SUMMARY (clean)                             │
│  **Drug Name:** acetaminophen                       │
│  **Brand Names:** Tylenol, Panadol                  │
│  **Side Effects:**                                  │
│  1. Nausea                                         │
│  2. Vomiting                                       │
│  3. Diarrhea                                       │
│  ...                                               │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  GEMINI SYNTHESIS (human-friendly)                  │
│  Based on FDA drug label data, acetaminophen        │
│  (also sold as Tylenol and Panadol) may cause       │
│  the following side effects:                        │
│                                                     │
│  • Nausea - feeling sick to your stomach           │
│  • Vomiting - throwing up                          │
│  • Diarrhea - loose stools                         │
│                                                     │
│  These side effects are usually mild...            │
│                                                     │
│  ⚠️ SAFETY DISCLAIMER: ...                          │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
              USER RESPONSE
```

---

## 🏛️ Hexagonal Architecture

```
┌───────────────────────────────────────────────────────┐
│              EXTERNAL WORLD                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │   HTTP   │  │  Gemini  │  │ openFDA  │            │
│  │  Client  │  │   API    │  │   API    │            │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘            │
└───────┼─────────────┼─────────────┼──────────────────┘
        │             │             │
        │ Port        │ Port        │ Port
        ▼             ▼             ▼
┌───────────────────────────────────────────────────────┐
│           APPLICATION CORE (Business Logic)           │
│                                                       │
│  ┌─────────────┐   ┌──────────────┐                  │
│  │ Controller  │───│ Agent Service│                  │
│  │  (HTTP)     │   │   (Brain)    │                  │
│  └─────────────┘   └──────┬───────┘                  │
│                           │                           │
│                           ▼                           │
│              ┌────────────────────────┐               │
│              │   Tool Adapter         │               │
│              │   (FDA Queries)        │               │
│              └────────┬───────────────┘               │
│                       │                               │
│                       ▼                               │
│              ┌────────────────────────┐               │
│              │   Domain Mapper        │               │
│              │   (Data Transform)     │               │
│              └────────────────────────┘               │
│                                                       │
│  ✅ Pure business logic - no external dependencies    │
│  ✅ Testable in isolation                            │
│  ✅ Framework-agnostic                               │
└───────────────────────────────────────────────────────┘
        │             │             │
        │ Adapter     │ Adapter     │ Adapter
        ▼             ▼             ▼
┌───────────────────────────────────────────────────────┐
│           INFRASTRUCTURE / ADAPTERS                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Express  │  │ Gemini   │  │  Axios   │            │
│  │  Router  │  │  Client  │  │  HTTP    │            │
│  └──────────┘  └──────────┘  └──────────┘            │
└───────────────────────────────────────────────────────┘

Benefits:
✅ Can swap Express → Fastify
✅ Can swap Gemini → Claude
✅ Can swap Axios → Fetch
✅ Core logic unchanged
```

---

## 📦 Project Structure

```
MediAssist/
│
├── 📝 Documentation
│   ├── README.md              (Overview)
│   ├── USAGE.md               (How to use)
│   ├── EXAMPLES.md            (API examples)
│   ├── ARCHITECTURE.md        (Design decisions)
│   ├── PROJECT_SUMMARY.md     (Complete summary)
│   ├── QUICK_REFERENCE.md     (Quick commands)
│   └── DIAGRAMS.md            (This file)
│
├── ⚙️ Configuration
│   ├── package.json           (Dependencies)
│   ├── tsconfig.json          (TypeScript config)
│   ├── .env.example           (Environment template)
│   ├── .gitignore             (Git ignore)
│   └── setup.sh               (Quick setup)
│
└── 💻 Source Code (src/)
    │
    ├── config/                (Configuration layer)
    │   ├── env.ts             → Environment validation
    │   └── gemini.ts          → Gemini client setup
    │
    ├── domain/                (Domain layer)
    │   ├── drug.entity.ts     → Data models
    │   └── drug.mapper.ts     → FDA → Domain mapping
    │
    ├── tools/                 (Tool layer)
    │   └── openfda.tool.ts    → FDA API integration
    │
    ├── agent/                 (Agent layer - CORE)
    │   ├── agent.types.ts     → Type definitions
    │   ├── agent.prompt.ts    → System prompt + safety
    │   └── agent.service.ts   → ReAct loop orchestration
    │
    ├── api/                   (API layer)
    │   └── agent.controller.ts→ Express routes
    │
    ├── utils/                 (Utilities)
    │   ├── logger.ts          → Structured logging
    │   └── normalizeDrugName.ts→ Drug name mapping
    │
    ├── app.ts                 (Express app)
    └── server.ts              (Server entry point)
```

---

**Built with ❤️ for safe, reliable pharmacy assistance**
