"""
Gemini Vision OCR tool for Intake Agent
"""

def parse_prescription_image(image_bytes: bytes) -> dict:
    """
    Extract fields from prescription image using OCR.
    Args:
        image_bytes (bytes): Image file bytes.
    Returns:
        dict: Extracted fields (drug name, dose, etc).
    """
    """
    Simulated OCR extraction for testing.
    """
    return {
        "drug_name": "Amoxicillin",
        "dose": "500mg",
        "frequency": "TID",
        "patient_id": "P12345",
        "prescriber": "Dr. Simulated"
    }
