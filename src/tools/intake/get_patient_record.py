"""
Patient DB fetch tool for Intake Agent
"""

def get_patient_record(patient_id: str) -> dict:
    """
    Fetch patient record from the database.
    Args:
        patient_id (str): Unique patient identifier.
    Returns:
        dict: Patient record including allergies, current meds, age, conditions.
    """
    """
    Simulated patient record fetch for testing.
    """
    return {
        "patient_id": patient_id,
        "allergies": ["Penicillin"],
        "current_meds": ["Paracetamol"],
        "age": 35,
        "conditions": ["Hypertension"]
    }
