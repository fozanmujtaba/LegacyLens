"""
LegacyLens - FastAPI Backend Server
===================================
Provides REST and WebSocket endpoints for the frontend.
"""

import asyncio
import json
import uuid
import os
from datetime import datetime
from typing import Optional, Literal
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.core.state import create_initial_state, RefactorPhase
from src.core.graph import compile_graph
from src.models.llm import initialize_model, get_model, LegacyLensLLM


# =============================================================================
# CONFIGURATION
# =============================================================================

MODEL_PATH = Path("models/qwen2.5-coder-7b-instruct-q4_k_m.gguf")
MODEL_TYPE = "qwen"

class RefactorRequest(BaseModel):
    """Request to start a refactoring job."""
    source_code: str = Field(..., min_length=1)
    language: Literal["cpp", "java", "c"] = "cpp"
    file_name: str = "input.cpp"
    target_python_version: str = "3.11"
    target_nextjs_version: str = "14"
    max_retries: int = 3
    use_mock: bool = True  # Use mock responses until real model is loaded


class RefactorResponse(BaseModel):
    """Response with job ID."""
    job_id: str
    status: str
    message: str


class JobStatus(BaseModel):
    """Current status of a refactoring job."""
    job_id: str
    status: str
    current_phase: str
    progress: int  # 0-100
    agents: list[dict]
    generated_code: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# JOB STORAGE (In-memory for demo)
# =============================================================================

jobs: dict[str, dict] = {}


# =============================================================================
# MOCK PROCESSING (Until real LLM is loaded)
# =============================================================================

MOCK_PYTHON_OUTPUT = '''from pathlib import Path
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
        self._pixel_buffer = np.zeros(
            (self.height, self.width, 3), dtype=np.uint8
        )
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._pixel_buffer = None
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
    """Main entry point with context manager usage."""
    with ImageProcessor(1920, 1080) as processor:
        if processor.load_from_file(Path("input.raw")):
            processor.apply_gamma_correction(2.2)
            processor.apply_brightness(10)
            processor.save_to_file(Path("output.raw"))


if __name__ == "__main__":
    main()
'''


async def run_mock_pipeline(job_id: str, source_code: str, websocket: Optional[WebSocket] = None):
    """Run a mock pipeline for demo purposes."""
    agents = [
        {"id": "archaeologist", "name": "Archaeologist", "emoji": "🏛️", "status": "pending", "message": None},
        {"id": "architect", "name": "Architect", "emoji": "📐", "status": "pending", "message": None},
        {"id": "engineer", "name": "Engineer", "emoji": "⚙️", "status": "pending", "message": None},
        {"id": "validator", "name": "Validator", "emoji": "✅", "status": "pending", "message": None},
        {"id": "scribe", "name": "Scribe", "emoji": "📜", "status": "pending", "message": None},
    ]
    
    delays = [1.5, 1.2, 2.0, 1.5, 1.0]
    messages = [
        f"Parsed {source_code.count('class')} class(es), {source_code.count('void') + source_code.count('int ')} method(s)",
        "Mapped: new/delete → context manager, loops → NumPy vectorization",
        "Generated Python module with type hints and docstrings",
        "All tests passed (100% coverage) ✓",
        "Created README.md and architecture documentation",
    ]
    
    jobs[job_id]["status"] = "running"
    jobs[job_id]["agents"] = agents
    
    for i, agent in enumerate(agents):
        # Set to running
        agents[i]["status"] = "running"
        jobs[job_id]["current_phase"] = agent["id"]
        jobs[job_id]["progress"] = int((i / len(agents)) * 100)
        
        if websocket:
            await websocket.send_json({
                "type": "agent_update",
                "job_id": job_id,
                "agent_id": agent["id"],
                "status": "running",
                "progress": jobs[job_id]["progress"],
            })
        
        # Simulate processing
        await asyncio.sleep(delays[i])
        
        # Set to completed
        agents[i]["status"] = "completed"
        agents[i]["message"] = messages[i]
        
        if websocket:
            await websocket.send_json({
                "type": "agent_update",
                "job_id": job_id,
                "agent_id": agent["id"],
                "status": "completed",
                "message": messages[i],
                "progress": int(((i + 1) / len(agents)) * 100),
            })
    
    # Complete the job
    jobs[job_id]["status"] = "completed"
    jobs[job_id]["progress"] = 100
    jobs[job_id]["current_phase"] = "completed"
    jobs[job_id]["generated_code"] = MOCK_PYTHON_OUTPUT
    jobs[job_id]["completed_at"] = datetime.now().isoformat()
    
    if websocket:
        await websocket.send_json({
            "type": "job_complete",
            "job_id": job_id,
            "generated_code": MOCK_PYTHON_OUTPUT,
        })


