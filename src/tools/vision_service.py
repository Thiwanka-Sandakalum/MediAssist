"""
Gemini Vision OCR Service for Prescription Image Processing
Handles extraction of prescription data from images and caches results
"""

import base64
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
from functools import lru_cache

import google.generativeai as genai
from langchain_core.tools import tool
from langchain_core.runnables.utils import ConfigurableField
from pydantic import BaseModel, ValidationError

from src.config import config
from src.utilities.timeout import with_timeout

logger = logging.getLogger(__name__)

# Cache directory for vision results
CACHE_DIR = Path("/tmp/mediassist_vision_cache")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL_HOURS = 24


class ExtractionError(Exception):
    """Raised when vision extraction fails"""
    pass


class PrescriptionExtraction(BaseModel):
    """Extracted prescription data from image"""
    drug_name: str
    dosage: str  # e.g., "500mg"
    dosage_unit: str  # "mg", "ml", "units"
    frequency: str  # "3 times daily"
    quantity: int  # number of units
    route: str  # "oral", "intravenous", "topical"
    duration: Optional[str]  # "7 days"
    patient_name: Optional[str]
    patient_id: Optional[str]
    prescriber_name: Optional[str]
    prescriber_license: Optional[str]
    date: Optional[str]
    refills: int = 0
    special_instructions: Optional[str]
    confidence_score: float  # 0-1 confidence in extraction


class VisionService:
    """Service for extracting prescription data from images using Gemini Vision"""
    
    def __init__(self):
        """Initialize Gemini Vision API client"""
        genai.configure(api_key=config.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        self.cache = {}
        self._load_cache_from_disk()
    
    def _load_cache_from_disk(self):
        """Load cached extractions from disk"""
        try:
            for cache_file in CACHE_DIR.glob("*.json"):
                file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
                if file_age < timedelta(hours=CACHE_TTL_HOURS):
                    with open(cache_file, "r") as f:
                        data = json.load(f)
                        self.cache[data["image_hash"]] = data["extraction"]
                else:
                    cache_file.unlink()  # Remove expired cache
        except Exception as e:
            logger.warning(f"Failed to load cache from disk: {e}")
    
    def _get_image_hash(self, image_path: str) -> str:
        """Generate hash of image for caching"""
        import hashlib
        with open(image_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def _save_to_cache(self, image_hash: str, extraction: Dict):
        """Save extraction result to cache"""
        try:
            cache_file = CACHE_DIR / f"{image_hash}.json"
            with open(cache_file, "w") as f:
                json.dump({"image_hash": image_hash, "extraction": extraction}, f)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for API transmission"""
        with open(image_path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")
    
    def _parse_extraction(self, response_text: str) -> PrescriptionExtraction:
        """Parse Gemini response into structured format"""
        try:
            # Try to extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
            
            return PrescriptionExtraction(**data)
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            logger.warning(f"Failed to parse extraction: {e}")
            raise ExtractionError(f"Failed to parse vision response: {e}")
    
    @with_timeout(seconds=30)
    async def extract_from_image(self, image_path: str) -> Dict[str, any]:
        """
        Extract prescription data from image using Gemini Vision
        
        Args:
            image_path: Path to prescription image
        
        Returns:
            Dictionary containing extracted prescription data
        
        Raises:
            ExtractionError: If extraction fails
            FileNotFoundError: If image file not found
        """
        try:
            # Check if image exists
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            # Check cache
            image_hash = self._get_image_hash(image_path)
            if image_hash in self.cache:
                logger.info(f"Cache hit for image: {image_path}")
                return self.cache[image_hash]
            
            # Encode image
            image_b64 = self._encode_image(image_path)
            
            # Prepare extraction prompt
            extraction_prompt = """
            Analyze this prescription image and extract all relevant information.
            Return a JSON object with the following fields:
            {
                "drug_name": "Name of the medication",
                "dosage": "Numerical dosage value",
                "dosage_unit": "mg/ml/units",
                "frequency": "How often to take (e.g., 3 times daily)",
                "quantity": "Number of units prescribed",
                "route": "oral/intravenous/topical/etc",
                "duration": "How long to take (e.g., 7 days)",
                "patient_name": "Patient name if visible",
                "patient_id": "Patient ID if visible",
                "prescriber_name": "Doctor/prescriber name",
                "prescriber_license": "License number if visible",
                "date": "Date of prescription",
                "refills": "Number of refills",
                "special_instructions": "Any special instructions",
                "confidence_score": "Your confidence in the extraction (0-1)"
            }
            
            If any field is not visible or unclear, use null for that field.
            Ensure confidence_score reflects uncertainty about any of the fields.
            """
            
            # Call Gemini Vision API
            response = self.model.generate_content([
                extraction_prompt,
                {
                    "mime_type": "image/jpeg",
                    "data": image_b64,
                }
            ])
            
            # Parse response
            extraction = self._parse_extraction(response.text)
            result = extraction.model_dump()
            
            # Cache result
            self._save_to_cache(image_hash, result)
            self.cache[image_hash] = result
            
            logger.info(f"Successfully extracted prescription from image: {image_path}")
            return result
            
        except FileNotFoundError as e:
            logger.error(f"Image file not found: {e}")
            raise
        except ExtractionError as e:
            logger.error(f"Extraction error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during extraction: {e}")
            raise ExtractionError(f"Failed to extract from image: {e}")


# Global service instance
_vision_service: Optional[VisionService] = None


def get_vision_service() -> VisionService:
    """Get or create vision service instance"""
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService()
    return _vision_service


@tool
@with_timeout(seconds=30)
async def extract_prescription_from_image(image_path: str) -> Dict[str, any]:
    """
    Extract prescription information from an image using Gemini Vision OCR.
    Automatically caches results to avoid redundant API calls.
    
    Args:
        image_path: Path to the prescription image file
    
    Returns:
        Dictionary containing:
        - drug_name: Name of medication
        - dosage: Numerical dosage
        - dosage_unit: Unit of dosage (mg, ml, etc)
        - frequency: How often to take
        - quantity: Number of units
        - route: Administration route
        - duration: Length of treatment
        - patient_name: Patient name from prescription
        - prescriber_name: Doctor name
        - confidence_score: Confidence in extraction (0-1)
        - (and other fields)
    
    Raises:
        FileNotFoundError: Image file not found
        ExtractionError: Vision extraction failed
    """
    service = get_vision_service()
    return await service.extract_from_image(image_path)
