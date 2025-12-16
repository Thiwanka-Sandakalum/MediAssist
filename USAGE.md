# USAGE GUIDE

## 🚀 Getting Started

### 1. Install Dependencies

```bash
npm install
```

### 2. Set Up Environment

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:

```
GEMINI_API_KEY=your_actual_gemini_api_key_here
PORT=3000
NODE_ENV=development
```

**To get a Gemini API key:**
1. Visit https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key and paste it in your `.env` file

### 3. Run the Server

**Development mode (with auto-reload):**
```bash
npm run dev
```

**Production mode:**
```bash
npm run build
npm start
```

The server will start on `http://localhost:3000`

---

## 📡 API Endpoints

### POST /agent/chat

Main endpoint for interacting with the pharmacy assistant.

**Request:**

```json
{
  "message": "What are the side effects of ibuprofen?"
}
```

**Response:**

```json
{
  "answer": "Based on FDA drug label data, ibuprofen may cause the following side effects:\n\n**Common Side Effects:**\n- Nausea\n- Heartburn\n- Dizziness\n...\n\n⚠️ **SAFETY DISCLAIMER**: This information is from FDA drug labels and is for educational purposes only..."
}
```

### GET /agent/health

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "service": "MediAssist Agent",
  "timestamp": "2025-12-13T10:30:00.000Z"
}
```

---

## 🧪 Example Requests

### Using cURL

**Basic query:**
```bash
curl -X POST http://localhost:3000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is acetaminophen used for?"}'
```

**Side effects query:**
```bash
curl -X POST http://localhost:3000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the side effects of paracetamol?"}'
```

**Drug interactions:**
```bash
curl -X POST http://localhost:3000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the drug interactions with aspirin?"}'
```

**Health check:**
```bash
curl http://localhost:3000/agent/health
```

### Using JavaScript/Node.js

```javascript
const response = await fetch('http://localhost:3000/agent/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: 'What are the warnings for ibuprofen?'
  })
});

const data = await response.json();
console.log(data.answer);
```

### Using Python

```python
import requests

response = requests.post(
    'http://localhost:3000/agent/chat',
    json={'message': 'Tell me about metformin'}
)

print(response.json()['answer'])
```

---

## ✅ Supported Queries

The agent can answer questions like:

- "What are the side effects of [drug name]?"
- "What is [drug name] used for?"
- "What are the warnings for [drug name]?"
- "What are the drug interactions with [drug name]?"
- "Tell me about [drug name]"
- "What are the contraindications for [drug name]?"

### Supported Drug Names

The system automatically normalizes common brand names to generic names:

- **paracetamol** / **Panadol** / **Tylenol** → acetaminophen
- **Advil** / **Motrin** → ibuprofen
- **Aspro** → aspirin
- **Voltaren** → diclofenac
- **Prilosec** → omeprazole
- **Glucophage** → metformin
- **Lipitor** → atorvastatin
- And many more...

---

## ❌ Refused Queries (Safety Rules)

The agent will **refuse** to answer:

1. **Personal dosing questions:**
   - "How much should I take?"
   - "What dose is right for me?"

2. **Children-related queries:**
   - "Can I give this to my child?"
   - "What's the dose for a 5-year-old?"

3. **Pregnancy/breastfeeding:**
   - "Is this safe during pregnancy?"
   - "Can I take this while breastfeeding?"

4. **Liver/kidney conditions:**
   - "I have kidney disease, can I take this?"
   - "Is this safe with liver problems?"

5. **Medical advice:**
   - "Should I take this drug?"
   - "Can I take this?"

**These queries get a polite refusal directing the user to consult a healthcare professional.**

---

## 🏗️ Architecture Overview

```
User Request
    ↓
Express Controller (validates input)
    ↓
Agent Service (safety check)
    ↓
Gemini API (decides if tool is needed)
    ↓
openFDA Tool (fetches FDA data)
    ↓
Domain Mapper (structures data)
    ↓
Gemini API (synthesizes human-readable response)
    ↓
User Response (with safety disclaimer)
```

### Key Components

1. **Controller** (`api/agent.controller.ts`): HTTP handling
2. **Agent Service** (`agent/agent.service.ts`): ReAct loop orchestration
3. **openFDA Tool** (`tools/openfda.tool.ts`): FDA API integration
4. **Domain Mapper** (`domain/drug.mapper.ts`): Data transformation
5. **Utilities** (`utils/`): Name normalization, logging

---

## 🐛 Debugging

### Enable Debug Logs

Set `NODE_ENV=development` in your `.env` file to see detailed logs:

```
[2025-12-13T10:30:00.000Z] [INFO] POST /agent/chat
[2025-12-13T10:30:00.001Z] [INFO] 🤖 Agent Step: REASON
[2025-12-13T10:30:01.234Z] [INFO] 🔧 Tool Execution: query_openfda_drug_label
[2025-12-13T10:30:02.456Z] [INFO] 📡 API Request: GET https://api.fda.gov/drug/label.json?...
[2025-12-13T10:30:03.789Z] [INFO] 🤖 Agent Step: SYNTHESIZE
```

### Common Issues

**1. "GEMINI_API_KEY is required"**
- Make sure you created a `.env` file
- Make sure `GEMINI_API_KEY` is set correctly

**2. "Error communicating with FDA API"**
- Check your internet connection
- FDA API might be down (rare)

**3. "No drug found matching your search criteria"**
- Check drug name spelling
- Try using the generic name instead of brand name
- Try searching with a different field

---

## 📊 Production Deployment

### Environment Variables for Production

```bash
NODE_ENV=production
PORT=3000
GEMINI_API_KEY=your_production_key_here
```

### Build and Run

```bash
npm run build
npm start
```

### Docker Deployment (Optional)

Create a `Dockerfile`:

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

Build and run:

```bash
docker build -t mediassist .
docker run -p 3000:3000 --env-file .env mediassist
```

---

## 🔒 Security Considerations

1. **API Key Protection**: Never commit `.env` to version control
2. **Rate Limiting**: Add rate limiting in production (e.g., express-rate-limit)
3. **Input Validation**: Already implemented with Zod
4. **CORS**: Update CORS settings in `app.ts` for production
5. **HTTPS**: Use HTTPS in production (e.g., behind nginx or AWS ALB)

---

## 📈 Monitoring

Monitor these metrics in production:

- Request count and latency
- Function call frequency
- FDA API errors
- Refused query rate
- Average response time

Use the built-in logger or integrate with monitoring services like:
- DataDog
- New Relic
- CloudWatch

---

## 🤝 Contributing

To extend the system:

1. **Add new drug name mappings**: Edit `utils/normalizeDrugName.ts`
2. **Add new safety rules**: Edit `agent/agent.prompt.ts`
3. **Add new FDA search fields**: Extend `tools/openfda.tool.ts`
4. **Customize responses**: Modify `agent/agent.prompt.ts` system prompt

---

## 📚 Documentation

- [Gemini API Docs](https://ai.google.dev/gemini-api/docs)
- [openFDA Drug Label API](https://open.fda.gov/apis/drug/label/)
- [Function Calling Guide](https://ai.google.dev/gemini-api/docs/function-calling)

---

## ⚖️ License

MIT
