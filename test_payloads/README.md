# Test Payloads - Ready to Use

This directory contains JSON payloads for testing the MediAssist workflow.

## 📋 Available Payloads

### ✅ happypath.json
**Normal prescription that should complete successfully**

```json
{
  "workflow_id": "WF-2026-04-11-001",
  "raw_prescription_text": "Amoxicillin 500mg TID x 7 days qty 21 for patient P12345"
}
```

**Expected:**
- Status: COMPLETE
- No HITL escalation
- All agents execute successfully

**Use:** `python test_workflow.py --payload happy_path`

---

### ⚠️ highrisk.json
**High-risk prescription with drug interaction - escalates to HITL**

```json
{
  "workflow_id": "WF-2026-04-11-002-HIGHRISK",
  "raw_prescription_text": "Warfarin 5mg daily + Aspirin 325mg daily for patient P99999 with bleeding disorder"
}
```

**Expected:**
- Status: AWAITING_HUMAN
- HITL escalation at clinical validation
- risk_score > 0.7

**Use:** `python test_workflow.py --payload high_risk`

---

### 📦 minimal.json
**Minimal required fields - tests bare minimum state**

```json
{
  "workflow_id": "WF-2026-04-11-003-MINIMAL",
  "raw_prescription_text": "Ibuprofen 200mg BID x 3 days qty 6"
}
```

**Expected:**
- Status: COMPLETE
- No HITL escalation
- All data populated

**Use:** `python test_workflow.py --payload minimal`

---

## 🚀 How to Use

### Option 1: Command Line
```bash
python test_workflow.py --payload happy_path
python test_workflow.py --payload high_risk
python test_workflow.py --payload minimal
```

### Option 2: View JSON
```bash
cat happypath.json
cat highrisk.json
cat minimal.json
```

### Option 3: Python Code
```python
import json
from src.graph import graph

with open('test_payloads/happypath.json') as f:
    payload = json.load(f)

result = graph.invoke(payload)
print(f"Status: {result['workflow_status']}")
```

### Option 4: Copy/Paste
Copy the entire JSON content and use in your test code or API client.

---

## 📊 Payload Comparison

| File | Scenario | Risk | Expected Status | HITL |
|------|----------|------|-----------------|------|
| happypath.json | Normal RX | Low | COMPLETE | No |
| highrisk.json | Drug interaction | High | AWAITING_HUMAN | Yes |
| minimal.json | Minimal fields | Low | COMPLETE | No |

---

## ✨ Adding Custom Payloads

To test other scenarios, create a new JSON file:

```json
{
  "workflow_id": "WF-CUSTOM-001",
  "current_step": "PENDING",
  "workflow_status": "PENDING",
  "created_at": "2026-04-11T10:00:00",
  "completed_at": null,
  "prescription_image": null,
  "raw_prescription_text": "Your prescription here",
  "prescription": null,
  "patient_record": null,
  ... (all other fields as null/empty)
}
```

Then use with:
```bash
python test_workflow.py --payload custom_name  # if file is custom_name.json
```

---

## 📝 Field Reference

**Required Fields:**
- `workflow_id` - Unique identifier
- `current_step` - Start with "PENDING"
- `workflow_status` - Start with "PENDING"
- `created_at` - ISO timestamp
- `raw_prescription_text` - Your test prescription

**Initialize as Null/Empty:**
- All output fields: `prescription`, `patient_record`, etc.
- HITL fields: `clinical_approval`, `dispensing_approval`
- Arrays: `errors`, `messages`
- Pricing: `total_latency_ms`, `llm_cost_usd`

---

## 🔍 Testing Workflow

1. **Copy a payload file**
2. **Load it with your test code**
3. **Run the workflow**
4. **Check the results**

Example:
```bash
# Load and inspect
cat happypath.json | jq .

# Run test
python test_workflow.py --payload happy_path

# Check results
echo "If status is COMPLETE, test passed! ✅"
```

---

## 💡 Pro Tips

1. **Modify payloads** - Edit JSON to test different prescriptions
2. **Save outputs** - Redirect test results for analysis
3. **Compare results** - Run multiple tests and compare outputs
4. **Create variations** - Copy a payload and modify for new scenarios

---

## 📚 See Also

- `../TESTING_GUIDE.md` - Complete testing guide
- `../JSON_QUICK_REFERENCE.md` - All payloads in one place
- `test_workflow.py` - Test runner script
- `test_payloads.py` - Python payload definitions

---
