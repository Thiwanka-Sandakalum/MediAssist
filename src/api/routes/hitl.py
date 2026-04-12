"""HITL (Human-In-The-Loop) approval routes for MediAssist.

Endpoints for pharmacists to review and approve prescriptions that require
human decision-making based on clinical validation results.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from src.api.utils.workflow import (
	get_hitl_review,
	process_hitl_approval,
)
from src.api.utils.state_store import WorkflowStore
from src.api.schemas import (
	HITLReviewResponse,
	HITLApprovalRequest,
	ApprovalResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{workflow_id}/review", response_model=HITLReviewResponse)
async def get_hitl_review_details(workflow_id: str):
	"""Get HITL review details for a prescription.
	
	Retrieves detailed information needed for pharmacist review, including
	clinical validation results, inventory status, and context on why review
	is needed.
	
	Args:
		workflow_id: Workflow identifier
		
	Returns:
		HITLReviewResponse with review details
		
	Raises:
		HTTPException: 404 if workflow not found or not awaiting human review
	"""
	try:
		# Check if workflow exists
		if not WorkflowStore.exists(workflow_id):
			raise HTTPException(
				status_code=404,
				detail=f"Workflow {workflow_id} not found"
			)
		
		# Get HITL review info
		review_info = get_hitl_review(workflow_id)
		if not review_info:
			raise HTTPException(
				status_code=400,
				detail=f"Workflow {workflow_id} is not awaiting human review"
			)
		
		logger.info(f"Retrieved HITL review for workflow {workflow_id}")
		
		return HITLReviewResponse(**review_info)
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error getting HITL review: {str(e)}", exc_info=True)
		raise HTTPException(
			status_code=500,
			detail=f"Failed to get HITL review: {str(e)}"
		)


@router.post("/{workflow_id}/approve", response_model=ApprovalResponse)
async def approve_prescription(
	workflow_id: str,
	request: HITLApprovalRequest
):
	"""Approve a prescription after pharmacist review.
	
	Pharmacist approves the prescription, allowing it to proceed to next steps
	(dispensing, counseling, etc.). Stores approval record with pharmacist ID,
	timestamp, and digital signature.
	
	Args:
		workflow_id: Workflow identifier
		request: HITLApprovalRequest with approval details
		
	Returns:
		ApprovalResponse with updated workflow status
		
	Raises:
		HTTPException: 400 if workflow not awaiting review, 500 if approval fails
	"""
	try:
		# Validate input
		if not request.pharmacist_id or not request.pharmacist_id.strip():
			raise HTTPException(
				status_code=400,
				detail="pharmacist_id is required"
			)
		
		if not request.notes or not request.notes.strip():
			raise HTTPException(
				status_code=400,
				detail="notes are required"
			)
		
		# Process approval
		result = await process_hitl_approval(
			workflow_id=workflow_id,
			approved=True,
			notes=request.notes,
			pharmacist_id=request.pharmacist_id
		)
		
		if not result:
			raise HTTPException(
				status_code=400,
				detail=f"Could not approve workflow {workflow_id}"
			)
		
		logger.info(
			f"Prescription {workflow_id} approved by {request.pharmacist_id}"
		)
		
		return ApprovalResponse(
			workflow_id=workflow_id,
			approved=True,
			next_step="DISPENSING",
			message="Prescription approved and proceeding to dispensing"
		)
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error approving prescription: {str(e)}", exc_info=True)
		raise HTTPException(
			status_code=500,
			detail=f"Failed to approve prescription: {str(e)}"
		)


@router.post("/{workflow_id}/reject", response_model=ApprovalResponse)
async def reject_prescription(
	workflow_id: str,
	request: HITLApprovalRequest
):
	"""Reject a prescription after pharmacist review.
	
	Pharmacist rejects the prescription with notes. Updates workflow status to
	FAILED with rejection reason.
	
	Args:
		workflow_id: Workflow identifier
		request: HITLApprovalRequest with rejection details
		
	Returns:
		ApprovalResponse with rejection confirmation
		
	Raises:
		HTTPException: 400 if workflow not awaiting review, 500 if rejection fails
	"""
	try:
		# Validate input
		if not request.pharmacist_id or not request.pharmacist_id.strip():
			raise HTTPException(
				status_code=400,
				detail="pharmacist_id is required"
			)
		
		if not request.notes or not request.notes.strip():
			raise HTTPException(
				status_code=400,
				detail="rejection reason (notes) is required"
			)
		
		# Process rejection
		result = await process_hitl_approval(
			workflow_id=workflow_id,
			approved=False,
			notes=request.notes,
			pharmacist_id=request.pharmacist_id
		)
		
		if not result:
			raise HTTPException(
				status_code=400,
				detail=f"Could not reject workflow {workflow_id}"
			)
		
		logger.info(
			f"Prescription {workflow_id} rejected by {request.pharmacist_id}: {request.notes}"
		)
		
		return ApprovalResponse(
			workflow_id=workflow_id,
			approved=False,
			next_step="END",
			message=f"Prescription rejected: {request.notes}"
		)
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error rejecting prescription: {str(e)}", exc_info=True)
		raise HTTPException(
			status_code=500,
			detail=f"Failed to reject prescription: {str(e)}"
		)
