"""
Stock checker for Inventory Agent
"""

def check_stock(drug_id: str, quantity: float) -> dict:
    """
    Check inventory for drug availability and quantity.
    Args:
        drug_id (str): Drug identifier.
        quantity (float): Quantity required.
    Returns:
        dict: Stock status including available, batch, expiry, etc.
    """
    """
    Simulated inventory check for testing.
    """
    return {
        "available": True,
        "quantity_on_hand": 100.0,
        "batch_id": "BATCH123",
        "expiry_date": "2027-12-31",
        "alternatives": [],
        "reservation_id": "RESV001"
    }
