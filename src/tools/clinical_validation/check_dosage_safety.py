"""
Dosage safety checker for Clinical Validation Agent
"""

def check_dosage_safety(drug: str, dose: str, patient_weight: float, age: int) -> dict:
    """
    Check if dosage is within therapeutic range.
    Args:
        drug (str): Drug name.
        dose (str): Dosage string.
        patient_weight (float): Patient weight in kg.
        age (int): Patient age in years.
    Returns:
        dict: Dosage safety report.
    """
    """
    Simulated dosage safety check for testing.
    """
    return {
        "drug": drug,
        "dose": dose,
        "safe": True,
        "reason": "Simulated safe dosage."
    }