async def run_real_pipeline(job_id: str, source_code: str, language: str, websocket: Optional[WebSocket] = None):
    """Run the actual LLM-based pipeline."""
    agents = [
        {"id": "archaeologist", "name": "Archaeologist", "emoji": "🏛️", "status": "pending", "message": None},
        {"id": "architect", "name": "Architect", "emoji": "📐", "status": "pending", "message": None},
        {"id": "engineer", "name": "Engineer", "emoji": "⚙️", "status": "pending", "message": None},
        {"id": "validator", "name": "Validator", "emoji": "✅", "status": "pending", "message": None},
        {"id": "scribe", "name": "Scribe", "emoji": "📜", "status": "pending", "message": None},
    ]
    
    jobs[job_id]["status"] = "running"
    jobs[job_id]["agents"] = agents
    
    try:
        model = get_model()
        if model is None:
            raise Exception("Model not loaded. Please ensure the model file exists.")
        
        # Agent 1: Archaeologist - Analyze the code
        await update_agent(job_id, 0, agents, "running", websocket)
        
        analysis_prompt = f"""Analyze this {language.upper()} code and identify:
1. Classes and their purposes
2. Functions/methods and what they do
3. Memory management patterns (new/delete, malloc/free)
4. Resource handling (file handles, connections)
5. Loop patterns that could be vectorized

Code:
```{language}
{source_code}
```

Provide a brief JSON summary."""

        analysis = model.generate(analysis_prompt, system_prompt="You are an expert legacy code analyst.")
        class_count = source_code.count('class')
        method_count = source_code.count('void') + source_code.count('int ') + source_code.count('public ')
        await update_agent(job_id, 0, agents, "completed", websocket, 
                          f"Analyzed {class_count} class(es), {method_count} method(s)")
        
        # Agent 2: Architect - Design the modern structure
        await update_agent(job_id, 1, agents, "running", websocket)
        
        design_prompt = f"""Based on this legacy code analysis, design a modern Python equivalent:

Analysis: {analysis[:500]}

Map these patterns:
- Manual memory (new/delete) → Python context managers (__enter__/__exit__)  
- Raw pointers → Optional types or None
- For loops on arrays → NumPy vectorized operations
- C-style error codes → Python exceptions
- Callbacks → async/await

Describe the modern Python module structure briefly."""

        design = model.generate(design_prompt, system_prompt="You are a Python architect specializing in modernization.")
        await update_agent(job_id, 1, agents, "completed", websocket,
                          "Mapped legacy patterns → modern Python idioms")
        
        # Agent 3: Engineer - Generate the code
        await update_agent(job_id, 2, agents, "running", websocket)
        
        generate_prompt = f"""Convert this {language.upper()} code to modern Python 3.11+:

```{language}
{source_code}
```

Requirements:
1. Use @dataclass for classes
2. Use type hints throughout
3. Implement __enter__/__exit__ for resource management
4. Use NumPy for array operations where applicable
5. Add comprehensive docstrings
6. Use pathlib.Path for file paths
7. Follow PEP 8 style

Output ONLY the complete Python code, no explanations:"""

        generated_code = model.generate(
            generate_prompt, 
            system_prompt="You are an expert Python developer. Output clean, production-ready Python code.",
            max_tokens=4000
        )
        
        # Clean up the response - extract just the code
        if "```python" in generated_code:
            generated_code = generated_code.split("```python")[1].split("```")[0]
        elif "```" in generated_code:
            generated_code = generated_code.split("```")[1].split("```")[0]
        
        generated_code = generated_code.strip()
        
        await update_agent(job_id, 2, agents, "completed", websocket,
                          f"Generated {len(generated_code.splitlines())} lines of Python")
        
        # Agent 4: Validator - Check the code (simplified)
        await update_agent(job_id, 3, agents, "running", websocket)
        await asyncio.sleep(0.5)  # Brief validation simulation
        
        # Basic validation checks
        has_main = "def main" in generated_code or "if __name__" in generated_code
        has_types = "->" in generated_code or ": " in generated_code
        has_docstring = '"""' in generated_code
        
        validation_msg = f"Type hints: {'✓' if has_types else '✗'}, Docstrings: {'✓' if has_docstring else '✗'}"
        await update_agent(job_id, 3, agents, "completed", websocket, validation_msg)
        
        # Agent 5: Scribe - Document
        await update_agent(job_id, 4, agents, "running", websocket)
        await asyncio.sleep(0.3)
        await update_agent(job_id, 4, agents, "completed", websocket,
                          "Code modernization complete")
        
        # Complete the job
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["current_phase"] = "completed"
        jobs[job_id]["generated_code"] = generated_code
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        
        if websocket:
            await websocket.send_json({
                "type": "job_complete",
                "job_id": job_id,
                "generated_code": generated_code,
            })
            
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        
        if websocket:
            await websocket.send_json({
                "type": "job_error",
                "job_id": job_id,
                "error": str(e),
            })


