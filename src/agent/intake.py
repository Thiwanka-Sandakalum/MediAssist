
"""
Intake Agent node for MediAssist
- Extracts prescription data from image or text
- Fetches patient record
- Validates prescriber
- Normalizes drug name
"""
from langsmith import traceable
from src.config import config
from src.utilities.timeout import with_timeout
from src.state import MediAssistState, PrescriptionData
from src.tools.intake.parse_prescription_image import parse_prescription_image
from src.tools.intake.get_patient_record import get_patient_record
from src.tools.intake.lookup_drug_database import lookup_drug_database
from src.tools.intake.validate_prescriber import validate_prescriber

@traceable(name="intake_node")
@with_timeout(seconds=config.LLM_TIMEOUT_SECONDS)
async def intake_node(state: MediAssistState) -> dict:
	errors = []
	
	# Validate workflow_id exists
	workflow_id = state.get("workflow_id")
	if not workflow_id:
		errors.append("Missing workflow_id in state")
		return {"errors": errors, "current_step": "PENDING", "workflow_status": "FAILED"}
	
	# 1. Extract prescription fields
	prescription_image = state.get("prescription_image")
	raw_text = state.get("raw_prescription_text")
	
	drug_name = None
	dose = None
	frequency = None
	patient_id = None
	prescriber = None
	
	if prescription_image is not None:
		try:
			ocr = parse_prescription_image(prescription_image)
			drug_name = ocr.get("drug_name")
			dose = ocr.get("dose")
			frequency = ocr.get("frequency")
			patient_id = ocr.get("patient_id")
			prescriber = ocr.get("prescriber")
		except ValueError as e:
			errors.append(f"OCR parsing failed: {str(e)}")
			return {"errors": errors, "current_step": "PENDING", "workflow_status": "FAILED"}
		except Exception as e:
			errors.append(f"Unexpected OCR error: {str(e)}")
			return {"errors": errors, "current_step": "PENDING", "workflow_status": "FAILED"}
	elif raw_text:
		# Simulate text parsing (in real: NLP extraction)
		drug_name = "SimulatedDrug"
		dose = "100mg"
		frequency = "BID"
		patient_id = "P00000"
		prescriber = "Dr. Simulated"
	else:
		errors.append("No prescription input provided (image or text required).")
		return {"errors": errors, "current_step": "PENDING", "workflow_status": "FAILED"}

	# 2. Fetch patient record
	if not patient_id:
		errors.append("Patient ID not extracted from prescription")
		return {"errors": errors, "current_step": "PENDING", "workflow_status": "FAILED"}
	
	patient_record = None
	try:
		patient_record = get_patient_record(patient_id)
	except KeyError as e:
		errors.append(f"Patient not found: {str(e)}")
		return {"errors": errors, "current_step": "PENDING", "workflow_status": "FAILED"}
	except Exception as e:
		errors.append(f"Patient lookup failed: {str(e)}")
		return {"errors": errors, "current_step": "PENDING", "workflow_status": "FAILED"}

	# 3. Normalize drug name
	drug_info = None
	try:
		drug_info = lookup_drug_database(drug_name)
	except KeyError as e:
		errors.append(f"Drug not found in database: {str(e)}")
		return {"errors": errors, "current_step": "PENDING", "workflow_status": "FAILED"}
	except Exception as e:
		errors.append(f"Drug lookup failed: {str(e)}")
		return {"errors": errors, "current_step": "PENDING", "workflow_status": "FAILED"}

	# 4. Validate prescriber
	prescriber_valid = False
	try:
		prescriber_valid = validate_prescriber(prescriber)
	except Exception as e:
		errors.append(f"Prescriber validation error: {str(e)}")
		prescriber_valid = False
	
	if not prescriber_valid:
		errors.append(f"Prescriber {prescriber} is not valid or not registered")

	# 5. Build PrescriptionData
	try:
		prescription = PrescriptionData(
			prescription_id=f"{workflow_id}-RX",
			patient_id=patient_id,
			prescriber_id=prescriber,
			drug_name=drug_info.get("drug_name", drug_name),
			generic_name=drug_info.get("generic_name", ""),
			dosage=dose,
			frequency=frequency,
			duration_days=7,
			quantity=21,
			raw_text=raw_text
		)
	except Exception as e:
		errors.append(f"Failed to create prescription record: {str(e)}")
		return {"errors": errors, "current_step": "PENDING", "workflow_status": "FAILED"}

	return {
		"prescription": prescription,
		"patient_record": patient_record,
		"current_step": "INTAKE_DONE",
		"workflow_status": "IN_PROGRESS" if not errors else "AWAITING_HUMAN",
		"errors": errors
	}
