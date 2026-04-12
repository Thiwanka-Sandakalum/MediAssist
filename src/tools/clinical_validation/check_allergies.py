"""
Allergy checker for Clinical Validation Agent
"""

def check_allergies(drug: str, patient_allergies: list[str]) -> dict:
    """
    Cross-reference drug with patient allergies.
    Args:
        drug (str): Drug name.
        patient_allergies (list): List of allergies.
    Returns:
        dict: Allergy report.
    """
    """
    Simulated allergy check for testing.
    """
    return {
        "drug": drug,
        "allergy_conflict": drug in patient_allergies,
        "conflicts": [drug] if drug in patient_allergies else []
    }
