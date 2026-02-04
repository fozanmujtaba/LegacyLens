"""
LegacyLens - Main Entry Point
=============================
Command-line interface for the legacy code refactoring system.
"""

import asyncio
import argparse
from pathlib import Path

from src.core.graph import run_refactor
from src.core.state import RefactorPhase
from src.models.llm import load_model


def main():
    parser = argparse.ArgumentParser(
        description="LegacyLens: Modernize legacy C++/Java to Python/Next.js"
    )
    parser.add_argument(
        "source_file",
        type=str,
        help="Path to legacy source file (.cpp, .java, .c)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="models/mistral-small-3.Q4_K_M.gguf",
        help="Path to GGUF model file"
    )
    parser.add_argument(
        "--model-type",
        choices=["mistral", "llama"],
        default="mistral",
        help="Model type (mistral or llama)"
    )
    parser.add_argument(
        "--python-version",
        type=str,
        default="3.11",
        help="Target Python version"
    )
    parser.add_argument(
        "--nextjs-version",
        type=str,
        default="14",
        help="Target Next.js version"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum validation retry attempts"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Directory for generated code"
    )
    
    args = parser.parse_args()
    
    # Validate source file
    source_path = Path(args.source_file)
    if not source_path.exists():
        print(f"Error: Source file not found: {source_path}")
        return 1
    
    # Detect language
    ext = source_path.suffix.lower()
    language_map = {".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", 
                    ".java": "java", ".c": "c", ".h": "cpp"}
    language = language_map.get(ext)
    if not language:
        print(f"Error: Unsupported file type: {ext}")
        return 1
    
    print(f"🔍 LegacyLens - Legacy Code Modernization")
    print(f"=" * 50)
    print(f"Source: {source_path}")
    print(f"Language: {language}")
    print(f"Target: Python {args.python_version} + Next.js {args.nextjs_version}")
    print()
    
    # Read source
    source_code = source_path.read_text()
    
    # Run refactoring workflow
    result = asyncio.run(run_refactor(
        legacy_source=source_code,
        source_file_path=str(source_path),
        source_language=language,
        target_python_version=args.python_version,
        target_nextjs_version=args.nextjs_version,
        max_retries=args.max_retries,
    ))
    
    # Output results
    if result["current_phase"] == RefactorPhase.COMPLETED:
        print("✅ Refactoring completed successfully!")
        _save_output(result, args.output_dir)
    else:
        print(f"❌ Refactoring failed: {result.get('error', 'Unknown error')}")
        return 1
    
    return 0


def _save_output(result: dict, output_dir: str):
    """Save generated code to output directory."""
    outpath = Path(output_dir)
    outpath.mkdir(parents=True, exist_ok=True)
    
    # Save Python modules
    if result.get("generated_code"):
        py_dir = outpath / "python"
        py_dir.mkdir(exist_ok=True)
        
        for name, code in result["generated_code"].get("python_modules", {}).items():
            (py_dir / name).write_text(code)
            print(f"  📄 {py_dir / name}")
        
        # Save tests
        test_dir = outpath / "tests"
        test_dir.mkdir(exist_ok=True)
        
        for name, code in result["generated_code"].get("python_tests", {}).items():
            (test_dir / name).write_text(code)
            print(f"  🧪 {test_dir / name}")
    
    # Save documentation
    if result.get("documentation"):
        docs_dir = outpath / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        if result["documentation"].get("readme"):
            (outpath / "README.md").write_text(result["documentation"]["readme"])
            print(f"  📖 {outpath / 'README.md'}")
        
        if result["documentation"].get("architecture_doc"):
            (docs_dir / "Architecture.md").write_text(
                result["documentation"]["architecture_doc"]
            )
        
        if result["documentation"].get("migration_guide"):
            (docs_dir / "Migration.md").write_text(
                result["documentation"]["migration_guide"]
            )


if __name__ == "__main__":
    exit(main())
