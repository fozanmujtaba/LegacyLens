"""
LegacyLens - Unit Tests for Core State
======================================
"""

import pytest
from datetime import datetime

from src.core.state import (
    AgentState,
    create_initial_state,
    RefactorPhase,
    ValidationStatus,
    LogicSchema,
    DesignMapping,
    GeneratedCode,
    ValidationResult,
    Documentation,
    merge_messages,
    update_iteration,
)


class TestAgentState:
    """Tests for AgentState creation and management."""
    
    def test_create_initial_state_minimal(self):
        """Test creating state with minimal required arguments."""
        state = create_initial_state(
            legacy_source="int main() { return 0; }",
            source_file_path="test.cpp",
            source_language="cpp",
        )
        
        assert state["legacy_source"] == "int main() { return 0; }"
        assert state["source_file_path"] == "test.cpp"
        assert state["source_language"] == "cpp"
        assert state["current_phase"] == RefactorPhase.ARCHAEOLOGY
        assert state["iteration_count"] == 1
        assert state["max_retries"] == 3  # default
    
    def test_create_initial_state_full(self):
        """Test creating state with all arguments."""
        state = create_initial_state(
            legacy_source="class Test {}",
            source_file_path="Test.java",
            source_language="java",
            target_python_version="3.12",
            target_nextjs_version="15",
            max_retries=5,
        )
        
        assert state["target_python_version"] == "3.12"
        assert state["target_nextjs_version"] == "15"
        assert state["max_retries"] == 5
    
    def test_initial_state_outputs_are_none(self):
        """Test that all output fields start as None."""
        state = create_initial_state(
            legacy_source="code",
            source_file_path="test.c",
            source_language="c",
        )
        
        assert state["logic_schema"] is None
        assert state["flow_description"] is None
        assert state["design_mapping"] is None
        assert state["generated_code"] is None
        assert state["validation_result"] is None
        assert state["documentation"] is None
        assert state["error"] is None
    
    def test_initial_state_has_timestamp(self):
        """Test that started_at is set correctly."""
        before = datetime.now().isoformat()
        state = create_initial_state(
            legacy_source="code",
            source_file_path="test.cpp",
            source_language="cpp",
        )
        after = datetime.now().isoformat()
        
        assert before <= state["started_at"] <= after
        assert state["completed_at"] is None


class TestRefactorPhase:
    """Tests for RefactorPhase enum."""
    
    def test_all_phases_exist(self):
        """Test that all expected phases are defined."""
        phases = [
            RefactorPhase.ARCHAEOLOGY,
            RefactorPhase.ARCHITECTURE,
            RefactorPhase.ENGINEERING,
            RefactorPhase.VALIDATION,
            RefactorPhase.DOCUMENTATION,
            RefactorPhase.COMPLETED,
        ]
        assert len(phases) == 6
    
    def test_phase_values(self):
        """Test phase string values."""
        assert RefactorPhase.ARCHAEOLOGY.value == "archaeology"
        assert RefactorPhase.COMPLETED.value == "completed"


class TestValidationStatus:
    """Tests for ValidationStatus enum."""
    
    def test_all_statuses_exist(self):
        """Test that all expected statuses are defined."""
        statuses = [
            ValidationStatus.PENDING,
            ValidationStatus.PASSED,
            ValidationStatus.FAILED,
            ValidationStatus.PARTIAL,
        ]
        assert len(statuses) == 4


class TestLogicSchema:
    """Tests for LogicSchema dataclass."""
    
    def test_logic_schema_defaults(self):
        """Test LogicSchema with minimal arguments."""
        schema = LogicSchema(
            source_file="test.cpp",
            language="cpp",
        )
        
        assert schema.source_file == "test.cpp"
        assert schema.language == "cpp"
        assert schema.classes == []
        assert schema.functions == []
        assert schema.cyclomatic_complexity == 0
    
    def test_logic_schema_to_dict(self):
        """Test serialization to dictionary."""
        schema = LogicSchema(
            source_file="test.cpp",
            language="cpp",
            functions=[{"name": "main", "return": "int"}],
        )
        
        result = schema.to_dict()
        
        assert result["source_file"] == "test.cpp"
        assert result["functions"] == [{"name": "main", "return": "int"}]
        assert isinstance(result, dict)


class TestValidationResult:
    """Tests for ValidationResult dataclass."""
    
    def test_validation_result_defaults(self):
        """Test ValidationResult with defaults."""
        result = ValidationResult()
        
        assert result.status == ValidationStatus.PENDING
        assert result.tests_run == 0
        assert result.tests_passed == 0
    
    def test_pass_rate_calculation(self):
        """Test pass rate property."""
        result = ValidationResult(
            tests_run=10,
            tests_passed=8,
            tests_failed=2,
        )
        
        assert result.pass_rate == 80.0
    
    def test_pass_rate_zero_tests(self):
        """Test pass rate with no tests."""
        result = ValidationResult()
        assert result.pass_rate == 0.0
    
    def test_should_retry_logic(self):
        """Test should_retry property."""
        # Should retry: failed with fixes
        result_retry = ValidationResult(
            status=ValidationStatus.FAILED,
            suggested_fixes=[{"fix": "something"}],
        )
        assert result_retry.should_retry is True
        
        # Should not retry: passed
        result_passed = ValidationResult(
            status=ValidationStatus.PASSED,
        )
        assert result_passed.should_retry is False
        
        # Should not retry: failed but no fixes
        result_no_fix = ValidationResult(
            status=ValidationStatus.FAILED,
            suggested_fixes=[],
        )
        assert result_no_fix.should_retry is False


class TestReducerFunctions:
    """Tests for state reducer functions."""
    
    def test_merge_messages(self):
        """Test message merging."""
        left = [{"role": "a", "content": "1"}]
        right = [{"role": "b", "content": "2"}]
        
        result = merge_messages(left, right)
        
        assert len(result) == 2
        assert result[0]["role"] == "a"
        assert result[1]["role"] == "b"
    
    def test_update_iteration(self):
        """Test iteration update (takes max)."""
        assert update_iteration(1, 2) == 2
        assert update_iteration(3, 1) == 3
        assert update_iteration(2, 2) == 2
