
"""
Records Agent node for MediAssist
- Writes to legal log, updates patient history, syncs to PMS, submits regulatory report
"""

from langsmith import traceable
from src.config import config
from src.utilities.timeout import with_timeout
from src.state import MediAssistState
from src.tools.records.write_legal_dispensing_log import write_legal_dispensing_log
from src.tools.records.update_patient_history import update_patient_history
from src.tools.records.sync_to_pms import sync_to_pms
from src.tools.records.submit_regulatory_report import submit_regulatory_report


@traceable(name="records_node")
@with_timeout(seconds=config.TOOL_TIMEOUT_SECONDS)
async def records_node(state: MediAssistState) -> dict:
	"""Records agent - writes legal log, updates patient history, syncs PMS with error handling."""
	import datetime
	errors = []
	
	# VALIDATE INPUTS
	dispensing_record = state.get("dispensing_record")
	prescription = state.get("prescription")
	patient = state.get("patient_record")
	
	if not dispensing_record or not prescription or not patient:
		errors.append("Missing dispensing record, prescription, or patient data.")
		return {
			"errors": errors,
			"current_step": "RECORDED",
			"workflow_status": "FAILED"
		}
	
	# TOOL 1: WRITE LEGAL DISPENSING LOG
	log_record = None
	try:
		log_record = write_legal_dispensing_log(dispensing_record)
	except Exception as e:
		errors.append(f"Legal log write failed: {str(e)}")
		log_record = None
	
	# TOOL 2: UPDATE PATIENT HISTORY
	history_updated = False
	try:
		patient_id = patient.get("patient_id", "") if isinstance(patient, dict) else getattr(patient, "patient_id", "")
		history_updated = update_patient_history(patient_id, prescription, dispensing_record)
	except Exception as e:
		errors.append(f"Patient history update failed: {str(e)}")
		history_updated = False
	
	# TOOL 3: SYNC TO PHARMACY MANAGEMENT SYSTEM (CRITICAL)
	pms_synced = False
	try:
		pms_synced = sync_to_pms(dispensing_record)
	except Exception as e:
		errors.append(f"PMS sync failed: {str(e)}")
		pms_synced = False
	
	# TOOL 4: SUBMIT REGULATORY REPORT (Optional, non-blocking failure)
	regulatory_submission = None
	try:
		regulatory_submission = submit_regulatory_report(dispensing_record, "SG")  # Singapore
	except Exception as e:
		errors.append(f"Regulatory submission failed (non-critical): {str(e)}")
		regulatory_submission = None
	
	# DETERMINE SUCCESS (PMS sync is critical)
	success = pms_synced and history_updated
	
	return {
		"regulatory_submission": regulatory_submission,
		"current_step": "RECORDED",
		"workflow_status": "COMPLETE" if success else "FAILED",
		"completed_at": datetime.datetime.now().isoformat() if success else None,
		"legal_log_id": log_record,
		"errors": errors
	}
