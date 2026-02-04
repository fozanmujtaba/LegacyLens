"""
LegacyLens - Task 3: Memory Efficiency Strategy
================================================
Context window management for large legacy file analysis.

Implements:
1. RAG-based code retrieval with embeddings
2. Sliding window with overlap for sequential processing
3. Hierarchical summarization for large files
4. Smart chunking that respects code boundaries

Author: LegacyLens AI Architect
"""

from __future__ import annotations
from typing import Optional, Literal
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChunkMetadata:
    """Metadata for a code chunk."""
    chunk_id: str
    file_path: str
    start_line: int
    end_line: int
    chunk_type: Literal["class", "function", "block", "import", "other"]
    parent_scope: Optional[str] = None
    token_count: int = 0
    embedding: Optional[list[float]] = None


@dataclass
class MemoryConfig:
    """Configuration for memory-efficient processing."""
    # Context window limits
    max_context_tokens: int = 8192
    reserved_output_tokens: int = 2048
    available_input_tokens: int = 6144  # max - reserved
    
    # Chunking parameters
    chunk_size_tokens: int = 512
    chunk_overlap_tokens: int = 64
    min_chunk_size: int = 100
    
    # RAG parameters
    embedding_model: str = "nomic-embed-text"
    top_k_retrieval: int = 5
    similarity_threshold: float = 0.7
    
    # Summarization
    enable_hierarchical_summary: bool = True
    summary_max_tokens: int = 256


class CodeChunker:
    """
    Smart code chunker that respects syntax boundaries.
    
    Unlike naive text chunking, this ensures chunks don't split:
    - Class definitions
    - Function bodies
    - Control flow blocks
    """
    
    def __init__(self, config: MemoryConfig, llm):
        self.config = config
        self.llm = llm
    
    def chunk_file(self, source_code: str, language: str) -> list[ChunkMetadata]:
        """
        Chunk source code into semantically meaningful pieces.
        
        Strategy:
        1. Parse AST to identify natural boundaries
        2. Group small constructs, split large ones
        3. Maintain overlap for context continuity
        """
        chunks = []
        
        if language == "cpp":
            chunks = self._chunk_cpp(source_code)
        elif language == "java":
            chunks = self._chunk_java(source_code)
        else:
            chunks = self._chunk_generic(source_code)
        
        # Calculate token counts
        for chunk in chunks:
            chunk.token_count = self.llm.count_tokens(
                self._get_chunk_text(source_code, chunk)
            )
        
        return chunks
    
    def _chunk_cpp(self, source: str) -> list[ChunkMetadata]:
        """Parse C++ using regex patterns (full AST would use libclang)."""
        import re
        chunks = []
        lines = source.split('\n')
        
        # Pattern for class/struct definitions
        class_pattern = re.compile(r'^(class|struct)\s+(\w+)')
        func_pattern = re.compile(r'^[\w\s\*&]+\s+(\w+)\s*\([^)]*\)\s*{?')
        
        current_chunk_start = 0
        brace_depth = 0
        
        for i, line in enumerate(lines):
            # Track brace depth for scope detection
            brace_depth += line.count('{') - line.count('}')
            
            # Detect chunk boundaries at depth 0
            if brace_depth == 0 and i > current_chunk_start:
                chunk_text = '\n'.join(lines[current_chunk_start:i+1])
                if chunk_text.strip():
                    chunk_type = self._detect_chunk_type(chunk_text)
                    chunks.append(ChunkMetadata(
                        chunk_id=f"chunk_{len(chunks)}",
                        file_path="",
                        start_line=current_chunk_start + 1,
                        end_line=i + 1,
                        chunk_type=chunk_type,
                    ))
                current_chunk_start = i + 1
        
        return chunks
    
    def _chunk_java(self, source: str) -> list[ChunkMetadata]:
        """Parse Java using regex patterns."""
        return self._chunk_cpp(source)  # Similar brace-based structure
    
    def _chunk_generic(self, source: str) -> list[ChunkMetadata]:
        """Fallback: chunk by line count with overlap."""
        lines = source.split('\n')
        chunks = []
        
        lines_per_chunk = 50
        overlap = 5
        
        for i in range(0, len(lines), lines_per_chunk - overlap):
            end = min(i + lines_per_chunk, len(lines))
            chunks.append(ChunkMetadata(
                chunk_id=f"chunk_{len(chunks)}",
                file_path="",
                start_line=i + 1,
                end_line=end,
                chunk_type="block",
            ))
        
        return chunks
    
    def _detect_chunk_type(self, text: str) -> str:
        """Detect the type of code chunk."""
        if 'class ' in text or 'struct ' in text:
            return "class"
        elif '(' in text and ')' in text and '{' in text:
            return "function"
        elif '#include' in text or 'import ' in text:
            return "import"
        return "other"
    
    def _get_chunk_text(self, source: str, chunk: ChunkMetadata) -> str:
        """Extract chunk text from source."""
        lines = source.split('\n')
        return '\n'.join(lines[chunk.start_line-1:chunk.end_line])


