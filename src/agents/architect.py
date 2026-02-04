"""
LegacyLens - Architect Agent
============================
Node B: Maps Logic Schema to modern Pythonic design patterns.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from ..core.state import DesignMapping
from ..models.llm import LegacyLensLLM
from ..prompts.templates import ARCHITECT_SYSTEM, get_design_prompt


class ArchitectAgent:
    """
    The Architect: Expert in modern Python design patterns.
    
    Responsibilities:
    - Map legacy patterns to Pythonic equivalents
    - Identify async/await opportunities
    - Find vectorization candidates
    - Design context managers for resources
    """
    
    def __init__(self, llm: LegacyLensLLM = None):
        self.llm = llm
    
    async def design(
        self,
        logic_schema: dict,
        target_python: str = "3.11",
        target_nextjs: str = "14",
    ) -> DesignMapping:
        """
        Map Logic Schema to modern design patterns.
        """
        language = logic_schema.get("language", "cpp")
        prompt = get_design_prompt(logic_schema, language)
        
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=ARCHITECT_SYSTEM,
        )
        
        # Parse the design mapping from response
        mapping = self._parse_design_mapping(response, logic_schema)
        
        return mapping
    
    def _parse_design_mapping(self, response: str, logic_schema: dict) -> DesignMapping:
        """Parse design mapping from LLM response."""
        mapping = DesignMapping()
        
        # Analyze patterns in logic schema
        mapping.pattern_mappings = self._map_patterns(logic_schema)
        mapping.async_candidates = self._find_async_candidates(logic_schema)
        mapping.vectorization_opportunities = self._find_vectorization(logic_schema)
        mapping.context_managers = self._design_context_managers(logic_schema)
        mapping.design_rationale = response
        
        return mapping
    
    def _map_patterns(self, schema: dict) -> list[dict]:
        """Map legacy patterns to modern equivalents."""
        mappings = []
        
        # Check for singleton patterns
        for cls in schema.get("classes", []):
            if "getInstance" in str(cls.get("methods", [])):
                mappings.append({
                    "legacy": "Singleton",
                    "modern": "Module-level instance or @lru_cache",
                    "class": cls.get("name"),
                })
        
        # Check for factory patterns
        for func in schema.get("functions", []):
            if "create" in func.get("name", "").lower():
                mappings.append({
                    "legacy": "Factory",
                    "modern": "@classmethod constructor",
                    "function": func.get("name"),
                })
        
        return mappings
    
    def _find_async_candidates(self, schema: dict) -> list[str]:
        """Find functions suitable for async/await."""
        candidates = []
        io_indicators = ["read", "write", "fetch", "send", "receive", "query", "request"]
        
        for func in schema.get("functions", []):
            name = func.get("name", "").lower()
            if any(ind in name for ind in io_indicators):
                candidates.append(func.get("name"))
        
        return candidates
    
    def _find_vectorization(self, schema: dict) -> list[dict]:
        """Find loops that could be vectorized with NumPy."""
        opportunities = []
        
        for func in schema.get("functions", []):
            # Look for array processing patterns
            if "loop" in str(func.get("body", "")).lower():
                opportunities.append({
                    "function": func.get("name"),
                    "suggestion": "Consider NumPy vectorization",
                })
        
        return opportunities
    
    def _design_context_managers(self, schema: dict) -> list[dict]:
        """Design context managers for resource handling."""
        managers = []
        
        for alloc in schema.get("memory_allocations", []):
            managers.append({
                "resource": alloc.get("type", "resource"),
                "pattern": "Context manager with __enter__/__exit__",
            })
        
        return managers
