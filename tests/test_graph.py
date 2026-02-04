"""
LegacyLens - Unit Tests for Graph Routing
==========================================
"""

import pytest
from src.core.graph import (
    should_retry_or_proceed,
    should_continue_after_error,
    _calculate_pass_rate,
    _are_failures_minor,
)
from src.core.state import ValidationStatus


class TestShouldRetryOrProceed:
    """Tests for the critical routing logic."""
    
    def test_route_to_scribe_on_pass(self):
        """When all tests pass, route to scribe."""
        state = {
            "validation_result": {
                "status": "passed",
                "tests_run": 10,
                "tests_passed": 10,
                "tests_failed": 0,
                "suggested_fixes": [],
            },
            "iteration_count": 1,
            "max_retries": 3,
        }
        
        result = should_retry_or_proceed(state)
        assert result == "scribe"
    
    def test_route_to_engineer_on_fail_with_retries(self):
        """When tests fail and retries available, route to engineer."""
        state = {
            "validation_result": {
                "status": "failed",
                "tests_run": 10,
                "tests_passed": 5,
                "tests_failed": 5,
                "suggested_fixes": [{"fix": "something"}],
            },
            "iteration_count": 1,
            "max_retries": 3,
        }
        
        result = should_retry_or_proceed(state)
        assert result == "engineer"
    
    def test_route_to_scribe_on_high_pass_rate(self):
        """When pass rate >= 90%, proceed to scribe."""
        state = {
            "validation_result": {
                "status": "partial",
                "tests_run": 10,
                "tests_passed": 9,
                "tests_failed": 1,
                "suggested_fixes": [],
            },
            "iteration_count": 1,
            "max_retries": 3,
        }
        
        result = should_retry_or_proceed(state)
        assert result == "scribe"
    
    def test_route_to_error_when_retries_exhausted(self):
        """When retries exhausted and critical failures, route to error."""
        state = {
            "validation_result": {
                "status": "failed",
                "tests_run": 10,
                "tests_passed": 2,
                "tests_failed": 8,
                "suggested_fixes": [],
                "failure_details": [
                    {"category": "critical", "message": "Core logic failed"},
                ],
            },
            "iteration_count": 3,
            "max_retries": 3,
        }
        
        result = should_retry_or_proceed(state)
        # With critical failures and low pass rate, goes to error
        assert result == "error"
    
    def test_route_to_scribe_when_exhausted_but_acceptable(self):
        """When retries exhausted but 70%+ pass rate, proceed."""
        state = {
            "validation_result": {
                "status": "failed",
                "tests_run": 10,
                "tests_passed": 7,
                "tests_failed": 3,
                "suggested_fixes": [],
            },
            "iteration_count": 3,
            "max_retries": 3,
        }
        
        result = should_retry_or_proceed(state)
        assert result == "scribe"
    
    def test_route_to_error_when_no_validation_result(self):
        """When validation result is None, route to error."""
        state = {
            "validation_result": None,
            "iteration_count": 1,
            "max_retries": 3,
        }
        
        result = should_retry_or_proceed(state)
        assert result == "error"
    
    def test_route_to_engineer_partial_with_fixes(self):
        """Partial failure with fixes should retry."""
        state = {
            "validation_result": {
                "status": "partial",
                "tests_run": 10,
                "tests_passed": 6,
                "tests_failed": 4,
                "suggested_fixes": [{"fix": "update logic"}],
            },
            "iteration_count": 2,
            "max_retries": 3,
        }
        
        result = should_retry_or_proceed(state)
        assert result == "engineer"


class TestShouldContinueAfterError:
    """Tests for error recovery logic."""
    
    def test_retry_on_timeout(self):
        """Transient timeout errors should retry."""
        state = {
            "error": "Connection timeout occurred",
            "error_node": "engineer",
            "iteration_count": 1,
        }
        
        result = should_continue_after_error(state)
        assert result == "retry"
    
    def test_retry_on_rate_limit(self):
        """Rate limit errors should retry."""
        state = {
            "error": "Rate_limit exceeded",
            "error_node": "archaeologist",
            "iteration_count": 1,
        }
        
        result = should_continue_after_error(state)
        assert result == "retry"
    
    def test_abort_on_unknown_error(self):
        """Unknown errors should abort."""
        state = {
            "error": "Some random error",
            "error_node": "engineer",
            "iteration_count": 1,
        }
        
        result = should_continue_after_error(state)
        assert result == "abort"
    
    def test_abort_after_retry_attempt(self):
        """Don't retry transient errors more than once."""
        state = {
            "error": "Connection timeout",
            "error_node": "engineer",
            "iteration_count": 2,
        }
        
        result = should_continue_after_error(state)
        assert result == "abort"


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_calculate_pass_rate(self):
        """Test pass rate calculation."""
        assert _calculate_pass_rate({"tests_run": 10, "tests_passed": 8}) == 80.0
        assert _calculate_pass_rate({"tests_run": 0, "tests_passed": 0}) == 0.0
        assert _calculate_pass_rate({"tests_run": 5, "tests_passed": 5}) == 100.0
    
    def test_are_failures_minor_all_minor(self):
        """Test when all failures are minor."""
        validation = {
            "failure_details": [
                {"category": "style", "message": "line too long"},
                {"category": "deprecation", "message": "old API"},
            ]
        }
        
        assert _are_failures_minor(validation) is True
    
    def test_are_failures_minor_has_critical(self):
        """Test when there's a critical failure."""
        validation = {
            "failure_details": [
                {"category": "style", "message": "line too long"},
                {"category": "critical", "message": "assertion failed"},
            ]
        }
        
        assert _are_failures_minor(validation) is False
    
    def test_are_failures_minor_empty(self):
        """Test with no failures."""
        validation = {"failure_details": []}
        assert _are_failures_minor(validation) is True
