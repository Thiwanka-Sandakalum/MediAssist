"""
Label generator for Preparation Agent
"""

def generate_label(prescription, patient) -> str:
    """
    Generate plain-language label text for prescription.
    Args:
        prescription: Prescription data (PrescriptionData or dict).
        patient: Patient data (dict).
    Returns:
        str: Label text.
    """
    """
    Simulated label generation for testing.
    """
    # Handle both Pydantic models and dicts
    dosage = getattr(prescription, 'dosage', 
                     prescription.get('dosage', '1 tablet') if isinstance(prescription, dict) else '1 tablet')
    drug_name = getattr(prescription, 'drug_name',
                       prescription.get('drug_name', 'Drug') if isinstance(prescription, dict) else 'Drug')
    return f"Take {dosage} of {drug_name} by mouth."
