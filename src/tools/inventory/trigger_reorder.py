"""
Reorder trigger for Inventory Agent
"""

def trigger_reorder(drug_id: str, quantity: float) -> dict:
    """
    Trigger reorder workflow for a drug.
    Args:
        drug_id (str): Drug identifier.
        quantity (float): Quantity to reorder.
    Returns:
        dict: Reorder confirmation.
    """
    """
    Simulated reorder trigger for testing.
    """
    return {
        "drug_id": drug_id,
        "quantity": quantity,
        "status": "REORDERED",
        "confirmation_id": "CONFIRM123"
    }
