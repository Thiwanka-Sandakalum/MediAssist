"""Workflow execution wrapper for MediAssist.

Manages asynchronous graph execution, state updates, and error handling.
Integrates graph.py with FastAPI endpoints.
"""

import logging
import asyncio
import uuid
from typing import Optional
from datetime import datetime

from src.graph import graph
from src.state import MediAssistState, PrescriptionData
from src.api.utils.state_store import WorkflowStore

logger = logging.getLogger(__name__)


async def execute_workflow_async(
	prescription_text: str,
	patient_id: str,
	workflow_id: Optional[str] = None
) -> str:
	"""Execute a prescription workflow asynchronously.
	
	Runs the LangGraph workflow in background, stores state in WorkflowStore.
	Returns immediately with workflow_id for polling.
	
	Args:
		prescription_text: Raw prescription text or image content
		patient_id: Patient identifier
		workflow_id: Optional pre-generated workflow ID (for idempotency)
		
	Returns:
		workflow_id: Unique identifier for tracking this workflow
	"""
	# Generate or use provided workflow ID
	wf_id = workflow_id or f"wf_{uuid.uuid4().hex[:12]}"
	
	# Create initial state
	initial_state: MediAssistState = {
		# Workflow control
		"workflow_id": wf_id,
		"current_step": "INTAKE",
		"workflow_status": "IN_PROGRESS",
		"created_at": datetime.utcnow().isoformat(),
		"updated_at": datetime.utcnow().isoformat(),
		
		# Input data
		"patient_id": patient_id,
		"prescription_text": prescription_text,
		"prescription_image": None,
		"raw_prescription_text": prescription_text,
		
		# Will be filled by agents
		"prescription": None,
		"patient_record": None,
		"validation_result": None,
		"inventory_status": None,
		"dispensing_result": None,
		"counseling_provided": False,
		"accuracy_check_result": None,
		"pharmacy_records": None,
		
		# HITL
		"awaiting_human": False,
		"human_review_context": None,
		"pharmacist_approval": None,
		
		# Metadata
		"errors": [],
		"total_latency_ms": 0,
		"cost_usd": 0.0,
		"tool_calls": 0,
	}
	
	# Store initial state
	WorkflowStore.store(wf_id, initial_state)
	logger.info(f"Started workflow {wf_id} for patient {patient_id}")
	
	# Schedule async execution
	asyncio.create_task(_run_workflow(wf_id, initial_state))
	
	return wf_id


async def _run_workflow(workflow_id: str, initial_state: MediAssistState) -> None:
	"""Internal: Run the workflow to completion.
	
	Executes the LangGraph with error handling, storing state updates.
	This runs in background, called via asyncio.create_task().
	
	Args:
		workflow_id: Workflow identifier
		initial_state: Initial state dict
	"""
	try:
		start_time = datetime.utcnow()
		
		# Execute graph asynchronously (supervisor node is async-only)
		logger.debug(f"Invoking graph for workflow {workflow_id}")
		final_state = await graph.ainvoke(initial_state)
		
		# Update timestamps
		elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
		final_state["updated_at"] = datetime.utcnow().isoformat()
		final_state["total_latency_ms"] = int(elapsed_ms)
		
		# Store final state
		WorkflowStore.update(workflow_id, final_state)
		logger.info(
			f"Workflow {workflow_id} completed: "
			f"status={final_state['workflow_status']}, "
			f"latency={elapsed_ms:.0f}ms"
		)
		
	except Exception as e:
		logger.error(f"Workflow {workflow_id} failed: {str(e)}", exc_info=True)
		
		# Get current state and mark as failed
		current_state = WorkflowStore.get(workflow_id)
		if current_state:
			current_state["workflow_status"] = "FAILED"
			current_state["updated_at"] = datetime.utcnow().isoformat()
			current_state["errors"].append(f"Workflow execution failed: {str(e)}")
			WorkflowStore.update(workflow_id, current_state)


