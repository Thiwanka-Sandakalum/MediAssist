
"""
Clinical Validation Agent node for MediAssist
- Checks drug interactions, contraindications, allergies, dosage safety
- Calculates risk score and determines if human review is needed
"""

import json
import logging
from typing import List
from pydantic import BaseModel, Field
from langsmith import traceable
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import config
from src.utilities.timeout import with_timeout
from src.state import MediAssistState, ValidationResult

logger = logging.getLogger(__name__)


# Schema for LLM structured output
class ValidationResponse(BaseModel):
	"""Structured response from clinical validation LLM."""
	interactions: List[dict] = Field(description="List of drug interactions found")
	contraindications: List[str] = Field(description="List of contraindications")
	allergies: List[str] = Field(description="List of allergy conflicts")
	dosage_safe: bool = Field(description="Whether dosage is safe")
	risk_score: float = Field(description="Risk score from 0.0 to 1.0")
	reasoning: str = Field(description="Detailed reasoning for assessment")
	requires_human_review: bool = Field(description="Whether human review is required")


# Instantiate Gemini LLM with structured output
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview", temperature=0)
llm_structured = llm.with_structured_output(ValidationResponse)


@traceable(name="clinical_validation_node")
@with_timeout(seconds=config.LLM_TIMEOUT_SECONDS)
async def clinical_validation_node(state: MediAssistState) -> dict:
	errors = []
	prescription = state.get("prescription")
	patient = state.get("patient_record")
	
	if not prescription or not patient:
		errors.append("Missing prescription or patient data.")
		return {"errors": errors, "current_step": "VALIDATED", "workflow_status": "FAILED"}

	try:
		# Create comprehensive prompt for clinical validation
		validation_prompt = f"""You are a clinical pharmacist AI validator. Perform a thorough clinical validation of the following prescription against the patient record.

PRESCRIPTION DATA:
{json.dumps(prescription, indent=2, default=str)}

PATIENT RECORD:
{json.dumps(patient, indent=2, default=str)}

Analyze the following aspects:

1. DRUG INTERACTIONS: Check if the prescribed drug interacts with any current medications. Consider severity (mild, moderate, severe).
2. CONTRAINDICATIONS: Check if the drug is contraindicated for any of the patient's medical conditions.
3. ALLERGIES: Check if the patient has any known allergies to this drug or similar drugs.
4. DOSAGE SAFETY: Evaluate if the prescribed dosage is appropriate for the patient's weight, age, and conditions.
5. RISK ASSESSMENT: Calculate an overall risk score from 0.0 to 1.0 where:
   - 0.0-0.3: Safe, routine prescription
   - 0.3-0.6: Minor concerns, proceed with caution
   - 0.6-0.7: Moderate risk, may need review
   - 0.7-1.0: High risk, requires human review

Respond with valid JSON containing:
- interactions: list of objects with drug, severity, description
- contraindications: list of condition strings
- allergies: list of allergen strings
- dosage_safe: boolean
- risk_score: number between 0.0 and 1.0
- reasoning: string with detailed explanation
- requires_human_review: boolean

Be conservative: when in doubt, escalate. NEVER skip allergy or interaction checks."""

		messages = [
			SystemMessage(content="You are an expert clinical pharmacist validation system."),
			HumanMessage(content=validation_prompt)
		]
		
		# Call LLM with structured output
		try:
			validation_response = await llm_structured.ainvoke(messages)
		except Exception as e:
			errors.append(f"LLM invocation failed: {str(e)}")
			logger.error(f"Clinical validation LLM error: {str(e)}")
			return {
				"validation_result": None,
				"current_step": "VALIDATED",
				"workflow_status": "FAILED",
				"errors": errors
			}
		
		# Build ValidationResult from structured response
		try:
			# Convert string contraindications to dict format
			contraindications = [
				{"condition": c, "severity": "high"} if isinstance(c, str) else c
				for c in validation_response.contraindications
			]
			
			# Ensure interactions are dicts (safety check)
			interactions = [
				i if isinstance(i, dict) else {"drug": str(i), "severity": "unknown", "description": ""}
				for i in validation_response.interactions
			]
			
			validation = ValidationResult(
				risk_score=float(validation_response.risk_score),
				interactions=interactions,
				contraindications=contraindications,
				dosage_safe=validation_response.dosage_safe,
				allergy_conflicts=validation_response.allergies,
				reasoning=validation_response.reasoning,
				requires_human_review=validation_response.requires_human_review
			)
		except Exception as e:
			errors.append(f"Failed to create ValidationResult: {str(e)}")
			logger.error(f"ValidationResult creation error: {str(e)}")
			return {
				"validation_result": None,
				"current_step": "VALIDATED",
				"workflow_status": "FAILED",
				"errors": errors
			}

		return {
			"validation_result": validation,
			"current_step": "VALIDATED",
			"workflow_status": "AWAITING_HUMAN" if validation.requires_human_review else "IN_PROGRESS",
			"errors": errors,
			"awaiting_human": validation.requires_human_review,
			"human_review_context": "High-risk prescription requires pharmacist review" if validation.requires_human_review else None
		}
	
	except Exception as e:
		errors.append(f"Unexpected error in clinical validation: {str(e)}")
		logger.error(f"Clinical validation node error: {str(e)}")
		return {
			"validation_result": None,
			"current_step": "VALIDATED",
			"workflow_status": "FAILED",
			"errors": errors
		}
