"""
LegacyLens - Archaeologist Agent
================================
Node A: Parses legacy C++/Java code and extracts Logic Schema.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal
import json

from ..core.state import LogicSchema
from ..models.llm import LegacyLensLLM
from ..prompts.templates import ARCHAEOLOGIST_SYSTEM, get_analysis_prompt
from ..memory.manager import MemoryManager, MemoryConfig


@dataclass
class AnalysisResult:
    logic_schema: LogicSchema
    flow_description: str
    summary: str


class ArchaeologistAgent:
    """
    The Archaeologist: Expert in legacy code analysis.
    
    Responsibilities:
    - Parse C++/Java source code
    - Extract structured Logic Schema
    - Generate flow-based algorithm description
    - Identify memory management patterns
    """
    
    def __init__(self, llm: LegacyLensLLM = None):
        self.llm = llm
        self.memory_config = MemoryConfig()
    
    async def analyze(
        self,
        source_code: str,
        language: Literal["cpp", "java", "c"],
        file_path: str,
    ) -> AnalysisResult:
        """
        Analyze legacy source code and extract Logic Schema.
        """
        # Initialize memory manager for large files
        memory = MemoryManager(self.memory_config, self.llm)
        analysis_context = memory.analyze(source_code, language)
        
        if analysis_context["strategy"] == "direct":
            return await self._analyze_direct(source_code, language, file_path)
        else:
            return await self._analyze_chunked(analysis_context, language, file_path)
    
    async def _analyze_direct(
        self,
        source_code: str,
        language: str,
        file_path: str,
    ) -> AnalysisResult:
        """Direct analysis for small files."""
        prompt = get_analysis_prompt(source_code, language, file_path)
        
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=ARCHAEOLOGIST_SYSTEM,
            stop=["```\n\n", "---END---"],
        )
        
        # Parse JSON from response
        schema_dict = self._extract_json(response)
        logic_schema = self._build_logic_schema(schema_dict, file_path, language)
        
        # Generate flow description
        flow_prompt = f"Describe the algorithm flow in plain English:\n{source_code}"
        flow_description = self.llm.generate(flow_prompt, max_tokens=500)
        
        return AnalysisResult(
            logic_schema=logic_schema,
            flow_description=flow_description,
            summary=f"Analyzed {file_path}: {len(schema_dict.get('functions', []))} functions, "
                    f"{len(schema_dict.get('classes', []))} classes",
        )
    
    async def _analyze_chunked(
        self,
        context: dict,
        language: str,
        file_path: str,
    ) -> AnalysisResult:
        """Chunked analysis for large files using RAG/sliding window."""
        chunks = context.get("chunks", [])
        
        all_functions = []
        all_classes = []
        all_memory_ops = []
        
        for chunk in chunks:
            # Analyze each chunk
            chunk_result = await self._analyze_chunk(chunk, language)
            all_functions.extend(chunk_result.get("functions", []))
            all_classes.extend(chunk_result.get("classes", []))
            all_memory_ops.extend(chunk_result.get("memory_allocations", []))
        
        logic_schema = LogicSchema(
            source_file=file_path,
            language=language,
            functions=all_functions,
            classes=all_classes,
            memory_allocations=all_memory_ops,
        )
        
        return AnalysisResult(
            logic_schema=logic_schema,
            flow_description="Multi-chunk analysis completed",
            summary=f"Analyzed {len(chunks)} chunks from {file_path}",
        )
    
    async def _analyze_chunk(self, chunk, language: str) -> dict:
        """Analyze a single code chunk."""
        # Simplified chunk analysis
        return {"functions": [], "classes": [], "memory_allocations": []}
    
    def _extract_json(self, response: str) -> dict:
        """Extract JSON from LLM response."""
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {}
    
    def _build_logic_schema(self, data: dict, file_path: str, language: str) -> LogicSchema:
        """Build LogicSchema from parsed data."""
        return LogicSchema(
            source_file=file_path,
            language=language,
            classes=data.get("classes", []),
            functions=data.get("functions", []),
            memory_allocations=data.get("memory_allocations", []),
            control_flow_graph=data.get("control_flow_graph", {}),
            call_graph=data.get("call_graph", {}),
        )
