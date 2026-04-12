"""
Drug Database Tools
Provides drug lookup, interaction checking, and counseling information.
Integrates with OpenFDA API for comprehensive clinical decision support.
"""

import logging
from typing import Optional, List, Dict

from src.tools.drug_database_openfda import get_openfda_service

logger = logging.getLogger(__name__)

# Counseling templates for common drugs
COUNSELING_DATABASE = {
    "metformin": {
        "indication": "Type 2 diabetes mellitus",
        "counseling_points": [
            "Take with or immediately after meals to reduce GI upset",
            "Can cause vitamin B12 deficiency - periodic blood tests recommended",
            "Hold dose if you have acute illness, dehydration, or before contrast procedures",
            "Report signs of lactic acidosis: difficulty breathing, unusual muscle pain",
            "Does not cause hypoglycemia when used alone"
        ],
        "food_interactions": [
            "Alcohol increases lactic acidosis risk - limit intake",
            "Take with food to minimize GI effects"
        ]
    },
    "lisinopril": {
        "indication": "Hypertension, heart failure",
        "counseling_points": [
            "Take once daily at same time each day",
            "May cause dry cough or dizziness - rise slowly from sitting/lying",
            "Monitor blood pressure regularly",
            "Report signs of angioedema: facial/lip swelling, difficulty breathing",
            "Can elevate potassium levels - avoid potassium supplements unless directed"
        ],
        "food_interactions": [
            "Avoid high-potassium foods (bananas, tomatoes, orange juice)",
            "Salt substitutes may increase potassium; check with pharmacist"
        ]
    },
    "warfarin": {
        "indication": "Thromboembolism prevention",
        "counseling_points": [
            "Requires regular INR monitoring - do not skip appointments",
            "Consistent vitamin K intake important - do not change dietary habits dramatically",
            "Report signs of bleeding: nosebleeds, blood in urine, unusual bruising",
            "Avoid NSAIDs unless approved by healthcare provider",
            "Always inform healthcare providers you take warfarin"
        ],
        "food_interactions": [
            "Maintain consistent vitamin K intake (leafy greens)",
            "Avoid cranberry products - they increase warfarin effect"
        ]
    },
    "atorvastatin": {
        "indication": "High cholesterol, cardiovascular disease prevention",
        "counseling_points": [
            "Take with or without food, preferably in evening",
            "Report muscle pain or weakness - may indicate myositis",
            "Continue even if you feel well - treating risk factor",
            "Combine with diet and exercise for best results",
            "Can affect liver function - periodic blood tests recommended"
        ],
        "food_interactions": [
            "Grapefruit/grapefruit juice increases drug levels - avoid",
            "Alcohol increases liver damage risk - limit intake"
        ]
    }
}

# Alternative drugs for therapeutic substitution
ALTERNATIVES_DATABASE = {
    "metformin": [
        {"name": "glybeuride", "reason": "Older second-line agent, causes hypoglycemia"},
        {"name": "pioglitazone", "reason": "Insulin sensitizer, alternative mechanism"},
        {"name": "sitagliptin", "reason": "DPP-4 inhibitor, newer agent"}
    ],
    "lisinopril": [
        {"name": "losartan", "reason": "ARB - alternative for ACE inhibitor cough"},
        {"name": "amlodipine", "reason": "Calcium channel blocker, different class"},
        {"name": "enalapril", "reason": "Alternative ACE inhibitor"}
    ],
    "warfarin": [
        {"name": "apixaban", "reason": "Direct Xa inhibitor - no monitoring needed"},
        {"name": "rivaroxaban", "reason": "Direct Xa inhibitor - once daily dosing"},
        {"name": "dabigatran", "reason": "Direct thrombin inhibitor"}
    ]
}


async def lookup_drug_database(drug_name: str) -> Dict:
    """Look up drug information from OpenFDA database."""
    service = get_openfda_service()
    info = await service.get_drug_info(drug_name)
    
    if info:
        return {
            "found": True,
            "generic_name": info.generic_name,
            "brand_names": info.brand_names,
            "dosage_form": info.dosage_form,
            "ndc_code": info.ndc_code,
            "warnings": info.warnings[:3] if info.warnings else []
        }
    else:
        return {
            "found": False,
            "error": f"Drug not found in database: {drug_name}"
        }


def check_drug_interactions(drugs: List[str], patient_id: Optional[str] = None) -> Dict:
    """Check for interactions between multiple drugs."""
    service = get_openfda_service()
    
    all_interactions = []
    max_severity = "none"
    severity_order = {"none": 0, "mild": 1, "moderate": 2, "severe": 3, "critical": 4}
    
    for i in range(len(drugs)):
        for j in range(i + 1, len(drugs)):
            risk = service.check_drug_interaction(drugs[i], drugs[j], patient_id)
            if risk:
                all_interactions.append(risk)
                if severity_order.get(risk.severity, 0) > severity_order.get(max_severity, 0):
                    max_severity = risk.severity
    
    return {
        "has_interactions": len(all_interactions) > 0,
        "severity_level": max_severity,
        "interactions": [
            {
                "drug1": i.drug1,
                "drug2": i.drug2,
                "severity": i.severity,
                "description": i.description,
                "management": i.management
            }
            for i in all_interactions
        ],
        "recommendation": "Safe combination" if max_severity in ["none", "mild"] else
                         f"Use with caution: {max_severity} interaction(s)" if max_severity == "moderate" else
                         "NOT RECOMMENDED - severe interaction"
    }


def get_alternatives(drug_name: str) -> Dict:
    """Get therapeutically equivalent drug alternatives."""
    drug_lower = drug_name.lower().strip()
    
    if drug_lower in ALTERNATIVES_DATABASE:
        alternatives = ALTERNATIVES_DATABASE[drug_lower]
        return {
            "found": True,
            "drug": drug_name,
            "alternatives": alternatives,
            "note": "Therapeutic equivalents available"
        }
    else:
        return {
            "found": False,
            "drug": drug_name,
            "alternatives": [],
            "note": f"No alternatives in database for {drug_name}"
        }


def get_drug_counseling_points(drug_name: str) -> Dict:
    """Get counseling template for a drug."""
    drug_lower = drug_name.lower().strip()
    
    if drug_lower in COUNSELING_DATABASE:
        template = COUNSELING_DATABASE[drug_lower]
        return {
            "found": True,
            "drug": drug_name,
            "indication": template["indication"],
            "counseling_points": template["counseling_points"],
            "food_interactions": template["food_interactions"]
        }
    else:
        return {
            "found": False,
            "drug": drug_name,
            "counseling_points": ["Drug not in counseling database"],
            "note": f"Generic counseling recommended for {drug_name}"
        }


def get_food_interactions(drug_name: str) -> Dict:
    """Get food and dietary interaction information for a drug."""
    drug_lower = drug_name.lower().strip()
    
    if drug_lower in COUNSELING_DATABASE:
        interactions = COUNSELING_DATABASE[drug_lower]["food_interactions"]
        return {
            "found": True,
            "drug": drug_name,
            "food_interactions": interactions
        }
    else:
        return {
            "found": False,
            "drug": drug_name,
            "food_interactions": [],
            "note": f"No food interactions in database for {drug_name}"
        }
