
"""
Accuracy Check Agent node for MediAssist
- Compares prepared item to prescription, generates checklist, triggers HITL
"""

from langsmith import traceable
from src.config import config
from src.utilities.timeout import with_timeout
from src.state import MediAssistState
from src.tools.accuracy_check.compare_label_to_prescription import compare_label_to_prescription
from src.tools.accuracy_check.verify_quantity import verify_quantity
from src.tools.accuracy_check.generate_verification_checklist import generate_verification_checklist
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool

# Instantiate Gemini 2.5 Flash LLM
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview", temperature=0)

# Optionally, bind tools to the LLM (if you want tool-calling)
accuracy_tools = [
	compare_label_to_prescription,
	verify_quantity,
	generate_verification_checklist,
]
accuracy_agent = llm.bind_tools(accuracy_tools)


@traceable(name="accuracy_check_node")
@with_timeout(seconds=config.TOOL_TIMEOUT_SECONDS)
async def accuracy_check_node(state: MediAssistState) -> dict:
	errors = []
	prescription = state.get("prescription")
	work_order = state.get("work_order")
	label_text = state.get("label_text")
	if not prescription or not work_order or not label_text:
		errors.append("Missing prescription, work order, or label text.")
		return {"errors": errors, "current_step": "ACCURACY_CHECK", "workflow_status": "FAILED"}

	# Use Gemini 2.5 Flash LLM to verify accuracy and call tools
	prompt = (
		"You are a pharmacist AI. Compare the prepared item to the prescription, verify quantity, and generate a verification checklist using the provided tools."
	)
	# Call tools directly
	accuracy_report = compare_label_to_prescription(label_text, prescription)
	quantity_verified = verify_quantity(label_text, prescription.quantity)  # Returns bool
	checklist = generate_verification_checklist(prescription, work_order)

	# Only escalate to HITL if there's a mismatch or quantity issue
	has_mismatch = not accuracy_report.get("match", True) if isinstance(accuracy_report, dict) else False
	has_quantity_issue = not quantity_verified  # quantity_verified is already a bool
	needs_human_review = has_mismatch or has_quantity_issue

	return {
		"accuracy_report": accuracy_report,
		"verification_checklist": checklist,
		"current_step": "ACCURACY_DONE",
		"workflow_status": "AWAITING_HUMAN" if needs_human_review else "IN_PROGRESS",
		"awaiting_human": needs_human_review,
		"human_review_context": "Pharmacist must verify accuracy and sign off." if needs_human_review else None,
		"errors": errors
	}
