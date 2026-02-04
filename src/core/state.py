"""
LegacyLens - Task 1: LangGraph State Definition
================================================
Defines the AgentState TypedDict and all state management logic
for the agentic refactoring workflow.

Author: LegacyLens AI Architect
"""

from __future__ import annotations
from typing import TypedDict, Literal, Optional, Annotated, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel, Field
import operator


class ValidationStatus(str, Enum):
    """Enumeration of possible validation outcomes."""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some tests pass, critical ones fail


class RefactorPhase(str, Enum):
    """Current phase in the refactoring lifecycle."""
    ARCHAEOLOGY = "archaeology"
    ARCHITECTURE = "architecture"
    ENGINEERING = "engineering"
    VALIDATION = "validation"
    DOCUMENTATION = "documentation"
    COMPLETED = "completed"


@dataclass
class LogicSchema:
    """
    Structured representation of parsed legacy code logic.
    Output from the Archaeologist agent.
    """
    # Core identifiers
    source_file: str
    language: Literal["cpp", "java", "c"]
    
    # Structural analysis
    classes: list[dict] = field(default_factory=list)
    functions: list[dict] = field(default_factory=list)
    global_variables: list[dict] = field(default_factory=list)
    
    # Memory patterns (critical for C++)
    memory_allocations: list[dict] = field(default_factory=list)
    pointer_operations: list[dict] = field(default_factory=list)
    resource_handles: list[dict] = field(default_factory=list)
    
    # Control flow
    control_flow_graph: dict = field(default_factory=dict)
    call_graph: dict = field(default_factory=dict)
    
    # Dependencies
    includes: list[str] = field(default_factory=list)
    external_dependencies: list[str] = field(default_factory=list)
    
    # Complexity metrics
    cyclomatic_complexity: int = 0
    lines_of_code: int = 0
    
    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage."""
        return {
            "source_file": self.source_file,
            "language": self.language,
            "classes": self.classes,
            "functions": self.functions,
            "global_variables": self.global_variables,
            "memory_allocations": self.memory_allocations,
            "pointer_operations": self.pointer_operations,
            "resource_handles": self.resource_handles,
            "control_flow_graph": self.control_flow_graph,
            "call_graph": self.call_graph,
            "includes": self.includes,
            "external_dependencies": self.external_dependencies,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "lines_of_code": self.lines_of_code,
        }


@dataclass
class DesignMapping:
    """
    Mapping from legacy patterns to modern Pythonic designs.
    Output from the Architect agent.
    """
    # Pattern translations
    pattern_mappings: list[dict] = field(default_factory=list)
    
    # Recommended modern constructs
    async_candidates: list[str] = field(default_factory=list)
    vectorization_opportunities: list[dict] = field(default_factory=list)
    
    # Resource management strategy
    context_managers: list[dict] = field(default_factory=list)
    dataclasses: list[dict] = field(default_factory=list)
    
    # Frontend component mapping
    ui_components: list[dict] = field(default_factory=list)
    api_endpoints: list[dict] = field(default_factory=list)
    
    # Architecture decisions
    design_rationale: str = ""
    risk_assessment: list[dict] = field(default_factory=list)


@dataclass
class GeneratedCode:
    """
    Container for generated modern code artifacts.
    Output from the Engineer agent.
    """
    # Python backend
    python_modules: dict[str, str] = field(default_factory=dict)
    python_tests: dict[str, str] = field(default_factory=dict)
    
    # Next.js frontend
    nextjs_components: dict[str, str] = field(default_factory=dict)
    nextjs_pages: dict[str, str] = field(default_factory=dict)
    api_routes: dict[str, str] = field(default_factory=dict)
    
    # Configuration
    pyproject_toml: str = ""
    package_json: str = ""
    
    # Iteration tracking
    iteration: int = 1
    previous_failures: list[dict] = field(default_factory=list)


@dataclass
class ValidationResult:
    """
    Comprehensive validation results from pytest execution.
    Output from the Validator agent.
    """
    status: ValidationStatus = ValidationStatus.PENDING
    
    # Test results
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0
    
    # Failure details
    failure_details: list[dict] = field(default_factory=list)
    error_traces: list[str] = field(default_factory=list)
    
    # Coverage metrics
    line_coverage: float = 0.0
    branch_coverage: float = 0.0
    
    # Quality gates
    type_check_passed: bool = False
    lint_passed: bool = False
    security_scan_passed: bool = False
    
    # Reflection data for retry
    suggested_fixes: list[dict] = field(default_factory=list)
    root_cause_analysis: str = ""
    
    @property
    def should_retry(self) -> bool:
        """Determine if we should route back to Engineer."""
        return (
            self.status == ValidationStatus.FAILED
            and len(self.suggested_fixes) > 0
        )
    
    @property
    def pass_rate(self) -> float:
        """Calculate test pass percentage."""
        if self.tests_run == 0:
            return 0.0
        return (self.tests_passed / self.tests_run) * 100


@dataclass 
class Documentation:
    """
    Living documentation artifacts.
    Output from the Scribe agent.
    """
    # Main documentation
    readme: str = ""
    architecture_doc: str = ""
    api_reference: str = ""
    
    # Diagrams (Mermaid.js syntax)
    system_diagram: str = ""
    sequence_diagrams: list[str] = field(default_factory=list)
    class_diagrams: list[str] = field(default_factory=list)
    flowcharts: list[str] = field(default_factory=list)
    
    # Migration guide
    migration_guide: str = ""
    breaking_changes: list[str] = field(default_factory=list)
    
    # Changelog
    changelog_entry: str = ""


def merge_messages(left: list[dict], right: list[dict]) -> list[dict]:
    """Reducer function to merge message histories."""
    return left + right


def update_iteration(left: int, right: int) -> int:
    """Reducer to track iteration count."""
    return max(left, right)


class AgentState(TypedDict):
    """
    The central state object that flows through the LangGraph DAG.
    
    This TypedDict defines ALL state that persists across nodes.
    Each agent reads from and writes to specific keys.
    
    State Flow:
    -----------
    Archaeologist -> logic_schema, flow_description
    Architect     -> design_mapping
    Engineer      -> generated_code
    Validator     -> validation_result
    Scribe        -> documentation
    
    Annotations:
    ------------
    - Annotated fields use reducer functions for merging
    - Messages accumulate across all nodes
    - Iteration count tracks retry loops
    """
    
    # ===== INPUT STATE =====
    # Raw legacy source code to be refactored
    legacy_source: str
    
    # Source file metadata
    source_file_path: str
    source_language: Literal["cpp", "java", "c"]
    
    # User preferences
    target_python_version: str  # e.g., "3.11"
    target_nextjs_version: str  # e.g., "14"
    
    # ===== PROCESSING STATE =====
    # Current phase in the workflow
    current_phase: RefactorPhase
    
    # Accumulated messages from all agents (for context)
    messages: Annotated[list[dict], merge_messages]
    
    # Iteration counter (increments on retry loops)
    iteration_count: Annotated[int, update_iteration]
    
    # Maximum retries before failing
    max_retries: int
    
    # ===== NODE A: ARCHAEOLOGIST OUTPUT =====
    logic_schema: Optional[dict]  # Serialized LogicSchema
    flow_description: Optional[str]  # Natural language algorithm description
    
    # ===== NODE B: ARCHITECT OUTPUT =====
    design_mapping: Optional[dict]  # Serialized DesignMapping
    
    # ===== NODE C: ENGINEER OUTPUT =====
    generated_code: Optional[dict]  # Serialized GeneratedCode
    
    # ===== NODE D: VALIDATOR OUTPUT =====
    validation_result: Optional[dict]  # Serialized ValidationResult
    
    # ===== NODE E: SCRIBE OUTPUT =====
    documentation: Optional[dict]  # Serialized Documentation
    
    # ===== ERROR HANDLING =====
    error: Optional[str]
    error_node: Optional[str]
    
    # ===== METADATA =====
    started_at: str  # ISO timestamp
    completed_at: Optional[str]
    total_tokens_used: int


def create_initial_state(
    legacy_source: str,
    source_file_path: str,
    source_language: Literal["cpp", "java", "c"],
    target_python_version: str = "3.11",
    target_nextjs_version: str = "14",
    max_retries: int = 3,
) -> AgentState:
    """
    Factory function to create the initial state for a refactoring job.
    
    Args:
        legacy_source: The raw legacy C++/Java source code
        source_file_path: Path to the source file
        source_language: The source language ('cpp', 'java', 'c')
        target_python_version: Target Python version
        target_nextjs_version: Target Next.js version
        max_retries: Maximum validation retry attempts
        
    Returns:
        Initialized AgentState ready for the workflow
    """
    from datetime import datetime
    
    return AgentState(
        # Input
        legacy_source=legacy_source,
        source_file_path=source_file_path,
        source_language=source_language,
        target_python_version=target_python_version,
        target_nextjs_version=target_nextjs_version,
        
        # Processing
        current_phase=RefactorPhase.ARCHAEOLOGY,
        messages=[],
        iteration_count=1,
        max_retries=max_retries,
        
        # Outputs (initially None)
        logic_schema=None,
        flow_description=None,
        design_mapping=None,
        generated_code=None,
        validation_result=None,
        documentation=None,
        
        # Error handling
        error=None,
        error_node=None,
        
        # Metadata
        started_at=datetime.now().isoformat(),
        completed_at=None,
        total_tokens_used=0,
    )
