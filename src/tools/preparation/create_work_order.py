"""
Work order creator for Preparation Agent
"""

def create_work_order(prescription, patient) -> dict:
    """
    Create structured preparation instructions for pharmacy technician.
    Args:
        prescription: Prescription data (PrescriptionData or dict).
        patient: Patient data (dict).
    Returns:
        dict: Work order instructions.
    """
    """
    Simulated work order creation for testing.
    """
    prescription_id = getattr(prescription, 'prescription_id',
                             prescription.get('prescription_id', 'RX001') if isinstance(prescription, dict) else 'RX001')
    # Try to get batch_id from inventory_status if available
    batch_id = 'BATCH001'
    if hasattr(prescription, 'batch_id'):
        batch_id = prescription.batch_id
    
    return {
        "prescription_id": prescription_id,
        "batch_id": batch_id,
        "instructions": "Prepare as per standard protocol."
    }
