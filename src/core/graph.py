"""
LegacyLens - LangGraph DAG Definition
======================================
Defines the directed acyclic graph (DAG) for the refactoring workflow
with conditional edge routing logic.

Author: LegacyLens AI Architect
"""

from __future__ import annotations
from typing import Literal, Callable, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import (
    AgentState,
    RefactorPhase,
    ValidationStatus,
    create_initial_state,
)


# =============================================================================
# CONDITIONAL EDGE LOGIC
# =============================================================================

def should_retry_or_proceed(state: AgentState) -> Literal["engineer", "scribe", "error"]:
    """
    Critical conditional edge from Validator node.
    
    Decision Logic:
    ---------------
    1. If validation PASSED → proceed to Scribe (documentation)
    2. If validation FAILED and retries remaining → route back to Engineer
    3. If validation FAILED and no retries → route to error handler
    
    The decision is based on:
    - Test pass rate (must be > 80% to proceed)
    - Type checking status
    - Number of iteration attempts vs max_retries
    - Severity of failures (critical vs minor)
    
    Args:
        state: Current AgentState after Validator execution
        
    Returns:
        Next node identifier: "engineer", "scribe", or "error"
    """
    validation = state.get("validation_result")
    iteration = state.get("iteration_count", 1)
    max_retries = state.get("max_retries", 3)
    
    # No validation result means something went wrong
    if validation is None:
        return "error"
    
    status = ValidationStatus(validation.get("status", "pending"))
    pass_rate = _calculate_pass_rate(validation)
    has_suggested_fixes = len(validation.get("suggested_fixes", [])) > 0
    
    # SUCCESS PATH: All tests pass and quality gates met
    if status == ValidationStatus.PASSED:
        return "scribe"
    
    # PARTIAL SUCCESS: High pass rate, proceed with warnings
    if status == ValidationStatus.PARTIAL and pass_rate >= 90.0:
        # Log warning but proceed
        return "scribe"
    
    # RETRY PATH: Failures exist but we have retries and actionable fixes
    if status in (ValidationStatus.FAILED, ValidationStatus.PARTIAL):
        if iteration < max_retries and has_suggested_fixes:
            return "engineer"
        
        # Check if failures are all minor (non-blocking)
        if _are_failures_minor(validation):
            return "scribe"
    
    # FAILURE PATH: Exhausted retries or no actionable fixes
    if iteration >= max_retries:
        # Final attempt failed - check if we can proceed anyway
        if pass_rate >= 70.0:
            return "scribe"  # Proceed with known issues documented
        return "error"
    
    return "error"


def should_continue_after_error(state: AgentState) -> Literal["retry", "abort"]:
    """
    Conditional edge for error recovery.
    
    Determines if the workflow should attempt recovery or abort completely.
    
    Args:
        state: Current state with error information
        
    Returns:
        "retry" to attempt recovery, "abort" to terminate
    """
    error = state.get("error")
    error_node = state.get("error_node")
    iteration = state.get("iteration_count", 1)
    
    # Transient errors that might succeed on retry
    transient_errors = [
        "timeout",
        "rate_limit",
        "connection_error",
        "context_length_exceeded",
    ]
    
    if error and any(te in error.lower() for te in transient_errors):
        if iteration < 2:  # Only retry transient errors once
            return "retry"
    
    return "abort"


def _calculate_pass_rate(validation: dict) -> float:
    """Calculate the test pass percentage."""
    tests_run = validation.get("tests_run", 0)
    tests_passed = validation.get("tests_passed", 0)
    
    if tests_run == 0:
        return 0.0
    return (tests_passed / tests_run) * 100


def _are_failures_minor(validation: dict) -> bool:
    """
    Determine if all test failures are minor/non-critical.
    
    Minor failures include:
    - Style/formatting issues
    - Deprecation warnings
    - Optional feature tests
    
    Critical failures include:
    - Core logic failures
    - Security vulnerabilities
    - Memory safety issues
    """
    failures = validation.get("failure_details", [])
    
    minor_categories = {"style", "deprecation", "warning", "optional"}
    
    for failure in failures:
        category = failure.get("category", "critical").lower()
        if category not in minor_categories:
            return False
    
    return True


