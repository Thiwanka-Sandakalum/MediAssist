"""
MediAssistState and related data models for the multi-agent workflow.
"""

from typing_extensions import TypedDict
from typing import Annotated, Optional, Literal, List
from pydantic import BaseModel
import operator

class PrescriptionData(BaseModel):
    prescription_id: str
    patient_id: str
    prescriber_id: str
    drug_name: str
    generic_name: str
    dosage: str
    frequency: str
    duration_days: int
    quantity: float
    raw_text: Optional[str]

class ValidationResult(BaseModel):
    risk_score: float  # 0.0 - 1.0
    interactions: List[dict]
    contraindications: List[dict]
    dosage_safe: bool
    allergy_conflicts: List[str]
    reasoning: str
    requires_human_review: bool

class InventoryStatus(BaseModel):
    available: bool
    quantity_on_hand: float
    batch_id: str
    expiry_date: str
    alternatives: List[dict]
    reservation_id: Optional[str]

class PharmacistApproval(BaseModel):
    pharmacist_id: str
    approved: bool
    action: Literal["APPROVE", "REJECT", "MODIFY"]
    notes: str
    digital_signature: str
    timestamp: str

class MediAssistState(TypedDict):
    # --- Workflow control ---
    workflow_id: str
    current_step: Literal[
        "PENDING",
        "INTAKE_DONE",
        "VALIDATED",
        "INVENTORY_DONE",
        "PREPARED",
        "ACCURACY_DONE",
        "DISPENSED",
        "COUNSELED",
        "RECORDED"
    ]
    workflow_status: Literal["PENDING","IN_PROGRESS","AWAITING_HUMAN","COMPLETE","FAILED"]
    errors: Annotated[List[str], operator.add]  # accumulates errors
    messages: Annotated[List, operator.add]     # LangGraph message history

    # --- Input ---
    prescription_image: Optional[bytes]
    raw_prescription_text: Optional[str]

    # --- Agent outputs (each agent writes to its own slice) ---
    prescription: Optional[PrescriptionData]
    patient_record: Optional[dict]
    validation_result: Optional[ValidationResult]
    inventory_status: Optional[InventoryStatus]
    work_order: Optional[dict]
    label_text: Optional[str]
    accuracy_report: Optional[dict]
    verification_checklist: Optional[List[str]]
    dispensing_record: Optional[dict]
    counseling_notes: Optional[str]
    regulatory_submission: Optional[dict]

    # --- HITL state ---
    awaiting_human: bool
    human_review_context: Optional[str]   # what pharmacist needs to review
    clinical_approval: Optional[PharmacistApproval]
    dispensing_approval: Optional[PharmacistApproval]

    # --- Metadata ---
    created_at: str
    completed_at: Optional[str]
    total_latency_ms: Optional[int]
    llm_cost_usd: Optional[float]  # track per-workflow cost
