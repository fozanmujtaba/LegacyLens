"""
LegacyLens - End-to-End Demo
============================
Demonstrates the complete refactoring pipeline with a sample C++ file.

Run: python -m examples.demo
"""

import asyncio
from pathlib import Path

# Sample C++ legacy code to refactor
SAMPLE_CPP_CODE = '''
#include <iostream>
#include <fstream>
#include <vector>
#include <string>

class ImageProcessor {
private:
    unsigned char* pixelBuffer;
    int width;
    int height;
    FILE* outputFile;
    
public:
    ImageProcessor(int w, int h) {
        width = w;
        height = h;
        pixelBuffer = new unsigned char[w * h * 3];
        outputFile = nullptr;
    }
    
    ~ImageProcessor() {
        if (pixelBuffer) {
            delete[] pixelBuffer;
        }
        if (outputFile) {
            fclose(outputFile);
        }
    }
    
    bool loadFromFile(const char* filename) {
        FILE* f = fopen(filename, "rb");
        if (!f) return false;
        
        fread(pixelBuffer, 1, width * height * 3, f);
        fclose(f);
        return true;
    }
    
    void applyGammaCorrection(float gamma) {
        for (int i = 0; i < width * height * 3; i++) {
            float normalized = pixelBuffer[i] / 255.0f;
            float corrected = pow(normalized, gamma);
            pixelBuffer[i] = (unsigned char)(corrected * 255.0f);
        }
    }
    
    void applyBrightness(int offset) {
        for (int i = 0; i < width * height * 3; i++) {
            int newVal = pixelBuffer[i] + offset;
            if (newVal > 255) newVal = 255;
            if (newVal < 0) newVal = 0;
            pixelBuffer[i] = (unsigned char)newVal;
        }
    }
    
    bool saveToFile(const char* filename) {
        outputFile = fopen(filename, "wb");
        if (!outputFile) return false;
        
        fwrite(pixelBuffer, 1, width * height * 3, outputFile);
        fclose(outputFile);
        outputFile = nullptr;
        return true;
    }
};

int main() {
    ImageProcessor* processor = new ImageProcessor(1920, 1080);
    
    if (processor->loadFromFile("input.raw")) {
        processor->applyGammaCorrection(2.2f);
        processor->applyBrightness(10);
        processor->saveToFile("output.raw");
    }
    
    delete processor;
    return 0;
}
'''

def demo_state_creation():
    """Demonstrate AgentState creation."""
    from src.core.state import create_initial_state, RefactorPhase
    
    print("\n" + "="*60)
    print("📋 TASK 1: Creating AgentState")
    print("="*60)
    
    state = create_initial_state(
        legacy_source=SAMPLE_CPP_CODE,
        source_file_path="examples/image_processor.cpp",
        source_language="cpp",
        target_python_version="3.11",
        target_nextjs_version="14",
        max_retries=3,
    )
    
    print(f"✅ State created successfully!")
    print(f"   - Phase: {state['current_phase']}")
    print(f"   - Source language: {state['source_language']}")
    print(f"   - Max retries: {state['max_retries']}")
    print(f"   - Source code length: {len(state['legacy_source'])} chars")
    
    return state