# =============================================================================
# NODE IMPLEMENTATIONS (Stubs - Actual logic in agents/)
# =============================================================================

async def archaeologist_node(state: AgentState) -> dict:
    """
    Node A: The Archaeologist
    
    Parses legacy C++/Java code and outputs:
    - Logic Schema (structured JSON)
    - Flow-based algorithm description
    """
    from ..agents.archaeologist import ArchaeologistAgent
    
    agent = ArchaeologistAgent()
    result = await agent.analyze(
        source_code=state["legacy_source"],
        language=state["source_language"],
        file_path=state["source_file_path"],
    )
    
    return {
        "logic_schema": result.logic_schema.to_dict(),
        "flow_description": result.flow_description,
        "current_phase": RefactorPhase.ARCHITECTURE,
        "messages": [{"role": "archaeologist", "content": result.summary}],
    }


async def architect_node(state: AgentState) -> dict:
    """
    Node B: The Architect
    
    Maps Logic Schema to modern Pythonic design patterns.
    """
    from ..agents.architect import ArchitectAgent
    
    agent = ArchitectAgent()
    result = await agent.design(
        logic_schema=state["logic_schema"],
        target_python=state["target_python_version"],
        target_nextjs=state["target_nextjs_version"],
    )
    
    return {
        "design_mapping": result.to_dict(),
        "current_phase": RefactorPhase.ENGINEERING,
        "messages": [{"role": "architect", "content": result.design_rationale}],
    }


async def engineer_node(state: AgentState) -> dict:
    """
    Node C: The Engineer
    
    Generates Python code and Next.js components.
    Incorporates feedback from previous validation attempts.
    """
    from ..agents.engineer import EngineerAgent
    
    agent = EngineerAgent()
    
    # Check if this is a retry iteration
    previous_failures = []
    if state.get("validation_result"):
        previous_failures = state["validation_result"].get("failure_details", [])
    
    result = await agent.generate(
        design_mapping=state["design_mapping"],
        logic_schema=state["logic_schema"],
        flow_description=state["flow_description"],
        previous_failures=previous_failures,
        iteration=state["iteration_count"],
    )
    
    return {
        "generated_code": result.to_dict(),
        "current_phase": RefactorPhase.VALIDATION,
        "messages": [{"role": "engineer", "content": f"Generated code iteration {state['iteration_count']}"}],
    }


async def validator_node(state: AgentState) -> dict:
    """
    Node D: The Validator
    
    Runs pytest suites and quality checks.
    Generates suggested fixes if tests fail.
    """
    from ..agents.validator import ValidatorAgent
    
    agent = ValidatorAgent()
    result = await agent.validate(
        generated_code=state["generated_code"],
        logic_schema=state["logic_schema"],
    )
    
    return {
        "validation_result": result.to_dict(),
        "current_phase": RefactorPhase.DOCUMENTATION if result.status == ValidationStatus.PASSED else RefactorPhase.ENGINEERING,
        "iteration_count": state["iteration_count"] + (1 if result.status != ValidationStatus.PASSED else 0),
        "messages": [{"role": "validator", "content": f"Validation: {result.status.value} ({result.pass_rate:.1f}% pass rate)"}],
    }


async def scribe_node(state: AgentState) -> dict:
    """
    Node E: The Scribe
    
    Generates living documentation with Mermaid.js diagrams.
    """
    from ..agents.scribe import ScribeAgent
    from datetime import datetime
    
    agent = ScribeAgent()
    result = await agent.document(
        logic_schema=state["logic_schema"],
        design_mapping=state["design_mapping"],
        generated_code=state["generated_code"],
        validation_result=state["validation_result"],
    )
    
    return {
        "documentation": result.to_dict(),
        "current_phase": RefactorPhase.COMPLETED,
        "completed_at": datetime.now().isoformat(),
        "messages": [{"role": "scribe", "content": "Documentation generated successfully"}],
    }


