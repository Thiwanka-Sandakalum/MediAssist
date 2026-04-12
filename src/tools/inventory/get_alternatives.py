"""
Alternative drug finder for Inventory Agent
"""

def get_alternatives(drug_id: str) -> list:
    """
    Get therapeutically equivalent drug alternatives.
    Args:
        drug_id (str): Drug identifier.
    Returns:
        list: List of alternative drugs.
    """
    """
    Simulated alternatives fetch for testing.
    """
    return [
        {"drug_id": drug_id + "_ALT1", "name": "SimulatedAlt1"},
        {"drug_id": drug_id + "_ALT2", "name": "SimulatedAlt2"}
    ]
