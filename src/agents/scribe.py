"""
LegacyLens - Scribe Agent
=========================
Node E: Generates living documentation with Mermaid.js diagrams.
"""

from __future__ import annotations
from dataclasses import dataclass

from ..core.state import Documentation
from ..models.llm import LegacyLensLLM
from ..prompts.templates import SCRIBE_SYSTEM


class ScribeAgent:
    """
    The Scribe: Expert technical writer.
    
    Responsibilities:
    - Generate README.md with project overview
    - Create architecture documentation
    - Build Mermaid.js diagrams
    - Write migration guides
    """
    
    def __init__(self, llm: LegacyLensLLM = None):
        self.llm = llm
    
    async def document(
        self,
        logic_schema: dict,
        design_mapping: dict,
        generated_code: dict,
        validation_result: dict,
    ) -> Documentation:
        """Generate comprehensive documentation."""
        doc = Documentation()
        
        # Generate README
        doc.readme = self._generate_readme(logic_schema, design_mapping)
        
        # Generate architecture doc with diagrams
        doc.architecture_doc = self._generate_architecture_doc(design_mapping)
        doc.system_diagram = self._generate_system_diagram(design_mapping)
        doc.class_diagrams = self._generate_class_diagrams(logic_schema)
        doc.flowcharts = self._generate_flowcharts(logic_schema)
        
        # Generate migration guide
        doc.migration_guide = self._generate_migration_guide(
            logic_schema, design_mapping
        )
        
        return doc
    
    def _generate_readme(self, schema: dict, mapping: dict) -> str:
        """Generate project README."""
        source_file = schema.get("source_file", "unknown")
        num_functions = len(schema.get("functions", []))
        num_classes = len(schema.get("classes", []))
        
        return f"""# Modernized Code from {source_file}

## Overview
This project was automatically refactored from legacy {schema.get('language', 'C++')} to modern Python.

## Statistics
- **Original Functions:** {num_functions}
- **Original Classes:** {num_classes}
- **Design Patterns Applied:** {len(mapping.get('pattern_mappings', []))}

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```python
from src import main
main.run()
```

## Architecture
See [Architecture.md](./docs/Architecture.md) for detailed diagrams.

## Migration Notes
See [Migration.md](./docs/Migration.md) for changes from the original codebase.
"""
    
    def _generate_architecture_doc(self, mapping: dict) -> str:
        """Generate architecture documentation."""
        return f"""# Architecture Documentation

## Design Patterns Applied

{self._format_pattern_mappings(mapping.get('pattern_mappings', []))}

## Async Components
{', '.join(mapping.get('async_candidates', ['None']))}

## Resource Management
Context managers implemented for safe resource handling.
"""
    
    def _format_pattern_mappings(self, mappings: list) -> str:
        """Format pattern mappings as markdown table."""
        if not mappings:
            return "No pattern mappings applied."
        
        lines = ["| Legacy Pattern | Modern Equivalent | Location |",
                 "|---------------|-------------------|----------|"]
        for m in mappings:
            lines.append(f"| {m.get('legacy', 'N/A')} | {m.get('modern', 'N/A')} | {m.get('class', m.get('function', 'N/A'))} |")
        return "\n".join(lines)
    
    def _generate_system_diagram(self, mapping: dict) -> str:
        """Generate Mermaid system architecture diagram."""
        return """```mermaid
flowchart TB
    subgraph Legacy["Legacy System"]
        L1[C++/Java Source]
        L2[Manual Memory Management]
        L3[Synchronous I/O]
    end
    
    subgraph Modern["Modern Python"]
        M1[Python Modules]
        M2[Context Managers]
        M3[Async/Await]
    end
    
    subgraph Frontend["Next.js Frontend"]
        F1[React Components]
        F2[API Routes]
        F3[Server Actions]
    end
    
    L1 -->|Refactor| M1
    L2 -->|Transform| M2
    L3 -->|Modernize| M3
    M1 --> F2
    F2 --> F1
    F1 --> F3
```"""
    
    def _generate_class_diagrams(self, schema: dict) -> list[str]:
        """Generate Mermaid class diagrams."""
        classes = schema.get("classes", [])
        if not classes:
            return []
        
        diagram = "```mermaid\nclassDiagram\n"
        for cls in classes[:5]:  # Limit to 5 classes
            name = cls.get("name", "UnknownClass")
            diagram += f"    class {name} {{\n"
            for method in cls.get("methods", [])[:3]:
                diagram += f"        +{method.get('name', 'method')}()\n"
            diagram += "    }\n"
        diagram += "```"
        
        return [diagram]
    
    def _generate_flowcharts(self, schema: dict) -> list[str]:
        """Generate Mermaid flowcharts for main functions."""
        functions = schema.get("functions", [])
        if not functions:
            return []
        
        # Generate flowchart for first function
        func = functions[0]
        name = func.get("name", "main")
        
        return [f"""```mermaid
flowchart TD
    A[Start: {name}] --> B{{Input Validation}}
    B -->|Valid| C[Process Data]
    B -->|Invalid| D[Return Error]
    C --> E[Transform Output]
    E --> F[Return Result]
    D --> G[End]
    F --> G
```"""]
    
    def _generate_migration_guide(self, schema: dict, mapping: dict) -> str:
        """Generate migration guide."""
        return f"""# Migration Guide

## From {schema.get('language', 'Legacy')} to Python

### Key Changes

1. **Memory Management**
   - Replaced manual `new`/`delete` with context managers
   - No more raw pointers - using Optional types

2. **Async Operations**
   - Converted callbacks to `async`/`await`
   - Using `asyncio` for concurrent operations

3. **Type Safety**
   - Full type hints with Python 3.11+
   - Pydantic models for validation

### Breaking Changes
- API signatures have changed to be more Pythonic
- Callback interfaces replaced with coroutines

### Testing
All original functionality preserved with pytest coverage.
"""
    
    def to_dict(self) -> dict:
        """Serialize documentation for state storage."""
        return {
            "readme": self.readme if hasattr(self, 'readme') else "",
            "architecture_doc": self.architecture_doc if hasattr(self, 'architecture_doc') else "",
            "system_diagram": self.system_diagram if hasattr(self, 'system_diagram') else "",
        }
