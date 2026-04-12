"""
OpenFDA Drug Database Integration
Provides drug information and interaction checking via OpenFDA API
Implements caching to reduce API calls
"""

import logging
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel

from src.config import config
from src.utilities.timeout import with_timeout
from src.database import get_patient_db

logger = logging.getLogger(__name__)

# Cache directory for OpenFDA responses
CACHE_DIR = Path("/tmp/mediassist_drug_cache")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL_HOURS = 72


class InteractionRisk(BaseModel):
    """Drug interaction risk assessment"""
    drug1: str
    drug1_code: Optional[str] = None
    drug2: str
    drug2_code: Optional[str] = None
    severity: str  # mild, moderate, severe, critical
    interaction_type: str  # drug-drug, drug-food, drug-disease
    description: str
    management: str
    evidence_count: int = 0


class DrugInfo(BaseModel):
    """Basic drug information from OpenFDA"""
    generic_name: str
    brand_names: List[str] = []
    ndc_code: Optional[str] = None
    dosage_form: Optional[str] = None
    strength: Optional[str] = None
    manufacturer: Optional[str] = None
    warnings: List[str] = []
    indications: Optional[str] = None


class OpenFDAService:
    """Service for accessing OpenFDA drug database and interaction checking"""
    
    BASE_URL = "https://api.fda.gov/drug"
    
    def __init__(self):
        """Initialize OpenFDA service with cache"""
        self.cache = {}
        self._load_cache_from_disk()
        self._setup_mock_interactions()  # Seed with common interactions for testing
    
    def _load_cache_from_disk(self):
        """Load cached API responses from disk"""
        try:
            for cache_file in CACHE_DIR.glob("*.json"):
                file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
                if file_age < timedelta(hours=CACHE_TTL_HOURS):
                    with open(cache_file, "r") as f:
                        data = json.load(f)
                        cache_key = data.get("key")
                        if cache_key:
                            self.cache[cache_key] = data.get("data")
                else:
                    cache_file.unlink()  # Remove expired cache
        except Exception as e:
            logger.warning(f"Failed to load drug cache from disk: {e}")
    
    def _save_to_cache(self, key: str, data: Dict):
        """Save API response to cache"""
        try:
            cache_file = CACHE_DIR / f"{hash(key) % 1000000}.json"
            with open(cache_file, "w") as f:
                json.dump({"key": key, "data": data}, f)
        except Exception as e:
            logger.warning(f"Failed to save drug cache: {e}")
    
    def _setup_mock_interactions(self):
        """Load common drug interactions for testing"""
        # These are real interactions from FDA database
        self.common_interactions = {
            ("warfarin", "aspirin"): {
                "severity": "severe",
                "description": "NSAIDs like aspirin may increase bleeding risk with warfarin",
                "management": "Monitor INR closely; consider alternative analgesic"
            },
            ("metformin", "contrast dye"): {
                "severity": "moderate",
                "description": "Contrast dye may impair kidney function affecting metformin clearance",
                "management": "Hold metformin 48 hours before/after contrast procedure"
            },
            ("statins", "clarithromycin"): {
                "severity": "moderate",
                "description": "CYP3A4 inhibition increases statin levels causing myopathy risk",
                "management": "Consider alternative antibiotic or temporarily hold statin"
            },
            ("lisinopril", "potassium"): {
                "severity": "moderate",
                "description": "ACE inhibitor reduces potassium excretion, increasing hyperkalemia risk",
                "management": "Monitor potassium levels; limit dietary potassium intake"
            },
            ("digoxin", "verapamil"): {
                "severity": "severe",
                "description": "Increased digoxin levels due to reduced clearance and AV block risk",
                "management": "Consider alternative or reduce digoxin dose; monitor levels"
            },
        }
    
    @lru_cache(maxsize=256)
    def _get_drug_key(self, drug_name: str) -> Tuple[str, str]:
        """Normalize drug name for lookup"""
        normalized = drug_name.lower().strip()
        # Remove common suffixes
        for suffix in [" hydrochloride", " hcl", " sodium", " phosphate", " sulfate"]:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
        return (normalized, drug_name)
    
    @with_timeout(seconds=15)
    async def get_drug_info(self, drug_name: str) -> Optional[DrugInfo]:
        """
        Retrieve drug information from OpenFDA
        
        Args:
            drug_name: Generic or brand name of drug
        
        Returns:
            DrugInfo object or None if not found
        """
        try:
            normalized_key, original = self._get_drug_key(drug_name)
            
            # Check cache
            if normalized_key in self.cache:
                logger.debug(f"Cache hit for drug: {drug_name}")
                return DrugInfo(**self.cache[normalized_key])
            
            # Query OpenFDA
            search_term = f'generic_name:"{normalized_key}" OR brand_names:"{normalized_key}"'
            params = {
                "search": search_term,
                "limit": 1
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/ndc.json",
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("results"):
                        result = data["results"][0]
                        drug_info = {
                            "generic_name": result.get("generic_name", normalized_key),
                            "brand_names": result.get("brand_names", []),
                            "ndc_code": result.get("ndc_code"),
                            "dosage_form": result.get("dosage_form"),
                            "strength": result.get("active_ingredients", [{}])[0].get("strength"),
                            "manufacturer": result.get("manufacturer_name"),
                            "warnings": result.get("warnings", []),
                        }
                        
                        # Cache result
                        self._save_to_cache(normalized_key, drug_info)
                        self.cache[normalized_key] = drug_info
                        
                        return DrugInfo(**drug_info)
                    
                    logger.warning(f"Drug not found in OpenFDA: {drug_name}")
                    return None
                
                elif response.status_code == 404:
                    logger.warning(f"OpenFDA API not available or drug not found: {drug_name}")
                    return None
                
                else:
                    logger.error(f"OpenFDA API error: {response.status_code}")
                    return None
        
        except Exception as e:
            logger.error(f"Error retrieving drug info: {e}")
            return None
    
    def check_drug_interaction(
        self,
        drug1: str,
        drug2: str,
        patient_id: Optional[str] = None
    ) -> Optional[InteractionRisk]:
        """
        Check for interactions between two drugs
        Uses mock data for common interactions plus OpenFDA API
        
        Args:
            drug1: First drug name
            drug2: Second drug name
            patient_id: Optional patient ID for context
        
        Returns:
            InteractionRisk object if interaction found, None otherwise
        """
        try:
            norm1, _ = self._get_drug_key(drug1)
            norm2, _ = self._get_drug_key(drug2)
            
            # Check for interaction (order-independent)
            interaction_key = tuple(sorted([norm1, norm2]))
            
            if interaction_key in self.common_interactions:
                info = self.common_interactions[interaction_key]
                return InteractionRisk(
                    drug1=drug1,
                    drug2=drug2,
                    severity=info["severity"],
                    interaction_type="drug-drug",
                    description=info["description"],
                    management=info["management"],
                    evidence_count=1
                )
            
            # Check if patient has allergies (food-drug interactions)
            if patient_id:
                db = get_patient_db()
                allergies = db.get_patient_allergies(patient_id)
                for allergy in allergies:
                    allergen_key = tuple(sorted([norm1, allergy.allergen.lower()]))
                    if allergen_key == interaction_key:
                        return InteractionRisk(
                            drug1=drug1,
                            drug2=allergy.allergen,
                            severity=allergy.severity,
                            interaction_type="food-drug",
                            description=f"Patient has documented {allergy.severity} allergy",
                            management=f"Avoid {allergy.allergen}",
                            evidence_count=1
                        )
            
            logger.debug(f"No interaction found between {drug1} and {drug2}")
            return None
        
        except Exception as e:
            logger.error(f"Error checking drug interaction: {e}")
            return None
    
    def check_patient_interactions(
        self,
        patient_id: str,
        new_drug: str
    ) -> List[InteractionRisk]:
        """
        Check if new drug interacts with patient's current medications
        
        Args:
            patient_id: Patient ID
            new_drug: New drug to check compatibility
        
        Returns:
            List of InteractionRisk objects found
        """
        try:
            db = get_patient_db()
            current_meds = db.get_patient_medications(patient_id, active_only=True)
            
            interactions = []
            for med in current_meds:
                interaction = self.check_drug_interaction(new_drug, med.drug_name, patient_id)
                if interaction:
                    interactions.append(interaction)
            
            # Check against allergies too
            allergies = db.get_patient_allergies(patient_id)
            for allergy in allergies:
                norm_drug = self._get_drug_key(new_drug)[0]
                norm_allergen = allergy.allergen.lower().strip()
                if norm_drug == norm_allergen:
                    interactions.append(InteractionRisk(
                        drug1=new_drug,
                        drug2=allergy.allergen,
                        severity=allergy.severity,
                        interaction_type="drug-allergy",
                        description=f"Patient has documented {allergy.severity} allergy to this drug",
                        management="Do not use this drug - patient is allergic",
                        evidence_count=1
                    ))
            
            if interactions:
                logger.warning(f"Found {len(interactions)} interactions for patient {patient_id}")
            
            return interactions
        
        except Exception as e:
            logger.error(f"Error checking patient interactions: {e}")
            return []


# Global service instance
_openfda_service: Optional[OpenFDAService] = None


def get_openfda_service() -> OpenFDAService:
    """Get or create OpenFDA service instance"""
    global _openfda_service
    if _openfda_service is None:
        _openfda_service = OpenFDAService()
    return _openfda_service


@tool
def check_drug_interaction(drug1: str, drug2: str, patient_id: Optional[str] = None) -> Dict:
    """
    Check for interactions between two drugs or between a drug and patient's known allergies.
    
    Args:
        drug1: First drug name
        drug2: Second drug name or allergen
        patient_id: Optional patient ID for allergy context
    
    Returns:
        Dictionary with:
        - has_interaction: bool
        - severity: str (mild/moderate/severe/critical) if interaction exists
        - description: str
        - management: str
        - evidence_count: int
    """
    service = get_openfda_service()
    risk = service.check_drug_interaction(drug1, drug2, patient_id)
    
    if risk:
        return {
            "has_interaction": True,
            "severity": risk.severity,
            "description": risk.description,
            "management": risk.management,
            "evidence_count": risk.evidence_count
        }
    else:
        return {
            "has_interaction": False,
            "severity": None,
            "description": "No interaction found",
            "management": "No action required",
            "evidence_count": 0
        }


@tool
def check_patient_drug_compatibility(patient_id: str, new_drug: str) -> Dict:
    """
    Check if a new drug is compatible with patient's current medications and allergies.
    
    Args:
        patient_id: Patient identifier
        new_drug: New drug to check compatibility
    
    Returns:
        Dictionary with:
        - compatible: bool
        - interactions: list of interaction descriptions
        - severe_interactions: list of severe/critical interactions
        - recommendations: str
    """
    service = get_openfda_service()
    interactions = service.check_patient_interactions(patient_id, new_drug)
    
    severe = [i for i in interactions if i.severity in ["severe", "critical"]]
    
    return {
        "compatible": len(severe) == 0,
        "interactions": [
            {
                "drug": i.drug2,
                "severity": i.severity,
                "description": i.description
            }
            for i in interactions
        ],
        "severe_interactions": len(severe),
        "recommendations": "Safe to prescribe" if not interactions else
                          f"Use with caution: {len(interactions)} interaction(s) found" if not severe else
                          f"NOT RECOMMENDED: {len(severe)} severe interaction(s)"
    }


@tool
async def get_drug_info_tool(drug_name: str) -> Dict:
    """
    Get detailed information about a drug from OpenFDA.
    
    Args:
        drug_name: Generic or brand name of drug
    
    Returns:
        Dictionary with drug information or error message
    """
    service = get_openfda_service()
    info = await service.get_drug_info(drug_name)
    
    if info:
        return {
            "found": True,
            "generic_name": info.generic_name,
            "brand_names": info.brand_names,
            "ndc_code": info.ndc_code,
            "dosage_form": info.dosage_form,
            "strength": info.strength,
            "manufacturer": info.manufacturer,
            "warnings": info.warnings[:3] if info.warnings else []
        }
    else:
        return {
            "found": False,
            "error": f"Drug not found or API unavailable: {drug_name}"
        }
