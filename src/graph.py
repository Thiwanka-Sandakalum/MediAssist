

"""
MediAssist LangGraph Construction — Multi-Agent Workflow
"""

# Load environment variables from .env if present
import os
from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import END, START, StateGraph

from src.agent.clinical_validation import clinical_validation_node
from src.agent.intake import intake_node
from src.agent.inventory import inventory_node
from src.agent.preparation import preparation_node
from src.agent.supervisor import supervisor_node
from src.agent.accuracy_check import accuracy_check_node
from src.agent.dispensing import dispensing_node
from src.agent.counseling import counseling_node
from src.agent.records import records_node
from src.state import MediAssistState

# Placeholder for human_review node (HITL gate)
async def human_review_node(state: MediAssistState) -> dict:
    """Pauses workflow for pharmacist review. To be implemented with HITL logic."""
    # In production, this would trigger a notification/UI for pharmacist approval
    return dict(state)

def route_from_supervisor(state: MediAssistState) -> str:
    s = state["workflow_status"]
    if s == "FAILED": return END
    if state.get("awaiting_human"): return "human_review"

    step = state["current_step"]
    routing = {
        "PENDING":          "intake_agent",
        "INTAKE_DONE":      "clinical_validation_agent",
        "VALIDATED":        "inventory_agent",
        "INVENTORY_DONE":   "preparation_agent",
        "PREPARED":         "accuracy_check_agent",
        "ACCURACY_DONE":    "dispensing_agent",
        "DISPENSED":        "counseling_agent",
        "COUNSELED":        "records_agent",
        "RECORDED":         END,
    }
    return routing.get(step, END)

builder = StateGraph(MediAssistState)

# Add all nodes
builder.add_node("supervisor",                supervisor_node)
builder.add_node("intake_agent",              intake_node)
builder.add_node("clinical_validation_agent", clinical_validation_node)
builder.add_node("inventory_agent",           inventory_node)
builder.add_node("preparation_agent",         preparation_node)
builder.add_node("accuracy_check_agent",      accuracy_check_node)
builder.add_node("dispensing_agent",          dispensing_node)
builder.add_node("counseling_agent",          counseling_node)
builder.add_node("records_agent",             records_node)
# builder.add_node("human_review",              human_review_node)  # HITL gate (implement as needed)
builder.add_node("human_review",              human_review_node)  # HITL gate

# Edges: every agent routes back through supervisor
builder.add_edge(START, "supervisor")
builder.add_conditional_edges("supervisor", route_from_supervisor)
for agent in [
    "intake_agent", "clinical_validation_agent",
    "inventory_agent", "preparation_agent",
    "accuracy_check_agent", "dispensing_agent",
    "counseling_agent", "records_agent", # "human_review"
]:
    builder.add_edge(agent, "supervisor")
    builder.add_edge("human_review", "supervisor")

# Compile the graph (add checkpointer as needed)
graph = builder.compile(
    interrupt_before=["human_review"]  # Pauses before human_review for HITL
)
