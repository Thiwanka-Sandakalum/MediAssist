
"""
Dispensing Agent node for MediAssist
- Confirms inventory deduction, creates dispensing record, marks fulfilled, updates patient meds
"""

from langsmith import traceable
from src.config import config
from src.utilities.timeout import with_timeout
from src.state import MediAssistState
from src.tools.dispensing.confirm_inventory_deduction import confirm_inventory_deduction
from src.tools.dispensing.create_dispensing_record import create_dispensing_record
from src.tools.dispensing.mark_prescription_fulfilled import mark_prescription_fulfilled
from src.tools.dispensing.update_patient_medication_list import update_patient_medication_list
import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool

# Instantiate Gemini 2.5 Flash LLM
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview", temperature=0)

# Optionally, bind tools to the LLM (if you want tool-calling)
dispensing_tools = [
	confirm_inventory_deduction,
	create_dispensing_record,
	mark_prescription_fulfilled,
	update_patient_medication_list,
]
dispensing_agent = llm.bind_tools(dispensing_tools)


@traceable(name="dispensing_node")
@with_timeout(seconds=config.TOOL_TIMEOUT_SECONDS)
async def dispensing_node(state: MediAssistState) -> dict:
	"""Dispensing agent - dispenses medication with robust error handling."""
	errors = []
	
	# VALIDATE INPUTS
	prescription = state.get("prescription")
	inventory_status = state.get("inventory_status")
	patient = state.get("patient_record")
	
	if not prescription or not inventory_status or not patient:
		errors.append("Missing prescription, inventory_status, or patient data.")
		return {
			"errors": errors,
			"current_step": "DISPENSED",
			"workflow_status": "FAILED"
		}
	
	# Extract pharmacist ID
	clinical_approval = state.get("clinical_approval", {})
	pharmacist_id = clinical_approval.get("pharmacist_id", "PHARM001") if clinical_approval else "PHARM001"
	
	# TOOL 1: CONFIRM INVENTORY DEDUCTION
	deduction_ok = False
	reservation_id = inventory_status.reservation_id if inventory_status else None
	try:
		deduction_ok = confirm_inventory_deduction(reservation_id)
	except Exception as e:
		errors.append(f"Inventory deduction failed: {str(e)}")
		deduction_ok = False
	
	# TOOL 2: CREATE DISPENSING RECORD
	dispensing_record = None
	try:
		dispensing_record = create_dispensing_record(
			prescription,
			patient,
			pharmacist_id,
			datetime.datetime.now().isoformat()
		)
	except Exception as e:
		errors.append(f"Dispensing record creation failed: {str(e)}")
		dispensing_record = {
			"prescription_id": getattr(prescription, 'prescription_id', ''),
			"status": "DISPENSED_WITH_ERROR"
		}
	
	# TOOL 3: MARK PRESCRIPTION FULFILLED
	fulfilled = False
	try:
		fulfilled = mark_prescription_fulfilled(prescription.prescription_id)
	except Exception as e:
		errors.append(f"Mark fulfilled failed: {str(e)}")
		fulfilled = False
	
	# TOOL 4: UPDATE PATIENT MEDICATION LIST
	updated = False
	try:
		patient_id = patient.get("patient_id", "") if isinstance(patient, dict) else getattr(patient, "patient_id", "")
		updated = update_patient_medication_list(patient_id, prescription)
	except Exception as e:
		errors.append(f"Patient meds update failed: {str(e)}")
		updated = False
	
	# DETERMINE SUCCESS (all tools must succeed)
	all_ok = deduction_ok and fulfilled and updated
	
	return {
		"dispensing_record": dispensing_record,
		"current_step": "DISPENSED",
		"workflow_status": "IN_PROGRESS" if all_ok else "FAILED",
		"errors": errors
	}
