"""In-memory state store for active workflows.

Week 2 MVP: Simple thread-safe dict with TTL cleanup.
Week 3: Replace with database-backed store for persistence.
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from threading import Lock
from copy import deepcopy

from src.state import MediAssistState

logger = logging.getLogger(__name__)

# Thread-safe storage for active workflows
_workflows: Dict[str, Dict] = {}
_lock = Lock()

# TTL for workflows (auto-delete if not accessed)
WORKFLOW_TTL_HOURS = 24


class WorkflowStore:
	"""Thread-safe store for workflow state."""
	
	@staticmethod
	def store(workflow_id: str, state: MediAssistState) -> None:
		"""Store workflow state.
		
		Args:
			workflow_id: Unique workflow identifier
			state: MediAssistState dict
		"""
		with _lock:
			_workflows[workflow_id] = {
				"state": deepcopy(state),
				"created_at": datetime.utcnow(),
				"accessed_at": datetime.utcnow()
			}
			logger.debug(f"Stored workflow {workflow_id}")
	
	@staticmethod
	def get(workflow_id: str) -> Optional[MediAssistState]:
		"""Retrieve workflow state.
		
		Args:
			workflow_id: Workflow identifier
			
		Returns:
			MediAssistState if found, None otherwise
		"""
		with _lock:
			if workflow_id not in _workflows:
				return None
			
			entry = _workflows[workflow_id]
			entry["accessed_at"] = datetime.utcnow()
			logger.debug(f"Retrieved workflow {workflow_id}")
			return entry["state"]
	
	@staticmethod
	def update(workflow_id: str, state: MediAssistState) -> None:
		"""Update workflow state.
		
		Args:
			workflow_id: Workflow identifier
			state: Updated MediAssistState
		"""
		with _lock:
			if workflow_id in _workflows:
				_workflows[workflow_id]["state"] = deepcopy(state)
				_workflows[workflow_id]["accessed_at"] = datetime.utcnow()
				logger.debug(f"Updated workflow {workflow_id}")
			else:
				logger.warning(f"Workflow {workflow_id} not found for update")
	
	@staticmethod
	def list_all(limit: int = 100, offset: int = 0) -> tuple:
		"""List all workflows (paginated).
		
		Args:
			limit: Max items to return
			offset: Starting offset
			
		Returns:
			Tuple of (total_count, workflows_list)
		"""
		with _lock:
			all_workflows = list(_workflows.items())
			total = len(all_workflows)
			
			# Sort by created_at descending
			all_workflows.sort(
				key=lambda x: x[1]["created_at"],
				reverse=True
			)
			
			# Apply pagination
			paginated = all_workflows[offset:offset + limit]
			
			result = []
			for wf_id, entry in paginated:
				state = entry["state"]
				result.append({
					"workflow_id": wf_id,
					"patient_id": state.get("patient_id", ""),
					"current_step": state.get("current_step", "UNKNOWN"),
					"workflow_status": state.get("workflow_status", "UNKNOWN"),
					"created_at": entry["created_at"].isoformat(),
					"updated_at": entry["accessed_at"].isoformat(),
					"errors": state.get("errors", [])
				})
			
			return total, result
	
	@staticmethod
	def delete(workflow_id: str) -> bool:
		"""Delete a workflow.
		
		Args:
			workflow_id: Workflow identifier
			
		Returns:
			True if deleted, False if not found
		"""
		with _lock:
			if workflow_id in _workflows:
				del _workflows[workflow_id]
				logger.debug(f"Deleted workflow {workflow_id}")
				return True
			return False
	
	@staticmethod
	def cleanup_expired() -> int:
		"""Remove expired workflows (TTL exceeded).
		
		Returns:
			Number of workflows cleaned up
		"""
		with _lock:
			now = datetime.utcnow()
			ttl = timedelta(hours=WORKFLOW_TTL_HOURS)
			
			expired = [
				wf_id for wf_id, entry in _workflows.items()
				if now - entry["accessed_at"] > ttl
			]
			
			for wf_id in expired:
				del _workflows[wf_id]
			
			if expired:
				logger.info(f"Cleaned up {len(expired)} expired workflows")
			
			return len(expired)
	
	@staticmethod
	def count() -> int:
		"""Get count of active workflows.
		
		Returns:
			Number of stored workflows
		"""
		with _lock:
			return len(_workflows)
	
	@staticmethod
	def exists(workflow_id: str) -> bool:
		"""Check if workflow exists.
		
		Args:
			workflow_id: Workflow identifier
			
		Returns:
			True if exists, False otherwise
		"""
		with _lock:
			return workflow_id in _workflows
