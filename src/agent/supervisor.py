
"""
Supervisor Agent node for MediAssist
- Routes workflow to correct agent based on state, handles errors and HITL
"""
from langsmith import traceable
from src.state import MediAssistState

SUPERVISOR_PROMPT = """
You are the pharmacy workflow supervisor. Given the current workflow state,
route to the correct next agent. Do not perform any clinical reasoning yourself.

Current state: {state}
Rules:
- If prescription.status == PENDING → route to intake_agent
- If intake.complete and validation.status == PENDING → route to clinical_validation_agent
- If validation.risk_score > 0.7 and not human_approved → INTERRUPT
- If inventory.status == OUT_OF_STOCK → route to supervisor for escalation
- If accuracy_check.complete and not dispensing_approved → INTERRUPT
Respond with: {"next": "agent_name"} or {"next": "INTERRUPT", "reason": "..."}
"""

@traceable(name="supervisor_node")
async def supervisor_node(state: MediAssistState) -> dict:
	"""
	Reads current state, decides which agent to call next. Handles errors and re-routing.
	Does NOT do domain reasoning — that's the specialists' job.
	Deterministic routing only, no LLM or external tools.
	"""
	errors = state.get("errors", [])
	result = {}

	# Routing logic as per system prompt
	# 1. If workflow failed, end
	if state.get("workflow_status") == "FAILED":
		result["next"] = "END"
		result["reason"] = "Workflow failed."
		return result

	# 2. If awaiting human, go to human_review
	if state.get("awaiting_human"):
		result["next"] = "human_review"
		return result

	# 3. If prescription.status == PENDING → intake_agent
	if state.get("current_step") == "PENDING":
		result["next"] = "intake_agent"
		return result

	# 4. If intake.complete and validation.status == PENDING → clinical_validation_agent
	if state.get("current_step") == "INTAKE_DONE":
		result["next"] = "clinical_validation_agent"
		return result

	# 5. If validation.risk_score > 0.7 and not human_approved → INTERRUPT
	if state.get("current_step") == "VALIDATED":
		validation = state.get("validation_result") or state.get("validation")
		if validation and getattr(validation, "risk_score", 0) > 0.7 and not state.get("clinical_approval"):
			result["next"] = "INTERRUPT"
			result["reason"] = "Risk score > 0.7, pharmacist review required."
			return result
		else:
			result["next"] = "inventory_agent"
			return result

	# 6. If inventory.status == OUT_OF_STOCK → supervisor for escalation
	if state.get("current_step") == "INVENTORY_DONE":
		inventory = state.get("inventory")
		if inventory and hasattr(inventory, "available") and not inventory.available:
			result["next"] = "supervisor"
			result["reason"] = "Inventory out of stock, escalation required."
			return result
		result["next"] = "preparation_agent"
		return result

	# 7. If preparation done → accuracy_check_agent
	if state.get("current_step") == "PREPARED":
		result["next"] = "accuracy_check_agent"
		return result

	# 8. If accuracy_check.complete and not dispensing_approved → INTERRUPT
	if state.get("current_step") == "ACCURACY_DONE":
		if not state.get("dispensing_approval"):
			result["next"] = "INTERRUPT"
			result["reason"] = "Dispensing approval required."
			return result
		else:
			result["next"] = "dispensing_agent"
			return result

	# 9. If dispensed → counseling_agent
	if state.get("current_step") == "DISPENSED":
		result["next"] = "counseling_agent"
		return result

	# 10. If counseled → records_agent
	if state.get("current_step") == "COUNSELED":
		result["next"] = "records_agent"
		return result

	# 11. If recorded → END
	if state.get("current_step") == "RECORDED":
		result["next"] = "END"
		return result

	# Fallback: unknown step
	result["next"] = "END"
	result["reason"] = f"Unknown step: {state.get('current_step')}"
	return result
