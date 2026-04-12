
"""
Inventory Agent node for MediAssist
- Checks stock, expiry, alternatives, triggers reorder if needed
"""

from langsmith import traceable
from src.config import config
from src.utilities.timeout import with_timeout
from src.state import MediAssistState, InventoryStatus
from src.tools.inventory.check_stock import check_stock
from src.tools.inventory.check_expiry import check_expiry
from src.tools.inventory.get_alternatives import get_alternatives
from src.tools.inventory.trigger_reorder import trigger_reorder


@traceable(name="inventory_node")
@with_timeout(seconds=config.TOOL_TIMEOUT_SECONDS)
async def inventory_node(state: MediAssistState) -> dict:
	"""
	Inventory agent - checks stock, expiry, alternatives with robust error handling.
	Wraps all tool calls to prevent crashes.
	"""
	errors = []
	
	# VALIDATE INPUTS
	prescription = state.get("prescription")
	if not prescription:
		errors.append("Missing prescription data.")
		return {
			"errors": errors,
			"current_step": "INVENTORY_DONE",
			"workflow_status": "FAILED"
		}
	
	# Validate prescription has required fields
	if not hasattr(prescription, 'drug_name') or not prescription.drug_name:
		errors.append("Prescription missing drug_name.")
		return {
			"errors": errors,
			"current_step": "INVENTORY_DONE",
			"workflow_status": "FAILED"
		}
	
	if not hasattr(prescription, 'quantity') or not prescription.quantity:
		errors.append("Prescription missing quantity.")
		return {
			"errors": errors,
			"current_step": "INVENTORY_DONE",
			"workflow_status": "FAILED"
		}
	
	# TOOL 1: CHECK STOCK
	stock = None
	try:
		stock = check_stock(prescription.drug_name, prescription.quantity)
	except Exception as e:
		errors.append(f"Stock check failed: {str(e)}")
		stock = {"available": False, "quantity_on_hand": 0, "batch_id": "", "expiry_date": "", "alternatives": []}
	
	# TOOL 2: CHECK EXPIRY (only if stock exists and has batch_id)
	expiry_valid = True
	if stock and stock.get("batch_id"):
		try:
			expiry = check_expiry(stock.get("batch_id", ""))
			expiry_valid = not expiry.get("expired", False)
		except Exception as e:
			errors.append(f"Expiry check failed: {str(e)}")
			expiry_valid = False
	
	# TOOL 3: GET ALTERNATIVES
	alternatives = []
	try:
		alternatives = get_alternatives(prescription.drug_name)
	except Exception as e:
		errors.append(f"Alternatives lookup failed: {str(e)}")
		alternatives = []
	
	# TOOL 4: TRIGGER REORDER (only if stock unavailable)
	reorder_triggered = False
	if stock and not stock.get("available", False):
		try:
			reorder_result = trigger_reorder(prescription.drug_name)
			reorder_triggered = reorder_result.get("triggered", False) if reorder_result else False
		except Exception as e:
			errors.append(f"Reorder trigger failed: {str(e)}")
			reorder_triggered = False
	
	# BUILD INVENTORY STATUS
	try:
		inventory_status = InventoryStatus(
			available=stock.get("available", False) and expiry_valid,
			quantity_on_hand=stock.get("quantity_on_hand", 0),
			batch_id=stock.get("batch_id", ""),
			expiry_date=stock.get("expiry_date", ""),
			alternatives=alternatives,
			reservation_id=stock.get("reservation_id")
		)
	except Exception as e:
		errors.append(f"Failed to build inventory status: {str(e)}")
		inventory_status = InventoryStatus(
			available=False,
			quantity_on_hand=0,
			batch_id="",
			expiry_date="",
			alternatives=[],
			reservation_id=None
		)
	
	# DETERMINE NEXT STEP
	if not inventory_status.available:
		return {
			"inventory_status": inventory_status,
			"current_step": "INVENTORY_DONE",
			"workflow_status": "AWAITING_HUMAN" if alternatives else "FAILED",
			"awaiting_human": bool(alternatives),
			"human_review_context": "Out of stock. Alternatives available." if alternatives else "Out of stock. No alternatives found.",
			"errors": errors,
			"reorder_triggered": reorder_triggered
		}
	
	return {
		"inventory_status": inventory_status,
		"current_step": "INVENTORY_DONE",
		"workflow_status": "IN_PROGRESS",
		"errors": errors,
		"reorder_triggered": reorder_triggered
	}