def demo_routing_logic():
    """Demonstrate the conditional edge routing logic."""
    from src.core.graph import should_retry_or_proceed
    from src.core.state import ValidationStatus
    
    print("\n" + "="*60)
    print("🔀 TASK 2: Testing Routing Logic")
    print("="*60)
    
    # Test case 1: All tests pass
    state_passed = {
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
    result = should_retry_or_proceed(state_passed)
    print(f"✅ All tests pass → Route to: {result}")
    assert result == "scribe", f"Expected 'scribe', got {result}"
    
    # Test case 2: Tests fail, retries available
    state_failed_retry = {
        "validation_result": {
            "status": "failed",
            "tests_run": 10,
            "tests_passed": 5,
            "tests_failed": 5,
            "suggested_fixes": [{"fix": "Update logic"}],
        },
        "iteration_count": 1,
        "max_retries": 3,
    }
    result = should_retry_or_proceed(state_failed_retry)
    print(f"✅ Tests fail, retries left → Route to: {result}")
    assert result == "engineer", f"Expected 'engineer', got {result}"
    
    # Test case 3: Tests fail, no retries left
    state_exhausted = {
        "validation_result": {
            "status": "failed",
            "tests_run": 10,
            "tests_passed": 3,
            "tests_failed": 7,
            "suggested_fixes": [{"fix": "Update logic"}],
        },
        "iteration_count": 3,
        "max_retries": 3,
    }
    result = should_retry_or_proceed(state_exhausted)
    print(f"✅ Retries exhausted → Route to: {result}")
    
    print("\n✅ All routing tests passed!")


def demo_memory_strategy():
    """Demonstrate memory strategy selection."""
    from src.memory.manager import MemoryConfig, CodeChunker
    
    print("\n" + "="*60)
    print("🧠 TASK 3: Memory Strategy Selection")
    print("="*60)
    
    config = MemoryConfig()
    print(f"Memory Configuration:")
    print(f"   - Max context tokens: {config.max_context_tokens}")
    print(f"   - Chunk size: {config.chunk_size_tokens} tokens")
    print(f"   - Chunk overlap: {config.chunk_overlap_tokens} tokens")
    print(f"   - RAG top-k: {config.top_k_retrieval}")
    
    # Simulate strategy selection based on file size
    small_file = 2000   # tokens
    medium_file = 10000 # tokens
    large_file = 50000  # tokens
    
    def select_strategy(tokens):
        if tokens <= config.available_input_tokens:
            return "direct"
        elif tokens <= config.available_input_tokens * 4:
            return "sliding_window"
        else:
            return "rag_hierarchical"
    
    print(f"\n📊 Strategy Selection:")
    print(f"   - {small_file:,} tokens → {select_strategy(small_file)}")
    print(f"   - {medium_file:,} tokens → {select_strategy(medium_file)}")
    print(f"   - {large_file:,} tokens → {select_strategy(large_file)}")


def demo_prompt_templates():
    """Demonstrate prompt template generation."""
    from src.prompts.templates import (
        ARCHAEOLOGIST_SYSTEM,
        get_analysis_prompt,
        get_design_prompt,
    )
    
    print("\n" + "="*60)
    print("📝 TASK 4: Prompt Templates")
    print("="*60)
    
    # Generate analysis prompt
    analysis_prompt = get_analysis_prompt(
        source_code=SAMPLE_CPP_CODE[:500] + "...",
        language="cpp",
        file_path="image_processor.cpp",
    )
    
    print(f"Archaeologist System Prompt (first 200 chars):")
    print(f"   {ARCHAEOLOGIST_SYSTEM[:200]}...")
    print(f"\nAnalysis Prompt generated: {len(analysis_prompt)} chars")
    
    # Show pattern examples
    print(f"\n📋 Design Pattern Mappings Available:")
    print(f"   - Manual memory (new/delete) → Context managers")
    print(f"   - Raw pointers → Optional types")
    print(f"   - Monolithic loops → NumPy vectorization")
    print(f"   - Callbacks → async/await")


def demo_expected_output():
    """Show expected modern Python output."""
    print("\n" + "="*60)
    print("🎯 EXPECTED MODERN PYTHON OUTPUT")
    print("="*60)
    
    expected_python = '''
from pathlib import Path
from dataclasses import dataclass
from contextlib import contextmanager
import numpy as np
from numpy.typing import NDArray

@dataclass
class ImageProcessor:
    """Modern Python image processor with automatic resource management."""
    width: int
    height: int
    _pixel_buffer: NDArray[np.uint8] | None = None
    
    def __post_init__(self):
        self._pixel_buffer = np.zeros((self.height, self.width, 3), dtype=np.uint8)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._pixel_buffer = None  # Release memory
        return False
    
    def load_from_file(self, filename: Path) -> bool:
        """Load raw image data from file."""
        try:
            data = np.fromfile(filename, dtype=np.uint8)
            self._pixel_buffer = data.reshape((self.height, self.width, 3))
            return True
        except Exception:
            return False
    
    def apply_gamma_correction(self, gamma: float) -> None:
        """Apply gamma correction using vectorized NumPy operations."""
        normalized = self._pixel_buffer.astype(np.float32) / 255.0
        corrected = np.power(normalized, gamma)
        self._pixel_buffer = (corrected * 255.0).astype(np.uint8)
    
    def apply_brightness(self, offset: int) -> None:
        """Apply brightness adjustment with clipping."""
        self._pixel_buffer = np.clip(
            self._pixel_buffer.astype(np.int16) + offset, 0, 255
        ).astype(np.uint8)
    
    def save_to_file(self, filename: Path) -> bool:
        """Save processed image to file."""
        try:
            self._pixel_buffer.tofile(filename)
            return True
        except Exception:
            return False


def main():
    with ImageProcessor(1920, 1080) as processor:
        if processor.load_from_file(Path("input.raw")):
            processor.apply_gamma_correction(2.2)
            processor.apply_brightness(10)
            processor.save_to_file(Path("output.raw"))


if __name__ == "__main__":
    main()
'''
    
    print(expected_python)


def main():
    """Run the complete demo."""
    print("\n" + "🔍 "*20)
    print("         LEGACYLENS - END-TO-END DEMO")
    print("🔍 "*20)
    
    print("\n📄 Sample C++ Input (ImageProcessor class):")
    print("-" * 40)
    print(SAMPLE_CPP_CODE[:600] + "\n... (truncated)")
    
    # Run all demos
    demo_state_creation()
    demo_routing_logic()
    demo_memory_strategy()
    demo_prompt_templates()
    demo_expected_output()
    
    print("\n" + "="*60)
    print("✅ DEMO COMPLETE!")
    print("="*60)
    print("\nThe full pipeline would:")
    print("  1. Archaeologist → Parse C++ and extract Logic Schema")
    print("  2. Architect → Map patterns (new/delete → context manager)")
    print("  3. Engineer → Generate Python with NumPy vectorization")
    print("  4. Validator → Run pytest, retry if needed")
    print("  5. Scribe → Generate docs with Mermaid diagrams")
    print("\n🚀 To run with a real LLM, download a GGUF model and use:")
    print("   python main.py examples/image_processor.cpp --model <path-to-model.gguf>")


if __name__ == "__main__":
    main()
