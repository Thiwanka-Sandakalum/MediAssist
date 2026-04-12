
"""
Vision Tools (Gemini Vision OCR)
Provides prescription image processing and label generation using Google Gemini Vision API.

Tools:
- parse_prescription_image(image_path) -> dict
- generate_label(prescription, patient) -> str
"""

import logging
from typing import Dict, Optional

from src.tools.vision_service import extract_prescription_from_image, ExtractionError

logger = logging.getLogger(__name__)


async def parse_prescription_image(image_path: str) -> Dict:
    """
    Extract prescription information from an image using Gemini Vision OCR.
    Automatically handles image caching to reduce API calls.
    
    Args:
        image_path: Path to the prescription image file
    
    Returns:
        Dictionary with extracted fields:
        - drug_name: Name of the medication
        - dosage: Numeric dosage value
        - dosage_unit: Unit of measurement (mg, ml, units)
        - frequency: How often to take (e.g., "3 times daily")
        - quantity: Number of units prescribed
        - route: Administration route (oral, IV, topical, etc)
        - duration: Length of treatment (e.g., "7 days")
        - patient_name: Patient name from prescription
        - patient_id: Patient ID if visible
        - prescriber_name: Doctor or practitioner name
        - prescriber_license: License number if visible
        - date: Date of prescription
        - refills: Number of refills
        - special_instructions: Any special instructions
        - confidence_score: Confidence in extraction (0-1)
        - error: Error message if extraction failed
    """
    try:
        result = await extract_prescription_from_image(image_path)
        return {
            "success": True,
            **result
        }
    except FileNotFoundError as e:
        logger.error(f"Image file not found: {e}")
        return {
            "success": False,
            "error": f"Image file not found: {image_path}",
            "error_type": "FileNotFoundError"
        }
    except ExtractionError as e:
        logger.error(f"Vision extraction failed: {e}")
        return {
            "success": False,
            "error": f"Failed to extract prescription data: {e}",
            "error_type": "ExtractionError"
        }
    except Exception as e:
        logger.error(f"Unexpected error during image parsing: {e}")
        return {
            "success": False,
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError"
        }


def generate_label(prescription: Dict, patient: Optional[Dict] = None) -> str:
    """
    Generate pharmacy label text from prescription data.
    
    Args:
        prescription: Prescription data dictionary with keys:
            - drug_name: Name of medication
            - dosage: Dosage amount
            - dosage_unit: Unit of dosage
            - frequency: Dosing frequency
            - quantity: Number of units
            - special_instructions: Any special instructions
            - date: Prescription date
            - prescriber_name: Prescriber name
        
        patient: Optional patient data dictionary with keys:
            - first_name: First name
            - last_name: Last name
            - date_of_birth: DOB
    
    Returns:
        Formatted pharmacy label text
    """
    try:
        # Extract fields with safe defaults
        drug_name = prescription.get("drug_name", "UNKNOWN DRUG")
        dosage = prescription.get("dosage", "UNKNOWN")
        dosage_unit = prescription.get("dosage_unit", "")
        frequency = prescription.get("frequency", "UNKNOWN")
        quantity = prescription.get("quantity", "1")
        special_instructions = prescription.get("special_instructions", "")
        prescriber = prescription.get("prescriber_name", "Unknown Prescriber")
        date = prescription.get("date", "")
        
        # Build label
        label_lines = []
        label_lines.append("=" * 50)
        label_lines.append("PHARMACY LABEL".center(50))
        label_lines.append("=" * 50)
        
        if patient:
            first_name = patient.get("first_name", "")
            last_name = patient.get("last_name", "")
            dob = patient.get("date_of_birth", "")
            label_lines.append(f"Patient: {first_name} {last_name}")
            if dob:
                label_lines.append(f"DOB: {dob}")
        
        label_lines.append("")
        label_lines.append(f"Medication: {drug_name}")
        label_lines.append(f"Strength: {dosage}{dosage_unit if dosage_unit else ''}")
        label_lines.append(f"Quantity: {quantity}")
        label_lines.append("")
        label_lines.append(f"Directions: Take {dosage}{dosage_unit if dosage_unit else ''} {frequency}")
        
        if special_instructions:
            label_lines.append("")
            label_lines.append(f"Special Instructions: {special_instructions}")
        
        label_lines.append("")
        label_lines.append("WARNINGS:")
        label_lines.append("- May cause dizziness or drowsiness")
        label_lines.append("- Do not operate machinery")
        label_lines.append("- Consult pharmacist for interactions")
        
        label_lines.append("")
        label_lines.append(f"Prescribed by: {prescriber}")
        if date:
            label_lines.append(f"Date: {date}")
        
        label_lines.append("")
        label_lines.append("=" * 50)
        label_lines.append("Refill as directed | Keep in cool, dry place")
        label_lines.append("=" * 50)
        
        return "\n".join(label_lines)
    
    except Exception as e:
        logger.error(f"Error generating label: {e}")
        return f"ERROR GENERATING LABEL: {e}"
