# Architecture Documentation

## 🏛️ System Architecture

This document explains the architectural decisions and patterns used in the MediAssist backend.

---

## 1. Overall Pattern: Hexagonal Architecture (Ports & Adapters)

### Why Hexagonal Architecture?

```
┌─────────────────────────────────────────────┐
│           External World                     │
│  ┌──────────┐         ┌──────────┐          │
│  │  HTTP    │         │  Gemini  │          │
│  │  Client  │         │   API    │          │
│  └────┬─────┘         └─────┬────┘          │
└───────┼───────────────────┼─────────────────┘
        │                   │
        │ Port              │ Port
        ▼                   ▼
┌─────────────────────────────────────────────┐
│        Application Core (Domain Logic)       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │Controller│→ │  Agent   │→ │   Tool   │  │
│  │          │  │  Service │  │  Adapter │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│                      ↓                       │
│               ┌──────────┐                  │
│               │  Domain  │                  │
│               │  Mapper  │                  │
│               └──────────┘                  │
└─────────────────────────────────────────────┘
        │                   │
        │ Adapter           │ Adapter
        ▼                   ▼
┌─────────────────────────────────────────────┐
│           External Systems                   │
│  ┌──────────┐         ┌──────────┐          │
│  │ Express  │         │ openFDA  │          │
│  │  Router  │         │   API    │          │
│  └──────────┘         └──────────┘          │
└─────────────────────────────────────────────┘
```

**Benefits:**
- ✅ Core logic is isolated from external dependencies
- ✅ Easy to swap Gemini for another LLM
- ✅ Easy to swap openFDA for another data source
- ✅ Testable business logic
- ✅ No vendor lock-in

---

## 2. Agent Pattern: ReAct (Reason + Act)

### The ReAct Loop

```
User Query
    ↓
┌─────────────────────────────────────┐
│  REASON (Gemini analyzes intent)    │
│  - Does this need FDA data?         │
│  - What field to search?            │
│  - What search term to use?         │
└─────────────┬───────────────────────┘
              ↓
         ┌─────────┐
         │ Need    │  No → Generate direct answer
         │ Tool?   │─────→ Return to user
         └────┬────┘
              │ Yes
              ↓
┌─────────────────────────────────────┐
│  ACT (Execute FDA tool)             │
│  - Call openFDA API                 │
│  - Validate response                │
│  - Structure data                   │
└─────────────┬───────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  OBSERVE (Receive tool result)      │
│  - Parse FDA data                   │
│  - Map to domain entities           │
│  - Create summary                   │
└─────────────┬───────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  SYNTHESIZE (Gemini creates answer) │
│  - Human-readable response          │
│  - Safety disclaimer added          │
│  - Return to user                   │
└─────────────────────────────────────┘
```

**Why ReAct?**
- ✅ True agent behavior (not just RAG)
- ✅ Gemini decides when tools are needed
- ✅ Handles complex multi-step reasoning
- ✅ Can be extended with more tools

---

## 3. Single Tool Pattern

Instead of many specialized tools:

```
❌ BAD: Tool Explosion
- get_drug_side_effects()
- get_drug_warnings()
- get_drug_interactions()
- get_drug_contraindications()
- ... (20+ functions)

✅ GOOD: Single Flexible Tool
- query_openfda_drug_label(
    search_field: string,  // Gemini decides field
    search_term: string,   // Gemini decides term
    limit: number          // Gemini decides count
  )
```

**Why Single Tool?**
- ✅ Prevents tool explosion (maintainability nightmare)
- ✅ Gemini chooses fields dynamically
- ✅ More flexible than hardcoded tools
- ✅ Easier to extend (just add more fields)

---

## 4. Safety-by-Design Pattern

Safety is enforced in **3 layers**:

### Layer 1: Hard Refusal (Controller/Service)
```typescript
// Detect dangerous keywords BEFORE sending to LLM
if (query.includes('child')) {
  return REFUSAL_TEMPLATE;
}
```

### Layer 2: System Prompt (LLM Instruction)
```
"NEVER provide personal medical advice"
"REFUSE queries about children"
"REFUSE dosing recommendations"
```

### Layer 3: Response Validation (Post-generation)
```
Every response MUST include:
"⚠️ SAFETY DISCLAIMER: This is not medical advice..."
```

**Why 3 Layers?**
- ✅ Defense in depth
- ✅ No single point of failure
- ✅ Compliant with medical information regulations
- ✅ Protects users and business

---

## 5. Domain Mapping Pattern

