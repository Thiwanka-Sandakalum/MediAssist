# Quick Reference Card

## 🚀 Quick Start (3 Steps)

```bash
# 1. Setup
./setup.sh

# 2. Edit .env
nano .env  # Add GEMINI_API_KEY=your_key_here

# 3. Run
npm run dev
```

---

## 📡 API Endpoint

```bash
POST http://localhost:3000/agent/chat
Content-Type: application/json

{
  "message": "What are the side effects of ibuprofen?"
}
```

---

## 🧪 Quick Test

```bash
curl -X POST http://localhost:3000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the side effects of aspirin?"}'
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `src/agent/agent.service.ts` | **Core agent loop (ReAct)** |
| `src/agent/agent.prompt.ts` | **System prompt + safety rules** |
| `src/tools/openfda.tool.ts` | **FDA API integration** |
| `src/config/gemini.ts` | **Gemini client setup** |
| `src/domain/drug.mapper.ts` | **FDA data → clean format** |

---

## 🎯 Agent Flow

```
User Query
    ↓
Safety Check (refuse dangerous queries)
    ↓
Gemini Reasoning (decide if tool needed)
    ↓
Execute Tool (query FDA)
    ↓
Map Data (clean FDA response)
    ↓
Synthesize Answer (Gemini creates response)
    ↓
Return with Disclaimer
```

---

## 🛡️ Safety Rules (Auto-Refuse)

| Keyword | Refusal Reason |
|---------|---------------|
| "how much should i take" | Personal dosing |
| "child", "baby", "kid" | Children's medication |
| "pregnant", "breastfeeding" | Pregnancy/nursing |
| "liver disease", "kidney disease" | Organ conditions |
| "should i take", "can i take" | Medical advice |

---

## 🔧 Commands

```bash
npm run dev      # Start dev server (auto-reload)
npm run build    # Build TypeScript → JavaScript
npm start        # Run production build
npm run lint     # Run ESLint
```

---

## 📝 Environment Variables

```bash
GEMINI_API_KEY=your_key_here     # Required
PORT=3000                        # Optional (default: 3000)
NODE_ENV=development             # Optional (default: development)
```

---

## 🎨 Customize

### Add Drug Name Mapping

```typescript
// src/utils/normalizeDrugName.ts
BRAND_TO_GENERIC['newbrand'] = 'generic_name';
```

### Add Safety Rule

```typescript
// src/agent/agent.prompt.ts
SAFETY_KEYWORDS.newCategory = ['keyword1', 'keyword2'];
REFUSAL_TEMPLATES.newCategory = 'Your refusal message';
```

### Modify System Prompt

```typescript
// src/agent/agent.prompt.ts
export const SYSTEM_PROMPT = `...your new prompt...`;
```

---

## 📊 Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/agent/chat` | POST | Main chat interface |
| `/agent/health` | GET | Health check |
| `/` | GET | API info |

---

## 🔍 Debugging

### View Logs

```bash
npm run dev  # Logs to console in real-time
```

### Enable Debug Mode

```bash
# .env
NODE_ENV=development
```

### Log Output Example

```
[2025-12-13T10:30:00.000Z] [INFO] POST /agent/chat
[2025-12-13T10:30:00.001Z] [INFO] 🤖 Agent Step: REASON
[2025-12-13T10:30:01.234Z] [INFO] 🔧 Tool Execution: query_openfda_drug_label
[2025-12-13T10:30:02.456Z] [INFO] 📡 API Request: GET https://api.fda.gov/drug/label.json
[2025-12-13T10:30:03.789Z] [INFO] 🤖 Agent Step: SYNTHESIZE
```

---

## ⚠️ Common Issues

### "GEMINI_API_KEY is required"
- Edit `.env` file
- Add `GEMINI_API_KEY=your_key_here`

### "No drug found"
- Check spelling
- Try generic name (e.g., "acetaminophen" not "paracetamol")
- Try brand name (e.g., "Tylenol")

### "Port 3000 already in use"
- Change `PORT=3001` in `.env`
- Or kill process on port 3000: `lsof -ti:3000 | xargs kill`

---

## 📚 Documentation

- `README.md` - Project overview
- `USAGE.md` - Complete usage guide
- `EXAMPLES.md` - 20+ API examples
- `ARCHITECTURE.md` - Design decisions
- `PROJECT_SUMMARY.md` - Full project summary

---

## 🎯 Example Queries

### ✅ Valid

```json
{"message": "What are the side effects of ibuprofen?"}
{"message": "What is metformin used for?"}
{"message": "What are the warnings for aspirin?"}
{"message": "Tell me about atorvastatin"}
```

### ❌ Refused

```json
{"message": "How much should I take?"}
{"message": "Can I give this to my child?"}
{"message": "Is this safe during pregnancy?"}
```

---

## 🏗️ Architecture Pattern

**Hexagonal (Ports & Adapters)**

```
HTTP Client → Controller → Agent Service → FDA Tool → FDA API
                ↓              ↓             ↓
            Validate       Reason        Execute
                           (Gemini)      (Axios)
                              ↓
                         Domain Mapper
```

---

## 🧠 Gemini Function Declaration

```typescript
{
  name: "query_openfda_drug_label",
  description: "Query FDA drug labels...",
  parameters: {
    search_field: "openfda.generic_name",
    search_term: "ibuprofen",
    limit: 5
  }
}
```

---

## 📞 Get Help

1. Check documentation files
2. Review error logs
3. Test with example requests
4. Check Gemini API docs: https://ai.google.dev/
5. Check openFDA docs: https://open.fda.gov/

---

## 🎓 Key Concepts

| Concept | Description |
|---------|-------------|
| **ReAct Agent** | Reason → Act → Observe → Synthesize loop |
| **Function Calling** | Gemini decides when/how to call tools |
| **Domain Mapping** | FDA data → validated entities → summaries |
| **Stateless** | Each request is independent (no memory) |
| **Safety-by-Design** | 3 layers: refusal, prompt, disclaimer |

---

**Built with Gemini 2.5 Flash + openFDA** 🚀
