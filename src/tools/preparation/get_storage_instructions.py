"""
Storage instructions fetcher for Preparation Agent
"""

def get_storage_instructions(drug_id: str) -> dict:
    """
    Get storage requirements for a drug.
    Args:
        drug_id (str): Drug identifier.
    Returns:
        dict: Storage info (temperature, light, humidity).
    """
    """
    Simulated storage instructions for testing.
    """
    return {
        "drug_id": drug_id,
        "temperature": "2-8C",
        "light": "Protect from light",
        "humidity": "Keep dry"
    }