async def error_handler_node(state: AgentState) -> dict:
    """
    Error handler node for graceful degradation.
    """
    from datetime import datetime
    
    return {
        "current_phase": RefactorPhase.COMPLETED,
        "completed_at": datetime.now().isoformat(),
        "messages": [{"role": "system", "content": f"Workflow terminated with error: {state.get('error', 'Unknown error')}"}],
    }


# =============================================================================
# GRAPH CONSTRUCTION
# =============================================================================

def build_refactor_graph() -> StateGraph:
    """
    Construct the LangGraph DAG for the refactoring workflow.
    
    Graph Structure:
    ----------------
    
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Archaeologist│
                    │   (Node A)   │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Architect  │
                    │   (Node B)  │
                    └──────┬──────┘
                           │
                           ▼
               ┌───────────────────────┐
               │                       │
               ▼                       │
        ┌─────────────┐                │
        │  Engineer   │◄───────────────┤ Retry Loop
        │   (Node C)  │                │
        └──────┬──────┘                │
               │                       │
               ▼                       │
        ┌─────────────┐                │
        │  Validator  │────────────────┘
        │   (Node D)  │    (if failed)
        └──────┬──────┘
               │ (if passed)
               ▼
        ┌─────────────┐
        │   Scribe    │
        │   (Node E)  │
        └──────┬──────┘
               │
               ▼
        ┌─────────────┐
        │     END     │
        └─────────────┘
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Initialize the graph with our state schema
    workflow = StateGraph(AgentState)
    
    # Add all nodes
    workflow.add_node("archaeologist", archaeologist_node)
    workflow.add_node("architect", architect_node)
    workflow.add_node("engineer", engineer_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("scribe", scribe_node)
    workflow.add_node("error_handler", error_handler_node)
    
    # Set entry point
    workflow.set_entry_point("archaeologist")
    
    # Add linear edges for the main flow
    workflow.add_edge("archaeologist", "architect")
    workflow.add_edge("architect", "engineer")
    workflow.add_edge("engineer", "validator")
    
    # Add conditional edge from validator
    # This is the critical routing decision
    workflow.add_conditional_edges(
        "validator",
        should_retry_or_proceed,
        {
            "engineer": "engineer",  # Retry loop
            "scribe": "scribe",       # Success path
            "error": "error_handler", # Failure path
        }
    )
    
    # Terminal edges
    workflow.add_edge("scribe", END)
    workflow.add_edge("error_handler", END)
    
    return workflow


def compile_graph(checkpointer: bool = True) -> Any:
    """
    Compile the graph with optional checkpointing.
    
    Args:
        checkpointer: Whether to enable state checkpointing
        
    Returns:
        Compiled graph ready for invocation
    """
    workflow = build_refactor_graph()
    
    if checkpointer:
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    return workflow.compile()


# =============================================================================
# MAIN EXECUTION INTERFACE
# =============================================================================

async def run_refactor(
    legacy_source: str,
    source_file_path: str,
    source_language: Literal["cpp", "java", "c"],
    **kwargs
) -> AgentState:
    """
    Main entry point to run the refactoring workflow.
    
    Args:
        legacy_source: Raw legacy source code
        source_file_path: Path to the source file
        source_language: Language of the legacy code
        **kwargs: Additional options (target versions, max retries, etc.)
        
    Returns:
        Final AgentState with all outputs
    """
    # Create initial state
    initial_state = create_initial_state(
        legacy_source=legacy_source,
        source_file_path=source_file_path,
        source_language=source_language,
        **kwargs
    )
    
    # Compile and run the graph
    app = compile_graph(checkpointer=True)
    
    # Execute with thread ID for checkpointing
    config = {"configurable": {"thread_id": source_file_path}}
    
    final_state = await app.ainvoke(initial_state, config)
    
    return final_state