```
Raw FDA Text (messy, unstructured)
    ↓
Domain Entity (structured, validated)
    ↓
Mapped Summary (clean, readable)
    ↓
LLM Synthesis (human-friendly)
```

**Example:**

```typescript
// Raw FDA (messy)
adverse_reactions: [
  "Nausea, vomiting, diarrhea\n\nIn clinical trials..."
]

// Domain Entity (structured)
{
  adverseReactions: ["Nausea", "Vomiting", "Diarrhea"]
}

// Mapped Summary (clean)
"**Side Effects:**
1. Nausea
2. Vomiting
3. Diarrhea"

// LLM Synthesis (human-friendly)
"Based on FDA data, ibuprofen may cause nausea, vomiting, 
and diarrhea. These are common side effects..."
```

**Why Domain Mapping?**
- ✅ Control over meaning (no hallucination)
- ✅ Validate data structure
- ✅ LLM only rephrases validated data
- ✅ Consistent output format

---

## 6. Stateless Agent Pattern

Each request is **completely independent**:

```typescript
// ❌ BAD: Stateful (memory between requests)
let conversationHistory = [];
conversationHistory.push(userMessage);

// ✅ GOOD: Stateless (fresh context each time)
function processMessage(request: AgentRequest) {
  // New chat session for each request
  const chat = model.startChat({
    history: [systemPrompt],
    tools: [fdaTool]
  });
  return chat.sendMessage(request.message);
}
```

**Why Stateless?**
- ✅ No memory leakage between users
- ✅ No cross-contamination of medical queries
- ✅ Easier to scale horizontally
- ✅ Simpler architecture
- ✅ HIPAA/GDPR friendly

**Trade-off:**
- ❌ No multi-turn conversations (acceptable for this use case)

---

## 7. Separation of Concerns

### Clear Responsibility Boundaries

```
┌─────────────────────────────────────┐
│  Controller (api/)                  │
│  - HTTP handling                    │
│  - Request validation (Zod)        │
│  - Response formatting              │
│  - Error handling                   │
└─────────────┬───────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Agent Service (agent/)             │
│  - Safety checks                    │
│  - Gemini orchestration             │
│  - ReAct loop                       │
│  - Tool execution                   │
└─────────────┬───────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Tool Adapter (tools/)              │
│  - API calls                        │
│  - Error handling                   │
│  - Data structuring                 │
└─────────────┬───────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Domain Mapper (domain/)            │
│  - Data transformation              │
│  - Validation                       │
│  - Summary generation               │
└─────────────────────────────────────┘
```

**Benefits:**
- ✅ Each layer has one responsibility
- ✅ Easy to test in isolation
- ✅ Easy to modify without side effects
- ✅ Clear data flow

---

## 8. Drug Name Normalization

### Why It's Critical

```
User says: "paracetamol"
FDA uses:  "acetaminophen"
Result:    ❌ No data found

Solution:  Normalize BEFORE querying
```

**Implementation:**

```typescript
const BRAND_TO_GENERIC = {
  'paracetamol': 'acetaminophen',
  'panadol': 'acetaminophen',
  'tylenol': 'acetaminophen'
};

function normalizeDrugName(name: string): string {
  return BRAND_TO_GENERIC[name.toLowerCase()] || name;
}
```

**Why This Matters:**
- ✅ Better user experience (they use common names)
- ✅ More accurate FDA queries
- ✅ International compatibility (UK: paracetamol, US: acetaminophen)

---

## 9. Error Handling Strategy

### Graceful Degradation

```typescript
try {
  const fdaData = await queryOpenFDA(params);
  return synthesizeResponse(fdaData);
} catch (error) {
  // Don't crash - return helpful error
  return {
    success: false,
    message: "No drug found. Check spelling.",
    suggestion: "Try using generic name"
  };
}
```

**Error Handling Layers:**

1. **API Level**: FDA API errors → structured error response
2. **Tool Level**: Validation errors → JSON error object
3. **Agent Level**: LLM errors → graceful fallback
4. **Controller Level**: HTTP errors → proper status codes

**Benefits:**
- ✅ Never expose stack traces to users
- ✅ Helpful error messages
- ✅ System stays responsive
- ✅ Logs errors for debugging

---

## 10. Configuration Management

### Environment-based Config

```typescript
// ✅ Type-safe environment variables
const envSchema = z.object({
  GEMINI_API_KEY: z.string().min(1),
  PORT: z.string().transform(Number),
  NODE_ENV: z.enum(['development', 'production'])
});

export const env = envSchema.parse(process.env);
```

