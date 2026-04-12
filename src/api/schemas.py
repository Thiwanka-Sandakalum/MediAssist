"""API request and response schemas for MediAssist.

Pydantic models for type-safe API communication. Used for
request validation and response serialization.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ===== REQUEST SCHEMAS =====

class PrescriptionUploadRequest(BaseModel):
	"""Request body for uploading prescription."""
	patient_id: str = Field(..., description="Unique patient identifier")
	prescription_text: Optional[str] = Field(None, description="Prescription text (if image not available)")
	metadata: Optional[Dict[str, str]] = Field(None, description="Additional metadata")


class HITLApprovalRequest(BaseModel):
	"""Request body for pharmacist approval/rejection."""
	approved: bool = Field(..., description="Approval decision: true to approve, false to reject")
	notes: str = Field(..., description="Pharmacist notes on decision")
	pharmacist_id: str = Field(..., description="ID of approving pharmacist")


# ===== RESPONSE SCHEMAS =====

class ValidationResultResponse(BaseModel):
	"""Clinical validation results."""
	risk_score: float = Field(..., description="Risk score 0.0-1.0")
	interactions: List[Dict[str, Any]] = Field(default_factory=list, description="Drug interactions found")
	contraindications: List[Dict[str, Any]] = Field(default_factory=list, description="Contraindications")
	dosage_safe: bool = Field(..., description="Is dosage safe?")
	allergy_conflicts: List[str] = Field(default_factory=list, description="Allergy conflicts")
	reasoning: str = Field(..., description="Clinical reasoning")
	requires_human_review: bool = Field(..., description="Needs pharmacist review?")


class InventoryStatusResponse(BaseModel):
	"""Inventory check results."""
	available: bool = Field(..., description="Is drug in stock?")
	quantity_on_hand: float = Field(..., description="Quantity available")
	batch_id: str = Field(..., description="Current batch ID")
	expiry_date: str = Field(..., description="Batch expiry date")
	alternatives: List[str] = Field(default_factory=list, description="Alternative drugs if unavailable")
	reservation_id: Optional[str] = Field(None, description="Reservation ID if reserved")


class WorkflowStatusResponse(BaseModel):
	"""Current status of a prescription workflow."""
	workflow_id: str = Field(..., description="Unique workflow ID")
	patient_id: str = Field(..., description="Associated patient ID")
	current_step: str = Field(..., description="Current workflow step")
	workflow_status: str = Field(..., description="Overall status: IN_PROGRESS, AWAITING_HUMAN, COMPLETED, FAILED")
	created_at: str = Field(..., description="Creation timestamp")
	updated_at: str = Field(..., description="Last update timestamp")
	
	# Results from agents
	validation_result: Optional[ValidationResultResponse] = Field(None, description="Clinical validation result")
	inventory_status: Optional[InventoryStatusResponse] = Field(None, description="Inventory check result")
	
	# HITL state
	awaiting_human: bool = Field(False, description="Waiting for pharmacist approval?")
	human_review_context: Optional[str] = Field(None, description="Why HITL is needed")
	
	# Error tracking
	errors: List[str] = Field(default_factory=list, description="Any errors encountered")
	
	class Config:
		"""Pydantic config."""
		json_schema_extra = {
			"example": {
				"workflow_id": "wf_001",
				"patient_id": "P_001",
				"current_step": "VALIDATED",
				"workflow_status": "IN_PROGRESS",
				"created_at": "2026-04-12T06:00:00Z",
				"updated_at": "2026-04-12T06:02:00Z",
				"awaiting_human": False,
				"errors": []
			}
		}


class WorkflowListResponse(BaseModel):
	"""List of workflows (paginated)."""
	total: int = Field(..., description="Total number of workflows")
	limit: int = Field(..., description="Items per page")
	offset: int = Field(..., description="Starting offset")
	items: List[WorkflowStatusResponse] = Field(..., description="Workflow list")


class HITLReviewResponse(BaseModel):
	"""Response when requesting HITL review details."""
	workflow_id: str = Field(..., description="Workflow ID")
	patient_id: str = Field(..., description="Patient ID")
	validation_result: ValidationResultResponse = Field(..., description="Clinical validation results")
	inventory_status: Optional[InventoryStatusResponse] = Field(None, description="Inventory status")
	human_review_context: str = Field(..., description="Why this needs review")
	timestamp: str = Field(..., description="When HITL gate reached")


class ApprovalResponse(BaseModel):
	"""Response after approval/rejection."""
	workflow_id: str = Field(..., description="Updated workflow ID")
	approved: bool = Field(..., description="Approval status")
	next_step: str = Field(..., description="Next workflow step")
	message: str = Field(..., description="User-friendly message")


class HealthResponse(BaseModel):
	"""Health check response."""
	status: str = Field(..., description="Health status: ok or degraded")
	graph: str = Field(..., description="Graph status")
	database: str = Field(..., description="Database connectivity")
	timestamp: str = Field(..., description="Check timestamp")


class ErrorResponse(BaseModel):
	"""Standard error response."""
	error: str = Field(..., description="Error message")
	details: Optional[str] = Field(None, description="Additional details")
	status_code: int = Field(..., description="HTTP status code")
	timestamp: str = Field(..., description="When error occurred")