def get_workflow_status(workflow_id: str) -> Optional[dict]:
	"""Get current status of a workflow.
	
	Args:
		workflow_id: Workflow identifier
		
	Returns:
		Dict with workflow status or None if not found
	"""
	state = WorkflowStore.get(workflow_id)
	if not state:
		return None
	
	return {
		"workflow_id": workflow_id,
		"patient_id": state.get("patient_id", ""),
		"current_step": state.get("current_step", "UNKNOWN"),
		"workflow_status": state.get("workflow_status", "UNKNOWN"),
		"created_at": state.get("created_at", ""),
		"updated_at": state.get("updated_at", ""),
		"validation_result": state.get("validation_result"),
		"inventory_status": state.get("inventory_status"),
		"awaiting_human": state.get("awaiting_human", False),
		"human_review_context": state.get("human_review_context"),
		"errors": state.get("errors", []),
		"total_latency_ms": state.get("total_latency_ms", 0),
	}


def get_hitl_review(workflow_id: str) -> Optional[dict]:
	"""Get HITL review details if workflow is awaiting human.
	
	Args:
		workflow_id: Workflow identifier
		
	Returns:
		Dict with review details or None if not applicable
	"""
	state = WorkflowStore.get(workflow_id)
	if not state or not state.get("awaiting_human"):
		return None
	
	return {
		"workflow_id": workflow_id,
		"patient_id": state.get("patient_id", ""),
		"validation_result": state.get("validation_result"),
		"inventory_status": state.get("inventory_status"),
		"human_review_context": state.get("human_review_context", ""),
		"timestamp": state.get("updated_at", ""),
	}


async def process_hitl_approval(
	workflow_id: str,
	approved: bool,
	notes: str,
	pharmacist_id: str
) -> Optional[dict]:
	"""Process pharmacist approval/rejection.
	
	Updates workflow with approval decision and resumes execution.
	Week 2: Store approval. Week 3: Actually resume interrupted LangGraph.
	
	Args:
		workflow_id: Workflow identifier
		approved: Approval decision
		notes: Pharmacist notes
		pharmacist_id: ID of approving pharmacist
		
	Returns:
		Updated workflow status dict
	"""
	state = WorkflowStore.get(workflow_id)
	if not state:
		logger.warning(f"Workflow {workflow_id} not found for approval")
		return None
	
	if not state.get("awaiting_human"):
		logger.warning(f"Workflow {workflow_id} not awaiting human review")
		return None
	
	try:
		# Create approval record
		from src.state import PharmacistApproval
		
		approval = PharmacistApproval(
			pharmacist_id=pharmacist_id,
			approved=approved,
			action="APPROVE" if approved else "REJECT",
			notes=notes,
			digital_signature="",  # Week 3: Add real digital signing
			timestamp=datetime.utcnow().isoformat()
		)
		
		# Update state
		state["pharmacist_approval"] = approval
		state["awaiting_human"] = False
		state["updated_at"] = datetime.utcnow().isoformat()
		
		if approved:
			state["workflow_status"] = "IN_PROGRESS"
			logger.info(f"Workflow {workflow_id} approved by {pharmacist_id}, resuming")
		else:
			state["workflow_status"] = "FAILED"
			state["errors"].append(f"Rejected by {pharmacist_id}: {notes}")
			logger.info(f"Workflow {workflow_id} rejected by {pharmacist_id}")
		
		WorkflowStore.update(workflow_id, state)
		
		# Week 3: Resume interrupted LangGraph here
		# For now, just update state
		
		return {
			"workflow_id": workflow_id,
			"approved": approved,
			"next_step": state["current_step"],
			"message": f"Prescription {'approved' if approved else 'rejected'}"
		}
		
	except Exception as e:
		logger.error(f"Error processing approval for {workflow_id}: {str(e)}")
		return None