async def update_agent(job_id: str, index: int, agents: list, status: str, 
                       websocket: Optional[WebSocket], message: str = None):
    """Helper to update agent status and notify via WebSocket."""
    agents[index]["status"] = status
    if message:
        agents[index]["message"] = message
    
    jobs[job_id]["current_phase"] = agents[index]["id"]
    jobs[job_id]["progress"] = int(((index + (1 if status == "completed" else 0)) / len(agents)) * 100)
    
    if websocket:
        await websocket.send_json({
            "type": "agent_update",
            "job_id": job_id,
            "agent_id": agents[index]["id"],
            "status": status,
            "message": message,
            "progress": jobs[job_id]["progress"],
        })


# =============================================================================
# FASTAPI APP
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print("🚀 LegacyLens API Server starting...")
    
    # Try to load the model if it exists
    if MODEL_PATH.exists():
        print(f"📦 Loading model from {MODEL_PATH}...")
        try:
            initialize_model(str(MODEL_PATH), MODEL_TYPE)
            print("✅ Model loaded successfully!")
        except Exception as e:
            print(f"⚠️  Failed to load model: {e}")
            print("   Server will run in mock mode until model is available.")
    else:
        print(f"⚠️  Model not found at {MODEL_PATH}")
        print("   Server will run in mock mode.")
        print("   Download a model to enable real inference.")
    
    yield
    print("👋 LegacyLens API Server shutting down...")


app = FastAPI(
    title="LegacyLens API",
    description="AI-powered legacy code modernization",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# REST ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    model = get_model()
    return {
        "service": "LegacyLens API",
        "status": "healthy",
        "version": "1.0.0",
        "model_loaded": model is not None,
        "model_path": str(MODEL_PATH) if MODEL_PATH.exists() else None,
    }


@app.post("/api/refactor", response_model=RefactorResponse)
async def start_refactor(request: RefactorRequest):
    """Start a new refactoring job."""
    job_id = str(uuid.uuid4())
    
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "current_phase": "queued",
        "progress": 0,
        "agents": [],
        "source_code": request.source_code,
        "language": request.language,
        "use_mock": request.use_mock,
        "created_at": datetime.now().isoformat(),
        "generated_code": None,
        "error": None,
    }
    
    return RefactorResponse(
        job_id=job_id,
        status="pending",
        message="Job queued. Connect to WebSocket for real-time updates.",
    )


@app.get("/api/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get the status of a refactoring job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        current_phase=job["current_phase"],
        progress=job["progress"],
        agents=job.get("agents", []),
        generated_code=job.get("generated_code"),
        error=job.get("error"),
    )


# =============================================================================
# WEBSOCKET ENDPOINT
# =============================================================================

@app.websocket("/api/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time job updates."""
    await websocket.accept()
    
    try:
        # Check if job exists
        if job_id not in jobs:
            await websocket.send_json({
                "type": "error",
                "message": "Job not found",
            })
            await websocket.close()
            return
        
        job = jobs[job_id]
        
        # Send initial status
        await websocket.send_json({
            "type": "job_started",
            "job_id": job_id,
            "status": "running",
        })
        
        # Run the pipeline
        if job.get("use_mock", True):
            await run_mock_pipeline(job_id, job["source_code"], websocket)
        else:
            await run_real_pipeline(
                job_id,
                job["source_code"],
                job["language"],
                websocket,
            )
        
        # Keep connection open briefly for final message
        await asyncio.sleep(0.5)
        
    except WebSocketDisconnect:
        print(f"Client disconnected from job {job_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except:
            pass


# =============================================================================
# RUN SERVER
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
