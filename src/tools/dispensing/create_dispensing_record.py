"""
Dispensing record creator for Dispensing Agent
"""

def create_dispensing_record(prescription, patient, pharmacist_id: str, timestamp: str) -> dict:
    """
    Create dispensing record for a prescription.
    Args:
        prescription: Prescription data (PrescriptionData or dict).
        patient: Patient data (dict).
        pharmacist_id (str): Pharmacist identifier.
        timestamp (str): Dispensing timestamp.
    Returns:
        dict: Dispensing record.
    """
    """
    Simulated dispensing record creation for testing.
    """
    prescription_id = getattr(prescription, 'prescription_id',
                             prescription.get('prescription_id', 'RX001') if isinstance(prescription, dict) else 'RX001')
    return {
        "prescription_id": prescription_id,
        "pharmacist_id": pharmacist_id,
        "timestamp": timestamp,
        "status": "DISPENSED"
    }
