
"""Inventory Database Tools - Week 2 MVP Mock Implementation.

WEEK 2: These are stubsreturning safe defaults for testing.
WEEK 3+: Replace with actual PostgreSQL implementation.

Functions:
- check_stock(drug_id, quantity) -> StockStatus
- check_expiry(batch_id) -> ExpiryStatus
- trigger_reorder(drug_id, quantity) -> ReorderConfirmation
- reserve_inventory(drug_id, quantity, reservation_id) -> bool
- confirm_inventory_deduction(reservation_id) -> bool
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Week 2: Mock inventory data (in-memory)
_mock_inventory = {
	"MTF": {"available": 100, "batch": "B20250401001", "expiry": "2027-04-01"},
	"LSD": {"available": 50, "batch": "B20250405001", "expiry": "2027-04-05"},
	"WSF": {"available": 75, "batch": "B20250410001", "expiry": "2027-04-10"},
	"APX": {"available": 200, "batch": "B20250412001", "expiry": "2027-04-12"},
}


def check_stock(drug_id: str, quantity: float) -> dict:
	"""Check inventory for drug availability and quantity.
	
	WEEK 2 MOCK: Returns from in-memory store, always "in stock" for common drugs.
	WEEK 3: Query actual PostgreSQL inventory database.
	
	Args:
		drug_id: Drug identifier (e.g., "MTF" for Metformin).
		quantity: Quantity required.
		
	Returns:
		dict: Stock status with available, batch_id, expiry_date, alternatives, etc.
	"""
	logger.info(f"Checking stock for {drug_id} (qty: {quantity})")
	
	# Week 2: Mock data - default to in stock for common drugs
	drug_upper = drug_id.upper()
	
	if drug_upper in _mock_inventory:
		stock = _mock_inventory[drug_upper]
		return {
			"available": stock["available"] >= quantity,
			"quantity_on_hand": stock["available"],
			"batch_id": stock["batch"],
			"expiry_date": stock["expiry"],
			"alternatives": [],  # No alternatives needed if in stock
			"reservation_id": None
		}
	
	# Unknown drug: return "in stock" safely (optimistic assumption)
	return {
		"available": True,
		"quantity_on_hand": quantity + 50,  # Assume we have it + buffer
		"batch_id": f"B{datetime.utcnow().strftime('%Y%m%d')}001",
		"expiry_date": (datetime.utcnow() + timedelta(days=365)).strftime("%Y-%m-%d"),
		"alternatives": [],
		"reservation_id": None
	}


def check_expiry(batch_id: str) -> dict:
	"""Validate batch expiry status.
	
	WEEK 2 MOCK: All batches are valid.
	WEEK 3: Query actual inventory database for batch expiry.
	
	Args:
		batch_id: Batch identifier.
		
	Returns:
		dict: Expiry status with expired flag and expiry date.
	"""
	logger.info(f"Checking expiry for batch {batch_id}")
	
	# Week 2: All batches are non-expired (safe default)
	return {
		"expired": False,
		"expiry_date": (datetime.utcnow() + timedelta(days=365)).strftime("%Y-%m-%d"),
		"days_remaining": 365
	}


def trigger_reorder(drug_id: str, quantity: float = None) -> dict:
	"""Trigger reorder workflow for a drug.
	
	WEEK 2 MOCK: Logs and returns success.
	WEEK 3: Actually create reorder in inventory system.
	
	Args:
		drug_id: Drug identifier.
		quantity: Quantity to reorder (optional).
		
	Returns:
		dict: Reorder confirmation.
	"""
	logger.info(f"Triggering reorder for {drug_id} (qty: {quantity})")
	
	# Week 2: Mock - just log and confirm
	return {
		"triggered": True,
		"order_id": f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
		"message": f"Reorder initiated for {drug_id}",
		"estimated_delivery": (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d")
	}


def reserve_inventory(drug_id: str, quantity: float, reservation_id: str) -> bool:
	"""Reserve inventory for a prescription (soft lock).
	
	WEEK 2 MOCK: Always succeeds.
	WEEK 3: Query database and create soft lock.
	
	Args:
		drug_id: Drug identifier.
		quantity: Quantity to reserve.
		reservation_id: Reservation identifier.
		
	Returns:
		bool: True if reservation successful.
	"""
	logger.info(f"Reserving {quantity} units of {drug_id} as {reservation_id}")
	
	# Week 2: Always succeed (safe default for testing)
	return True


def confirm_inventory_deduction(reservation_id: str) -> bool:
	"""Convert reservation to permanent deduction.
	
	WEEK 2 MOCK: Always succeeds.
	WEEK 3: Query database and finalize inventory transaction.
	
	Args:
		reservation_id: Reservation identifier.
		
	Returns:
		bool: True if deduction successful.
	"""
	logger.info(f"Confirming inventory deduction for {reservation_id}")
	
	# Week 2: Always succeed (safe default for testing)
	return True
