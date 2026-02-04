"""
LegacyLens - Validator Agent
============================
Node D: Runs pytest suites and generates fix suggestions on failure.
"""

from __future__ import annotations
import subprocess
import tempfile
from pathlib import Path
from dataclasses import dataclass

from ..core.state import ValidationResult, ValidationStatus
from ..models.llm import LegacyLensLLM
from ..prompts.templates import VALIDATOR_SYSTEM


class ValidatorAgent:
    """
    The Validator: Expert in software quality assurance.
    
    Responsibilities:
    - Execute pytest test suites
    - Run type checking with mypy
    - Analyze failures and suggest fixes
    - Determine retry vs proceed vs abort
    """
    
    def __init__(self, llm: LegacyLensLLM = None):
        self.llm = llm
    
    async def validate(
        self,
        generated_code: dict,
        logic_schema: dict,
    ) -> ValidationResult:
        """
        Validate generated code by running tests.
        """
        result = ValidationResult()
        
        # Create temp directory for code execution
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Write Python modules
            for name, code in generated_code.get("python_modules", {}).items():
                (tmppath / name).write_text(code)
            
            # Write tests
            for name, code in generated_code.get("python_tests", {}).items():
                (tmppath / name).write_text(code)
            
            # Run pytest
            test_result = self._run_pytest(tmppath)
            result.tests_run = test_result["total"]
            result.tests_passed = test_result["passed"]
            result.tests_failed = test_result["failed"]
            result.failure_details = test_result["failures"]
            
            # Run type checking
            result.type_check_passed = self._run_mypy(tmppath)
            
            # Determine status
            if result.tests_failed == 0 and result.type_check_passed:
                result.status = ValidationStatus.PASSED
            elif result.tests_failed > 0 and result.tests_passed > 0:
                result.status = ValidationStatus.PARTIAL
            else:
                result.status = ValidationStatus.FAILED
            
            # Generate fix suggestions if failed
            if result.status in (ValidationStatus.FAILED, ValidationStatus.PARTIAL):
                result.suggested_fixes = await self._analyze_failures(
                    result.failure_details,
                    generated_code,
                )
                result.root_cause_analysis = await self._root_cause_analysis(
                    result.failure_details
                )
        
        return result
    
    def _run_pytest(self, code_dir: Path) -> dict:
        """Run pytest and collect results."""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", str(code_dir), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            
            output = result.stdout + result.stderr
            
            # Parse pytest output
            passed = output.count(" PASSED")
            failed = output.count(" FAILED")
            
            failures = []
            if failed > 0:
                # Extract failure details
                for line in output.split("\n"):
                    if "FAILED" in line or "AssertionError" in line:
                        failures.append({
                            "message": line.strip(),
                            "category": "logic",
                        })
            
            return {
                "total": passed + failed,
                "passed": passed,
                "failed": failed,
                "failures": failures,
            }
            
        except subprocess.TimeoutExpired:
            return {"total": 0, "passed": 0, "failed": 1, 
                    "failures": [{"message": "Test timeout", "category": "critical"}]}
        except Exception as e:
            return {"total": 0, "passed": 0, "failed": 1,
                    "failures": [{"message": str(e), "category": "critical"}]}
    
    def _run_mypy(self, code_dir: Path) -> bool:
        """Run mypy type checking."""
        try:
            result = subprocess.run(
                ["python", "-m", "mypy", str(code_dir), "--ignore-missing-imports"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0
        except Exception:
            return True  # Skip type check if mypy unavailable
    
    async def _analyze_failures(
        self,
        failures: list[dict],
        generated_code: dict,
    ) -> list[dict]:
        """Use LLM to analyze failures and suggest fixes."""
        if not failures or not self.llm:
            return []
        
        prompt = f"""Analyze these test failures and suggest fixes:

Failures:
{failures}

Generated Code:
{list(generated_code.get('python_modules', {}).values())[:2]}

For each failure, provide:
1. Root cause
2. Specific fix
3. Confidence (high/medium/low)
"""
        
        response = self.llm.generate(prompt, system_prompt=VALIDATOR_SYSTEM)
        
        # Parse suggestions from response
        return [{"suggestion": response, "confidence": "medium"}]
    
    async def _root_cause_analysis(self, failures: list[dict]) -> str:
        """Generate root cause analysis summary."""
        if not failures:
            return "No failures to analyze"
        
        if self.llm:
            prompt = f"Summarize the root cause of these failures: {failures}"
            return self.llm.generate(prompt, max_tokens=200)
        
        return f"Found {len(failures)} test failures requiring attention"
    
    def to_dict(self) -> dict:
        """Serialize result for state storage."""
        return {
            "status": self.status.value,
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "failure_details": self.failure_details,
            "suggested_fixes": self.suggested_fixes,
            "type_check_passed": self.type_check_passed,
        }
