"""
LegacyLens - Unit Tests for Memory Management
=============================================
"""

import pytest
from src.memory.manager import (
    MemoryConfig,
    ChunkMetadata,
    CodeChunker,
    RAGCodeRetriever,
    SlidingWindowProcessor,
    HierarchicalSummarizer,
    MemoryManager,
)


class TestMemoryConfig:
    """Tests for MemoryConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = MemoryConfig()
        
        assert config.max_context_tokens == 8192
        assert config.reserved_output_tokens == 2048
        assert config.available_input_tokens == 6144
        assert config.chunk_size_tokens == 512
        assert config.top_k_retrieval == 5
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = MemoryConfig(
            max_context_tokens=4096,
            chunk_size_tokens=256,
        )
        
        assert config.max_context_tokens == 4096
        assert config.chunk_size_tokens == 256


class TestChunkMetadata:
    """Tests for ChunkMetadata."""
    
    def test_chunk_metadata_creation(self):
        """Test creating chunk metadata."""
        chunk = ChunkMetadata(
            chunk_id="chunk_0",
            file_path="test.cpp",
            start_line=1,
            end_line=50,
            chunk_type="class",
        )
        
        assert chunk.chunk_id == "chunk_0"
        assert chunk.start_line == 1
        assert chunk.end_line == 50
        assert chunk.chunk_type == "class"
        assert chunk.parent_scope is None
        assert chunk.token_count == 0
    
    def test_chunk_metadata_with_optional(self):
        """Test chunk metadata with optional fields."""
        chunk = ChunkMetadata(
            chunk_id="chunk_1",
            file_path="test.cpp",
            start_line=10,
            end_line=20,
            chunk_type="function",
            parent_scope="MyClass",
            token_count=150,
        )
        
        assert chunk.parent_scope == "MyClass"
        assert chunk.token_count == 150


class TestCodeChunker:
    """Tests for CodeChunker."""
    
    def test_detect_chunk_type_class(self):
        """Test detecting class chunk type."""
        # Create a mock LLM
        class MockLLM:
            def count_tokens(self, text):
                return len(text) // 4
        
        config = MemoryConfig()
        chunker = CodeChunker(config, MockLLM())
        
        assert chunker._detect_chunk_type("class Foo { }") == "class"
        assert chunker._detect_chunk_type("struct Bar { }") == "class"
    
    def test_detect_chunk_type_function(self):
        """Test detecting function chunk type."""
        class MockLLM:
            def count_tokens(self, text):
                return len(text) // 4
        
        config = MemoryConfig()
        chunker = CodeChunker(config, MockLLM())
        
        assert chunker._detect_chunk_type("void foo() { }") == "function"
    
    def test_detect_chunk_type_import(self):
        """Test detecting import chunk type."""
        class MockLLM:
            def count_tokens(self, text):
                return len(text) // 4
        
        config = MemoryConfig()
        chunker = CodeChunker(config, MockLLM())
        
        assert chunker._detect_chunk_type("#include <iostream>") == "import"
        assert chunker._detect_chunk_type("import java.util.*;") == "import"


class TestRAGCodeRetriever:
    """Tests for RAGCodeRetriever."""
    
    def test_retriever_creation(self):
        """Test creating retriever."""
        config = MemoryConfig()
        retriever = RAGCodeRetriever(config)
        
        assert retriever.chunks == []
        assert retriever.config.top_k_retrieval == 5
    
    def test_fallback_retrieve(self):
        """Test fallback retrieval without embeddings."""
        config = MemoryConfig(top_k_retrieval=2)
        retriever = RAGCodeRetriever(config)
        
        # Add some chunks without embeddings
        retriever.chunks = [
            ChunkMetadata("c0", "test.cpp", 1, 10, "class"),
            ChunkMetadata("c1", "test.cpp", 11, 20, "function"),
            ChunkMetadata("c2", "test.cpp", 21, 30, "function"),
        ]
        
        results = retriever.retrieve("some query", top_k=2)
        assert len(results) == 2


class TestSlidingWindowProcessor:
    """Tests for SlidingWindowProcessor."""
    
    def test_create_windows_small_file(self):
        """Test that small files get a single window."""
        class MockLLM:
            def count_tokens(self, text):
                return len(text) // 4
        
        config = MemoryConfig(available_input_tokens=1000)
        processor = SlidingWindowProcessor(config, MockLLM())
        
        small_source = "int main() { return 0; }"
        windows = processor._create_windows(small_source)
        
        assert len(windows) == 1
        assert windows[0][1]["window"] == 0


class TestMemoryManager:
    """Tests for MemoryManager strategy selection."""
    
    def test_manager_creation(self):
        """Test creating memory manager."""
        class MockLLM:
            def count_tokens(self, text):
                return len(text) // 4
        
        config = MemoryConfig()
        manager = MemoryManager(config, MockLLM())
        
        assert manager.chunker is not None
        assert manager.rag is not None
        assert manager.slider is not None
    
    def test_strategy_selection_direct(self):
        """Test direct strategy for small files."""
        class MockLLM:
            def count_tokens(self, text):
                return 1000  # Small file
        
        config = MemoryConfig()
        manager = MemoryManager(config, MockLLM())
        
        result = manager.analyze("small source code", "cpp")
        assert result["strategy"] == "direct"
    
    def test_strategy_selection_sliding(self):
        """Test sliding window strategy for medium files."""
        class MockLLM:
            def count_tokens(self, text):
                return 15000  # Medium file
        
        config = MemoryConfig()
        manager = MemoryManager(config, MockLLM())
        
        result = manager.analyze("medium source code", "cpp")
        assert result["strategy"] == "sliding"
    
    def test_strategy_selection_rag(self):
        """Test RAG strategy for large files."""
        class MockLLM:
            def count_tokens(self, text):
                return 50000  # Large file
        
        config = MemoryConfig()
        manager = MemoryManager(config, MockLLM())
        
        result = manager.analyze("large source code", "cpp")
        assert result["strategy"] == "rag"
