"""
Prescriber validation tool for Intake Agent
"""

def validate_prescriber(prescriber_id: str) -> bool:
    """
    Check if prescriber license is valid and active.
    Args:
        prescriber_id (str): Prescriber identifier.
    Returns:
        bool: True if valid, False otherwise.
    """
    """
    Simulated prescriber validation for testing.
    """
    return prescriber_id.startswith("Dr") or prescriber_id.startswith("dr")
