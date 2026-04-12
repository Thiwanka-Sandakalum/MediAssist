"""Prescription API routes for MediAssist.

Endpoints for uploading prescriptions, listing, and checking status.
Week 2 MVP: Basic CRUD operations with in-memory state store.
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from src.api.utils.workflow import (
	execute_workflow_async,
	get_workflow_status,
)
from src.api.utils.state_store import WorkflowStore
from src.api.schemas import (
	PrescriptionUploadRequest,
	WorkflowStatusResponse,
	WorkflowListResponse,
	ErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=dict)
async def upload_prescription(request: PrescriptionUploadRequest):
	"""Upload a new prescription for processing.
	
	Accepts prescription text, validates input, and kicks off the workflow
	asynchronously. Returns workflow_id for status polling.
	"""
	try:
		# Validate input
		if not request.patient_id or not request.patient_id.strip():
			raise HTTPException(
				status_code=400,
				detail="patient_id is required"
			)
		
		if not request.prescription_text or not request.prescription_text.strip():
			raise HTTPException(
				status_code=400,
				detail="prescription_text is required"
			)
		
		# Start workflow asynchronously
		workflow_id = await execute_workflow_async(
			prescription_text=request.prescription_text,
			patient_id=request.patient_id
		)
		
		logger.info(f"Started prescription workflow {workflow_id} for patient {request.patient_id}")
		
		return {
			"workflow_id": workflow_id,
			"status": "IN_PROGRESS",
			"message": "Prescription submitted for processing",
			"timestamp": datetime.utcnow().isoformat()
		}
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error uploading prescription: {str(e)}", exc_info=True)
		raise HTTPException(
			status_code=500,
			detail=f"Failed to upload prescription: {str(e)}"
		)


@router.get("/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_prescription_status(workflow_id: str):
	"""Get current status of a workflow."""
	try:
		# Check if workflow exists
		if not WorkflowStore.exists(workflow_id):
			raise HTTPException(
				status_code=404,
				detail=f"Workflow {workflow_id} not found"
			)
		
		# Get full status
		status = get_workflow_status(workflow_id)
		if not status:
			raise HTTPException(
				status_code=404,
				detail=f"Workflow {workflow_id} not found"
			)
		
		logger.debug(f"Retrieved status for workflow {workflow_id}")
		
		return WorkflowStatusResponse(**status)
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error getting prescription status: {str(e)}", exc_info=True)
		raise HTTPException(
			status_code=500,
			detail=f"Failed to get prescription status: {str(e)}"
		)


@router.get("", response_model=WorkflowListResponse)
async def list_prescriptions(
	limit: int = Query(100, ge=1, le=1000),
	offset: int = Query(0, ge=0),
	status_filter: Optional[str] = Query(None, description="Filter by status")
):
	"""List all prescriptions (paginated)."""
	try:
		# Get all workflows from store
		total, items = WorkflowStore.list_all(limit=limit, offset=offset)
		
		# Apply status filter if provided
		if status_filter:
			items = [
				item for item in items
				if item["workflow_status"] == status_filter
			]
			total = len(items)
		
		logger.debug(f"Listed {len(items)} prescriptions (total: {total})")
		
		return WorkflowListResponse(
			total=total,
			limit=limit,
			offset=offset,
			items=[WorkflowStatusResponse(**item) for item in items]
		)
		
	except Exception as e:
		logger.error(f"Error listing prescriptions: {str(e)}", exc_info=True)
		raise HTTPException(
			status_code=500,
			detail=f"Failed to list prescriptions: {str(e)}"
		)
