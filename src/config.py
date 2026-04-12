"""
Centralized configuration for MediAssist system.
Load from environment variables with sensible defaults.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


class Config:
    """Configuration settings for MediAssist workflow."""
    
    # ============ LLM SETTINGS ============
    LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.1-flash-lite-preview")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))
    LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
    
    # ============ LANGSMITH SETTINGS ============
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
    LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "true").lower() == "true"
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "default")
    
    # ============ CLINICAL VALIDATION SETTINGS ============
    RISK_THRESHOLD = float(os.getenv("RISK_THRESHOLD", "0.7"))
    AUTO_APPROVE_LOW_RISK = os.getenv("AUTO_APPROVE_LOW_RISK", "false").lower() == "true"
    
    # ============ HITL SETTINGS ============
    HITL_TIMEOUT_MINUTES = int(os.getenv("HITL_TIMEOUT_MINUTES", "30"))
    ESCALATE_ON_TIMEOUT = os.getenv("ESCALATE_ON_TIMEOUT", "true").lower() == "true"
    
    # ============ TOOL TIMEOUTS ============
    TOOL_TIMEOUT_SECONDS = int(os.getenv("TOOL_TIMEOUT_SECONDS", "10"))
    OCR_TIMEOUT_SECONDS = int(os.getenv("OCR_TIMEOUT_SECONDS", "15"))
    DATABASE_TIMEOUT_SECONDS = int(os.getenv("DATABASE_TIMEOUT_SECONDS", "5"))
    
    # ============ WORKFLOW SETTINGS ============
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
    ERROR_ACCUMULATION_LIMIT = int(os.getenv("ERROR_ACCUMULATION_LIMIT", "10"))
    
    # ============ LOGGING SETTINGS ============
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # "json" or "text"
    LOG_FILE = os.getenv("LOG_FILE", "pharma_workflow.log")
    
    # ============ DATABASE SETTINGS ============
    # Week 2: CONSOLIDATION - Single PostgreSQL database with multiple schemas
    # Week 3+: Can split into separate databases if needed for scale
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost/mediassist"
    )
    
    # Legacy URLs (kept for compatibility, but not used in Week 2)
    INVENTORY_DB_URL = os.getenv(
        "INVENTORY_DB_URL",
        DATABASE_URL  # Fall back to main database
    )
    PATIENT_DB_URL = os.getenv(
        "PATIENT_DB_URL",
        DATABASE_URL  # Fall back to main database
    )
    
    # ============ API SETTINGS ============
    API_HOST = os.getenv("API_HOST", "127.0.0.1")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_VERSION = "v1"
    
    # ============ FEATURE FLAGS ============
    ENABLE_GEMINI_VISION = os.getenv("ENABLE_GEMINI_VISION", "true").lower() == "true"
    ENABLE_RAG_LAYER = os.getenv("ENABLE_RAG_LAYER", "false").lower() == "true"
    ENABLE_AUDIT_LOG = os.getenv("ENABLE_AUDIT_LOG", "true").lower() == "true"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate critical configuration on startup."""
        missing = []
        
        if not os.getenv("GOOGLE_API_KEY"):
            missing.append("GOOGLE_API_KEY")
        
        if cls.LOG_LEVEL not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            missing.append(f"Invalid LOG_LEVEL: {cls.LOG_LEVEL}")
        
        if missing:
            raise ValueError(f"Missing or invalid config: {', '.join(missing)}")
        
        return True
    
    @classmethod
    def summary(cls) -> dict:
        """Return config summary for logging."""
        return {
            "llm_model": cls.LLM_MODEL,
            "risk_threshold": cls.RISK_THRESHOLD,
            "tool_timeout": cls.TOOL_TIMEOUT_SECONDS,
            "hitl_timeout_minutes": cls.HITL_TIMEOUT_MINUTES,
            "log_level": cls.LOG_LEVEL,
            "audit_enabled": cls.ENABLE_AUDIT_LOG,
        }


# Create singleton instance
config = Config()