class RAGCodeRetriever:
    """
    RAG-based code retrieval for context-aware analysis.
    
    When analyzing a specific function, retrieves:
    1. Related functions it calls
    2. Classes it uses
    3. Similar patterns from the codebase
    """
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.chunks: list[ChunkMetadata] = []
        self.embeddings_cache: dict[str, list[float]] = {}
    
    def index_codebase(self, chunks: list[ChunkMetadata], source_code: str):
        """Build embedding index for code chunks."""
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(self.config.embedding_model)
            
            for chunk in chunks:
                text = self._get_chunk_text(source_code, chunk)
                embedding = model.encode(text).tolist()
                chunk.embedding = embedding
                self.chunks.append(chunk)
                
        except ImportError:
            logger.warning("sentence-transformers not installed, using fallback")
            self._index_fallback(chunks)
    
    def _index_fallback(self, chunks: list[ChunkMetadata]):
        """Fallback indexing without embeddings."""
        self.chunks = chunks
    
    def retrieve(self, query: str, top_k: Optional[int] = None) -> list[ChunkMetadata]:
        """Retrieve most relevant chunks for a query."""
        k = top_k or self.config.top_k_retrieval
        
        if not self.chunks[0].embedding:
            return self.chunks[:k]  # Fallback: return first k
        
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
            
            model = SentenceTransformer(self.config.embedding_model)
            query_embedding = model.encode(query)
            
            # Cosine similarity
            similarities = []
            for chunk in self.chunks:
                sim = np.dot(query_embedding, chunk.embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(chunk.embedding)
                )
                similarities.append((chunk, sim))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            return [c for c, s in similarities[:k] if s >= self.config.similarity_threshold]
            
        except ImportError:
            return self.chunks[:k]
    
    def _get_chunk_text(self, source: str, chunk: ChunkMetadata) -> str:
        lines = source.split('\n')
        return '\n'.join(lines[chunk.start_line-1:chunk.end_line])


class SlidingWindowProcessor:
    """
    Process large files using a sliding window approach.
    
    Maintains context continuity with overlapping windows.
    """
    
    def __init__(self, config: MemoryConfig, llm):
        self.config = config
        self.llm = llm
    
    def process_large_file(self, source_code: str, process_fn) -> list:
        """
        Process a large file in windows with overlap.
        
        Args:
            source_code: The full source code
            process_fn: Function to call on each window
            
        Returns:
            List of results from each window
        """
        chunks = self._create_windows(source_code)
        results = []
        
        # Track previous context for continuity
        previous_summary = ""
        
        for i, (window_text, metadata) in enumerate(chunks):
            # Build context with previous summary
            context = f"Previous context: {previous_summary}\n\n{window_text}"
            
            # Process this window
            result = process_fn(context, metadata)
            results.append(result)
            
            # Summarize for next iteration
            previous_summary = self._summarize(result)
        
        return results
    
    def _create_windows(self, source: str) -> list[tuple[str, dict]]:
        """Create overlapping windows from source code."""
        windows = []
        
        total_tokens = self.llm.count_tokens(source)
        window_size = self.config.available_input_tokens
        overlap = self.config.chunk_overlap_tokens
        
        if total_tokens <= window_size:
            return [(source, {"window": 0, "total": 1})]
        
        # Estimate characters per token
        chars_per_token = len(source) / total_tokens
        window_chars = int(window_size * chars_per_token)
        overlap_chars = int(overlap * chars_per_token)
        
        start = 0
        window_idx = 0
        
        while start < len(source):
            end = min(start + window_chars, len(source))
            
            # Try to end at a newline
            if end < len(source):
                newline_pos = source.rfind('\n', start, end)
                if newline_pos > start:
                    end = newline_pos + 1
            
            windows.append((
                source[start:end],
                {"window": window_idx, "start_char": start, "end_char": end}
            ))
            
            start = end - overlap_chars
            window_idx += 1
        
        # Add total count to metadata
        for text, meta in windows:
            meta["total"] = window_idx
        
        return windows
    
    def _summarize(self, result) -> str:
        """Create a compact summary for context continuity."""
        if isinstance(result, dict):
            # Summarize key findings
            summary_parts = []
            if "functions" in result:
                funcs = [f.get("name", "") for f in result.get("functions", [])]
                summary_parts.append(f"Functions: {', '.join(funcs[:5])}")
            if "classes" in result:
                classes = [c.get("name", "") for c in result.get("classes", [])]
                summary_parts.append(f"Classes: {', '.join(classes[:5])}")
            return "; ".join(summary_parts)
        return str(result)[:self.config.summary_max_tokens]


