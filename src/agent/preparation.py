
"""
Preparation Agent node for MediAssist
- Generates work order, label, reserves inventory, fetches storage instructions
"""

from langsmith import traceable
from src.config import config
from src.utilities.timeout import with_timeout
from src.state import MediAssistState
from src.tools.preparation.generate_label import generate_label
from src.tools.preparation.create_work_order import create_work_order
from src.tools.preparation.reserve_inventory import reserve_inventory
from src.tools.preparation.get_storage_instructions import get_storage_instructions


@traceable(name="preparation_node")
@with_timeout(seconds=config.TOOL_TIMEOUT_SECONDS)
async def preparation_node(state: MediAssistState) -> dict:
	"""Preparation agent - generates label, work order, reserves inventory with error handling."""
	errors = []
	
	# VALIDATE INPUTS
	prescription = state.get("prescription")
	inventory_status = state.get("inventory_status")
	patient = state.get("patient_record")
	
	if not prescription or not inventory_status or not patient:
		errors.append(f"Missing data: prescription={bool(prescription)}, "
		             f"inventory_status={bool(inventory_status)}, patient={bool(patient)}")
		return {
			"errors": errors,
			"current_step": "PREPARED",
			"workflow_status": "FAILED"
		}
	
	# TOOL 1: GENERATE LABEL
	label_text = None
	try:
		label_text = generate_label(prescription, patient)
	except Exception as e:
		errors.append(f"Label generation failed: {str(e)}")
		label_text = f"Take {getattr(prescription, 'dosage', 'as directed')} of {getattr(prescription, 'drug_name', 'medication')} by mouth."
	
	# TOOL 2: CREATE WORK ORDER
	work_order = None
	try:
		work_order = create_work_order(prescription, patient)
	except Exception as e:
		errors.append(f"Work order creation failed: {str(e)}")
		work_order = {
			"prescription_id": getattr(prescription, 'prescription_id', ''),
			"instructions": "Prepare as per standard protocol"
		}
	
	# TOOL 3: GET STORAGE INSTRUCTIONS
	storage_info = None
	try:
		storage_info = get_storage_instructions(prescription.drug_name)
	except Exception as e:
		errors.append(f"Storage instructions lookup failed: {str(e)}")
		storage_info = {"storage": "Room temperature"}
	
	# TOOL 4: RESERVE INVENTORY
	reserved = False
	reservation_id = inventory_status.reservation_id if inventory_status else None
	try:
		reserved = reserve_inventory(
			prescription.drug_name,
			prescription.quantity,
			reservation_id
		)
	except Exception as e:
		errors.append(f"Inventory reservation failed: {str(e)}")
		reserved = False
	
	return {
		"label_text": label_text,
		"work_order": work_order,
		"storage_info": storage_info,
		"current_step": "PREPARED",
		"workflow_status": "IN_PROGRESS" if reserved else "FAILED",
		"errors": errors
	}
