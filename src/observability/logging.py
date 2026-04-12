"""
Structured logging for MediAssist workflow.
JSON-formatted logs with context for production debugging.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from src.config import config


# ============ CUSTOM JSON FORMATTER ============

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for parsing."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "workflow_id"):
            log_data["workflow_id"] = record.workflow_id
        if hasattr(record, "step"):
            log_data["step"] = record.step
        if hasattr(record, "agent"):
            log_data["agent"] = record.agent
        if hasattr(record, "error_code"):
            log_data["error_code"] = record.error_code
        
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Format logs as readable text."""
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        msg = (
            f"[{timestamp}] {record.levelname:8} "
            f"[{record.name}] {record.getMessage()}"
        )
        
        if record.exc_info:
            msg += f"\n{self.formatException(record.exc_info)}"
        
        return msg


# ============ LOGGER SETUP ============

def setup_logging() -> None:
    """Configure logging for entire application."""
    
    log_level = getattr(logging, config.LOG_LEVEL, logging.INFO)
    
    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    file_handler = logging.FileHandler(config.LOG_FILE)
    file_handler.setLevel(log_level)
    
    # Format selection
    if config.LOG_FORMAT == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


# ============ CONTEXT LOGGERS ============

def get_agent_logger(agent_name: str) -> logging.Logger:
    """Get logger for an agent."""
    logger = logging.getLogger(f"mediassist.agent.{agent_name}")
    return logger


def get_workflow_logger(workflow_id: str) -> logging.Logger:
    """Get logger for a workflow."""
    logger = logging.getLogger("mediassist.workflow")
    return logger


# ============ HELPER FUNCTIONS ============

def log_agent_start(agent_name: str, step: str, workflow_id: str):
    """Log agent execution start."""
    logger = get_agent_logger(agent_name)
    logger.info(
        f"Starting {agent_name} for step {step}",
        extra={"workflow_id": workflow_id, "step": step, "agent": agent_name}
    )


def log_agent_error(agent_name: str, error: str, workflow_id: str, step: str):
    """Log agent error."""
    logger = get_agent_logger(agent_name)
    logger.error(
        f"Error in {agent_name}: {error}",
        extra={"workflow_id": workflow_id, "step": step, "agent": agent_name}
    )


def log_agent_complete(agent_name: str, step: str, workflow_id: str, 
                       next_step: str, error_count: int = 0):
    """Log agent completion."""
    logger = get_agent_logger(agent_name)
    msg = f"Completed {agent_name}, moving to {next_step}"
    if error_count > 0:
        msg += f" ({error_count} errors accumulated)"
    logger.info(
        msg,
        extra={"workflow_id": workflow_id, "step": step, "agent": agent_name}
    )


def log_workflow_error(workflow_id: str, error: str, step: str):
    """Log workflow-level error."""
    logger = get_workflow_logger(workflow_id)
    logger.error(
        f"Workflow error at {step}: {error}",
        extra={"workflow_id": workflow_id, "step": step}
    )


def log_hitl_triggered(workflow_id: str, reason: str, risk_score: Optional[float] = None):
    """Log HITL escalation."""
    logger = get_workflow_logger(workflow_id)
    msg = f"HITL triggered: {reason}"
    if risk_score is not None:
        msg += f" (risk_score={risk_score:.2f})"
    logger.warning(
        msg,
        extra={"workflow_id": workflow_id, "event": "hitl_escalation"}
    )


def log_hitl_approved(workflow_id: str, approver_id: str):
    """Log HITL approval."""
    logger = get_workflow_logger(workflow_id)
    logger.info(
        f"HITL approved by {approver_id}",
        extra={"workflow_id": workflow_id, "event": "hitl_approval", "approver": approver_id}
    )


def log_workflow_complete(workflow_id: str, status: str, duration_seconds: float):
    """Log workflow completion."""
    logger = get_workflow_logger(workflow_id)
    logger.info(
        f"Workflow completed with status {status} in {duration_seconds:.2f}s",
        extra={"workflow_id": workflow_id, "event": "workflow_complete", "duration": duration_seconds}
    )


# Initialize on import
setup_logging()