**Why Zod Validation?**
- ✅ Fail fast on startup (not at runtime)
- ✅ Type safety
- ✅ Clear error messages
- ✅ Prevents misconfiguration

---

## 11. Logging Strategy

### Structured, Contextual Logging

```typescript
logger.agentStep('REASON', { userMessage });
logger.toolExecution('query_openfda', params);
logger.apiRequest('GET', url);
```

**Log Levels:**
- `INFO`: Normal flow (requests, steps)
- `WARN`: Refused queries, validation failures
- `ERROR`: Exceptions, API failures
- `DEBUG`: Detailed data (dev only)

**Benefits:**
- ✅ Easy to debug agent loop
- ✅ Track tool execution
- ✅ Monitor FDA API performance
- ✅ Production troubleshooting

---

## 12. Why This Will Impress a Pharmacy Owner

### Business Value

**Owner's Concern:** "Will it give wrong medical advice?"

**Your Answer:**
> "The AI never guesses. It only uses FDA-verified drug labels, and it refuses to give personal medical advice. It has 3 layers of safety checks."

**Demonstration:**
```bash
# Show refusal
curl ... -d '{"message": "How much should I take?"}'
→ "I cannot provide dosing recommendations..."

# Show FDA-based answer
curl ... -d '{"message": "What is aspirin used for?"}'
→ "According to FDA data, aspirin is used for..."
```

---

## 13. Extension Points

### Easy to Extend

**Add new safety rules:**
```typescript
// agent/agent.prompt.ts
SAFETY_KEYWORDS.newCategory = ['keyword1', 'keyword2'];
REFUSAL_TEMPLATES.newCategory = 'Refusal message';
```

**Add new FDA search fields:**
```typescript
// tools/openfda.tool.ts
enum: [
  'openfda.generic_name',
  'your_new_field_here'
]
```

**Add new drug name mappings:**
```typescript
// utils/normalizeDrugName.ts
BRAND_TO_GENERIC['newbrand'] = 'generic';
```

**Add new tools:**
```typescript
// tools/your-new-tool.ts
export const yourNewTool = { ... };

// agent/agent.service.ts
tools: [openFDAFunctionDeclaration, yourNewTool]
```

---

## 14. Testing Strategy

### Unit Testing (Recommended)

```typescript
// Test domain mapper
test('maps FDA data correctly', () => {
  const fdaResult = mockFDAResult();
  const entity = DrugMapper.toDrugEntity(fdaResult);
  expect(entity.genericName).toBe('acetaminophen');
});

// Test safety checks
test('refuses child queries', () => {
  const result = checkSafety('Can I give this to my child?');
  expect(result.isSafe).toBe(false);
});

// Test drug normalization
test('normalizes brand names', () => {
  expect(normalizeDrugName('paracetamol')).toBe('acetaminophen');
});
```

---

## 15. Performance Considerations

### Optimization Points

**1. FDA API Response Size**
- Use `limit` parameter (default: 5)
- Don't fetch more data than needed

**2. Gemini Token Usage**
- Concise system prompt
- Structured function responses
- Clear stop conditions

**3. Request Timeout**
- FDA API: 10 second timeout
- Gemini: Handled by SDK
- Overall request: ~5-10 seconds

**4. Caching (Future Enhancement)**
```typescript
// Cache common drug queries
const cache = new Map<string, DrugEntity>();
if (cache.has(drugName)) return cache.get(drugName);
```

---

## 16. Security Considerations

### Current Protections

1. **Input Validation**: Zod schemas prevent injection
2. **API Key Protection**: Environment variables only
3. **No SQL**: No database = no SQL injection
4. **Rate Limiting**: Not implemented (add in production)
5. **CORS**: Configured (adjust for production)

### Production Recommendations

```typescript
// Add rate limiting
import rateLimit from 'express-rate-limit';
app.use('/agent', rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
}));

// Add helmet for security headers
import helmet from 'helmet';
app.use(helmet());
```

---

## Summary: Why This Architecture?

| Pattern | Benefit |
|---------|---------|
| Hexagonal Architecture | Vendor independence, testability |
| ReAct Agent | True agent behavior, extensibility |
| Single Tool | Flexibility, maintainability |
| Safety-by-Design | User protection, compliance |
| Domain Mapping | No hallucination, data control |
| Stateless | Scalability, privacy |
| Separation of Concerns | Maintainability, clarity |

**Result:** Production-ready, safe, extensible pharmacy assistant that uses Gemini's reasoning with FDA's data.
