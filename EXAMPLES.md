# Example API Requests

This file contains example requests you can use to test the MediAssist backend.

## ✅ Valid Queries (Will Return FDA Data)

### 1. Side Effects Query
```bash
curl -X POST http://localhost:3000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the side effects of ibuprofen?"
  }'
```

### 2. Drug Purpose / Indications
```bash
curl -X POST http://localhost:3000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is metformin used for?"
  }'
```

### 3. Drug Warnings
```bash
curl -X POST http://localhost:3000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the warnings for aspirin?"
  }'
```

### 4. Drug Interactions
```bash
curl -X POST http://localhost:3000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What drugs interact with warfarin?"
  }'
```

### 5. General Drug Information
```bash
curl -X POST http://localhost:3000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about acetaminophen"
  }'
```

### 6. Brand Name Query (Auto-normalized)
```bash
curl -X POST http://localhost:3000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the side effects of Tylenol?"
  }'
```

### 7. Contraindications
```bash
curl -X POST http://localhost:3000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "When should I not take atorvastatin?"
  }'
```

---

## ❌ Refused Queries (Safety Rules)

### 1. Personal Dosing Question
```bash
curl -X POST http://localhost:3000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How much ibuprofen should I take for my headache?"
  }'
```

**Expected Response:**
```json
{
  "answer": "I cannot provide personal dosage recommendations. Medication dosing must be determined by a healthcare professional based on your individual medical history, current medications, and health conditions. Please consult your doctor or pharmacist."
}
```

### 2. Children Query
```bash
curl -X POST http://localhost:3000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can I give paracetamol to my 3 year old?"
  }'
```

**Expected Response:**
```json
{
  "answer": "I cannot provide medication information for children. Pediatric medication use requires professional medical guidance based on the child's age, weight, and health status. Please consult your pediatrician or pharmacist."
}
```

### 3. Pregnancy Query
```bash
curl -X POST http://localhost:3000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Is ibuprofen safe during pregnancy?"
  }'
```

**Expected Response:**
```json
{
  "answer": "I cannot provide medication safety information for pregnancy or breastfeeding. This requires professional medical evaluation. Please consult your obstetrician, midwife, or pharmacist immediately."
}
```

### 4. Liver/Kidney Condition Query
```bash
curl -X POST http://localhost:3000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I have kidney disease. Can I take metformin?"
  }'
```

**Expected Response:**
```json
{
  "answer": "I cannot advise on medication use with liver or kidney conditions. These conditions significantly affect how medications are processed and require professional medical evaluation. Please consult your doctor or specialist."
}
```

### 5. Medical Advice Request
```bash
curl -X POST http://localhost:3000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Should I take aspirin for my chest pain?"
  }'
```

**Expected Response:**
```json
{
  "answer": "I cannot provide personal medical advice or recommendations. I can only share general educational information from FDA drug labels. Please consult a healthcare professional for advice specific to your situation."
}
```

---

## 💬 Conversational Queries (No Tool Call)

### 1. Greeting
```bash
curl -X POST http://localhost:3000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello!"
  }'
```

**Expected Response:**
```json
{
  "answer": "Hello! I'm a pharmacy information assistant. I can help you learn about medications using FDA drug label data. What would you like to know about a specific drug?"
}
```

### 2. General Question
```bash
curl -X POST http://localhost:3000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What can you help me with?"
  }'
```

**Expected Response:**
```json
{
  "answer": "I can help you with information about medications based on FDA drug labels, such as:\n- Side effects and adverse reactions\n- What drugs are used for\n- Drug warnings and precautions\n- Drug interactions\n- Contraindications\n\nWhat specific medication would you like to know about?"
}
```

---

## 🧪 Testing with Postman

Import this collection:

```json
{
  "info": {
    "name": "MediAssist API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Chat - Side Effects",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"message\": \"What are the side effects of ibuprofen?\"\n}"
        },
        "url": {
          "raw": "http://localhost:3000/agent/chat",
          "protocol": "http",
          "host": ["localhost"],
          "port": "3000",
          "path": ["agent", "chat"]
        }
      }
    },
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": {
          "raw": "http://localhost:3000/agent/health",
          "protocol": "http",
          "host": ["localhost"],
          "port": "3000",
          "path": ["agent", "health"]
        }
      }
    }
  ]
}
```

---

## 📊 Expected Response Times

- **Simple queries** (no tool call): ~1-2 seconds
- **FDA queries** (with tool call): ~3-5 seconds
- **Complex queries** (multiple tool calls): ~5-10 seconds

---

## 🔍 Testing Drug Name Normalization

Test that brand names are properly converted to generic names:

```bash
# These should all query for "acetaminophen"
curl -X POST http://localhost:3000/agent/chat -H "Content-Type: application/json" \
  -d '{"message": "Side effects of paracetamol"}'

curl -X POST http://localhost:3000/agent/chat -H "Content-Type: application/json" \
  -d '{"message": "Side effects of Panadol"}'

curl -X POST http://localhost:3000/agent/chat -H "Content-Type: application/json" \
  -d '{"message": "Side effects of Tylenol"}'
```

All three should return similar results about acetaminophen.

---

## 🎯 Testing Agent Loop (Multi-turn)

The agent can handle compositional queries:

```bash
curl -X POST http://localhost:3000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about the side effects and drug interactions of warfarin"
  }'
```

Gemini might call the FDA tool multiple times to gather comprehensive information.

---

## 📝 Notes

- All responses include a safety disclaimer
- The agent is stateless - each request is independent
- Gemini decides when to use the FDA tool based on the query
- Invalid requests return 400 with error details
- Server errors return 500 with generic message (details in logs)
