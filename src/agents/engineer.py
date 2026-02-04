"""
LegacyLens - Engineer Agent
===========================
Node C: Generates Python code and Next.js frontend components.
"""

from __future__ import annotations
from dataclasses import dataclass, field

from ..core.state import GeneratedCode
from ..models.llm import LegacyLensLLM
from ..prompts.templates import ENGINEER_SYSTEM, get_generation_prompt


class EngineerAgent:
    """
    The Engineer: Expert Python and Next.js developer.
    
    Responsibilities:
    - Generate production Python code
    - Create pytest test suites
    - Build Next.js components
    - Incorporate feedback from validation failures
    """
    
    def __init__(self, llm: LegacyLensLLM = None):
        self.llm = llm
    
    async def generate(
        self,
        design_mapping: dict,
        logic_schema: dict,
        flow_description: str,
        previous_failures: list = None,
        iteration: int = 1,
    ) -> GeneratedCode:
        """Generate Python and Next.js code from design mapping."""
        prompt = get_generation_prompt(
            design_mapping=design_mapping,
            flow_description=flow_description,
            previous_failures=previous_failures or [],
        )
        
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=ENGINEER_SYSTEM,
        )
        
        # Parse generated code
        code = self._parse_generated_code(response, iteration, previous_failures or [])
        
        return code
    
    def _parse_generated_code(
        self,
        response: str,
        iteration: int,
        previous_failures: list,
    ) -> GeneratedCode:
        """Parse code blocks from LLM response."""
        import re
        
        code = GeneratedCode(iteration=iteration, previous_failures=previous_failures)
        
        # Extract Python code blocks
        python_blocks = re.findall(r'```python\s*(.*?)\s*```', response, re.DOTALL)
        for i, block in enumerate(python_blocks):
            if "def test_" in block or "class Test" in block:
                code.python_tests[f"test_{i}.py"] = block
            else:
                code.python_modules[f"module_{i}.py"] = block
        
        # Extract TypeScript/Next.js blocks
        ts_blocks = re.findall(r'```(?:typescript|tsx)\s*(.*?)\s*```', response, re.DOTALL)
        for i, block in enumerate(ts_blocks):
            if "export default" in block:
                code.nextjs_components[f"Component_{i}.tsx"] = block
        
        return code