class HierarchicalSummarizer:
    """
    Build hierarchical summaries for extremely large codebases.
    
    Level 0: Individual functions/classes
    Level 1: Module summaries
    Level 2: Package summaries
    Level 3: Project summary
    """
    
    def __init__(self, config: MemoryConfig, llm):
        self.config = config
        self.llm = llm
        self.summaries: dict[int, dict[str, str]] = {0: {}, 1: {}, 2: {}, 3: {}}
    
    def build_hierarchy(self, chunks: list[ChunkMetadata], source: str):
        """Build the complete summary hierarchy."""
        # Level 0: Summarize each chunk
        for chunk in chunks:
            text = self._get_chunk_text(source, chunk)
            summary = self._summarize_chunk(text, chunk.chunk_type)
            self.summaries[0][chunk.chunk_id] = summary
        
        # Level 1: Group by parent scope (module)
        modules = {}
        for chunk in chunks:
            scope = chunk.parent_scope or "main"
            if scope not in modules:
                modules[scope] = []
            modules[scope].append(self.summaries[0][chunk.chunk_id])
        
        for module, chunk_summaries in modules.items():
            self.summaries[1][module] = self._merge_summaries(chunk_summaries)
        
        # Level 2 & 3: Further aggregation as needed
        if len(self.summaries[1]) > 1:
            all_module_summaries = list(self.summaries[1].values())
            self.summaries[2]["project"] = self._merge_summaries(all_module_summaries)
    
    def get_context(self, query: str, max_tokens: int) -> str:
        """Get appropriate context level for a query."""
        # Start with highest level summary
        context = self.summaries.get(2, {}).get("project", "")
        tokens = self.llm.count_tokens(context)
        
        # Add more detail if space allows
        if tokens < max_tokens * 0.5:
            for module_summary in self.summaries.get(1, {}).values():
                if tokens + self.llm.count_tokens(module_summary) < max_tokens:
                    context += f"\n\n{module_summary}"
                    tokens = self.llm.count_tokens(context)
        
        return context
    
    def _summarize_chunk(self, text: str, chunk_type: str) -> str:
        prompt = f"Summarize this {chunk_type} in 2 sentences:\n{text}"
        return self.llm.generate(prompt, max_tokens=100)
    
    def _merge_summaries(self, summaries: list[str]) -> str:
        combined = "\n".join(summaries)
        prompt = f"Merge these summaries into one coherent paragraph:\n{combined}"
        return self.llm.generate(prompt, max_tokens=200)
    
    def _get_chunk_text(self, source: str, chunk: ChunkMetadata) -> str:
        lines = source.split('\n')
        return '\n'.join(lines[chunk.start_line-1:chunk.end_line])


class MemoryManager:
    """
    Unified memory management for the LegacyLens pipeline.
    
    Automatically selects the best strategy based on file size:
    - Small files (<4K tokens): Direct processing
    - Medium files (4K-16K): Sliding window
    - Large files (>16K): RAG + Hierarchical summarization
    """
    
    def __init__(self, config: MemoryConfig, llm):
        self.config = config
        self.llm = llm
        self.chunker = CodeChunker(config, llm)
        self.rag = RAGCodeRetriever(config)
        self.slider = SlidingWindowProcessor(config, llm)
        self.summarizer = HierarchicalSummarizer(config, llm)
    
    def analyze(self, source_code: str, language: str) -> dict:
        """
        Analyze source code with automatic memory strategy selection.
        """
        total_tokens = self.llm.count_tokens(source_code)
        logger.info(f"Source code size: {total_tokens} tokens")
        
        if total_tokens <= self.config.available_input_tokens:
            # Small file: direct processing
            logger.info("Using direct processing strategy")
            return {"strategy": "direct", "source": source_code}
        
        elif total_tokens <= self.config.available_input_tokens * 4:
            # Medium file: sliding window
            logger.info("Using sliding window strategy")
            chunks = self.chunker.chunk_file(source_code, language)
            return {"strategy": "sliding", "chunks": chunks}
        
        else:
            # Large file: RAG + hierarchical
            logger.info("Using RAG + hierarchical strategy")
            chunks = self.chunker.chunk_file(source_code, language)
            self.rag.index_codebase(chunks, source_code)
            self.summarizer.build_hierarchy(chunks, source_code)
            return {
                "strategy": "rag",
                "chunks": chunks,
                "retriever": self.rag,
                "summarizer": self.summarizer,
            }
