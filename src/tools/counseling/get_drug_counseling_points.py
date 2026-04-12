"""
Drug counseling points fetcher for Counseling Agent
"""

def get_drug_counseling_points(drug_id: str) -> dict:
    """
    Get base counseling content for a drug.
    Args:
        drug_id (str): Drug identifier.
    Returns:
        dict: Counseling template.
    """
    """
    Simulated counseling points fetch for testing.
    """
    return {
        "drug_id": drug_id,
        "points": ["Take with food", "Do not skip doses"]
    }
