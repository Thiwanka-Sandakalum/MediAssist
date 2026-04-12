
"""
Counseling Agent node for MediAssist
- Generates personalized, plain-language counseling notes, supports translation
"""

from langsmith import traceable
from src.config import config
from src.utilities.timeout import with_timeout
from src.state import MediAssistState
from src.tools.counseling.get_drug_counseling_points import get_drug_counseling_points
from src.tools.counseling.personalise_counseling import personalise_counseling
from src.tools.counseling.translate_counseling import translate_counseling
from src.tools.counseling.get_food_interactions import get_food_interactions
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool

# Instantiate Gemini 2.5 Flash LLM
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview", temperature=0)

# Optionally, bind tools to the LLM (if you want tool-calling)
counseling_tools = [
	get_drug_counseling_points,
	personalise_counseling,
	translate_counseling,
	get_food_interactions,
]
counseling_agent = llm.bind_tools(counseling_tools)


@traceable(name="counseling_node")
@with_timeout(seconds=config.TOOL_TIMEOUT_SECONDS)
async def counseling_node(state: MediAssistState) -> dict:
	"""Counseling agent - generates personalized counseling notes with error handling."""
	errors = []
	
	# VALIDATE INPUTS
	prescription = state.get("prescription")
	patient = state.get("patient_record")
	
	if not prescription or not patient:
		errors.append("Missing prescription or patient data.")
		return {
			"errors": errors,
			"current_step": "COUNSELED",
			"workflow_status": "FAILED"
		}
	
	# TOOL 1: GET COUNSELING POINTS
	counseling_template = None
	try:
		counseling_template = get_drug_counseling_points(prescription.drug_name)
	except Exception as e:
		errors.append(f"Counseling template lookup failed: {str(e)}")
		counseling_template = {
			"points": [f"Take {getattr(prescription, 'dosage', 'as directed')} of {prescription.drug_name}"]
		}
	
	# TOOL 2: PERSONALISE COUNSELING
	counseling_notes = None
	try:
		counseling_notes = personalise_counseling(counseling_template, patient)
	except Exception as e:
		errors.append(f"Counseling personalisation failed: {str(e)}")
		points = counseling_template.get("points", []) if isinstance(counseling_template, dict) else getattr(counseling_template, 'points', [])
		counseling_notes = str(points[0]) if points else "Take as directed."
	
	# TOOL 3: GET FOOD INTERACTIONS
	food_interactions = []
	try:
		food_interactions = get_food_interactions(prescription.drug_name)
	except Exception as e:
		errors.append(f"Food interactions lookup failed: {str(e)}")
		food_interactions = []
	
	# ADD FOOD INTERACTIONS TO NOTES
	if food_interactions:
		counseling_notes += f"\n\nFood/Drug Interactions: {', '.join(food_interactions)}"
	
	return {
		"counseling_notes": counseling_notes,
		"current_step": "COUNSELED",
		"workflow_status": "IN_PROGRESS",
		"errors": errors
	}
