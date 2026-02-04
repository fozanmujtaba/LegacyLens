"""
LegacyLens - Few-Shot Prompt Templates
======================================
Design Pattern Mapping prompts for C++/Java to Python translation.

Author: LegacyLens AI Architect
"""

from __future__ import annotations
from typing import Optional
from string import Template


# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

ARCHAEOLOGIST_SYSTEM = """You are The Archaeologist, an expert in legacy C++ and Java code analysis.
Your role is to parse legacy code and extract a structured Logic Schema.

You MUST output valid JSON with the following structure:
- classes: Array of class definitions with methods, members, inheritance
- functions: Array of standalone functions with signatures and logic
- memory_allocations: All new/malloc/delete/free operations
- pointer_operations: Pointer arithmetic and dereferencing
- control_flow_graph: Loops, conditionals, branches
- call_graph: Function call relationships

Be meticulous about identifying:
1. Manual memory management patterns (RAII violations, raw pointers)
2. Thread synchronization primitives (mutexes, locks)
3. Resource handles (file descriptors, sockets, database connections)
4. Legacy patterns (singletons, factories, observers)"""


ARCHITECT_SYSTEM = """You are The Architect, an expert in modern Python design patterns.
Your role is to map legacy C++/Java patterns to Pythonic equivalents.

Design Pattern Mapping Rules:
─────────────────────────────
| Legacy Pattern          | Modern Python Equivalent              |
|-------------------------|---------------------------------------|
| Manual memory (new/del) | Context managers, dataclasses         |
| Raw pointers            | Optional types, references            |
| Mutex/locks             | asyncio.Lock, threading.Lock          |
| Monolithic loops        | NumPy vectorization, list comps       |
| Callbacks               | async/await, Futures                  |
| Singleton               | Module-level instance, dependency inj |
| Factory pattern         | @classmethod, __init__ variants       |
| Observer pattern        | Signals, pub/sub, RxPY                |
| Template classes        | Generic[T], TypeVar                   |
| Virtual methods         | ABC, @abstractmethod                  |

Output a detailed design mapping with rationale for each decision."""


ENGINEER_SYSTEM = """You are The Engineer, an expert Python and Next.js developer.
Your role is to generate production-quality code from design specifications.

Requirements:
- Python 3.11+ with full type hints
- Async/await for I/O operations
- Pydantic for data validation
- pytest for testing
- Next.js 14 with App Router for frontend
- TypeScript with strict mode
- Tailwind CSS for styling

Generate complete, working code with proper error handling."""


VALIDATOR_SYSTEM = """You are The Validator, an expert in software quality assurance.
Your role is to analyze test results and suggest fixes for failures.

For each failure, provide:
1. Root cause analysis
2. Specific fix recommendation
3. Code snippet for the fix
4. Confidence level (high/medium/low)

Focus on:
- Logic errors from translation
- Missing edge cases
- Type mismatches
- Resource leaks"""


SCRIBE_SYSTEM = """You are The Scribe, an expert technical writer.
Your role is to generate comprehensive documentation.

Output format:
- README.md with project overview
- Architecture.md with Mermaid diagrams
- API reference with docstrings
- Migration guide from legacy to modern

Use Mermaid.js syntax for all diagrams:
- flowchart for control flow
- sequenceDiagram for interactions
- classDiagram for structure"""


# =============================================================================
# FEW-SHOT EXAMPLES
# =============================================================================

CPP_TO_PYTHON_EXAMPLES = """
### Example 1: Manual Memory Management → Context Manager

**C++ (Legacy):**
```cpp
class FileProcessor {
private:
    FILE* file;
public:
    FileProcessor(const char* path) {
        file = fopen(path, "r");
        if (!file) throw std::runtime_error("Cannot open file");
    }
    ~FileProcessor() {
        if (file) fclose(file);
    }
    std::string read() {
        char buffer[1024];
        fread(buffer, 1, 1024, file);
        return std::string(buffer);
    }
};

// Usage
FileProcessor* fp = new FileProcessor("data.txt");
std::string content = fp->read();
delete fp;
```

**Python (Modern):**
```python
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass

@dataclass
class FileProcessor:
    path: Path
    _file: object = None
    
    def __enter__(self):
        self._file = open(self.path, 'r')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._file:
            self._file.close()
        return False
    
    def read(self) -> str:
        return self._file.read()

# Usage
with FileProcessor(Path("data.txt")) as fp:
    content = fp.read()
```

---

### Example 2: Monolithic Loop → NumPy Vectorization

**C++ (Legacy):**
```cpp
void processImages(float* pixels, int size, float gamma) {
    for (int i = 0; i < size; i++) {
        pixels[i] = pow(pixels[i] / 255.0f, gamma) * 255.0f;
    }
}
```

**Python (Modern):**
```python
import numpy as np
from numpy.typing import NDArray

def process_images(pixels: NDArray[np.float32], gamma: float) -> NDArray[np.float32]:
    \"\"\"Apply gamma correction using vectorized operations.\"\"\"
    normalized = pixels / 255.0
    corrected = np.power(normalized, gamma)
    return (corrected * 255.0).astype(np.float32)
```

---

### Example 3: Callback Pattern → Async/Await

**Java (Legacy):**
```java
public interface DataCallback {
    void onSuccess(String data);
    void onError(Exception e);
}

public void fetchData(String url, DataCallback callback) {
    new Thread(() -> {
        try {
            String result = httpClient.get(url);
            callback.onSuccess(result);
        } catch (Exception e) {
            callback.onError(e);
        }
    }).start();
}
```

**Python (Modern):**
```python
import asyncio
import aiohttp
from typing import Optional

async def fetch_data(url: str) -> str:
    \"\"\"Fetch data asynchronously using modern async/await.\"\"\"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.text()

# Usage
data = await fetch_data("https://api.example.com/data")
```
"""


JAVA_TO_PYTHON_EXAMPLES = """
### Example 1: Singleton Pattern → Module Instance

**Java (Legacy):**
```java
public class DatabaseConnection {
    private static DatabaseConnection instance;
    private Connection conn;
    
    private DatabaseConnection() {
        conn = DriverManager.getConnection(URL);
    }
    
    public static synchronized DatabaseConnection getInstance() {
        if (instance == null) {
            instance = new DatabaseConnection();
        }
        return instance;
    }
}
```

**Python (Modern):**
```python
from functools import lru_cache
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@lru_cache(maxsize=1)
def get_database_connection():
    \"\"\"Get singleton database connection using lru_cache.\"\"\"
    engine = create_engine(DATABASE_URL)
    return sessionmaker(bind=engine)()

# Or using dependency injection
from dataclasses import dataclass

@dataclass
class DatabaseService:
    connection_url: str
    _engine: object = None
    
    def connect(self):
        self._engine = create_engine(self.connection_url)
        return sessionmaker(bind=self._engine)()
```

---

### Example 2: Builder Pattern → Dataclass with Defaults

**Java (Legacy):**
```java
public class User {
    private final String name;
    private final String email;
    private final int age;
    
    private User(Builder builder) {
        this.name = builder.name;
        this.email = builder.email;
        this.age = builder.age;
    }
    
    public static class Builder {
        private String name;
        private String email;
        private int age = 0;
        
        public Builder name(String name) { this.name = name; return this; }
        public Builder email(String email) { this.email = email; return this; }
        public Builder age(int age) { this.age = age; return this; }
        public User build() { return new User(this); }
    }
}
```

**Python (Modern):**
```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class User:
    name: str
    email: str
    age: int = 0
    
    @classmethod
    def create(cls, name: str, email: str, age: int = 0) -> "User":
        \"\"\"Factory method for creating users with validation.\"\"\"
        if not name or not email:
            raise ValueError("Name and email are required")
        return cls(name=name, email=email, age=age)

# Usage
user = User(name="John", email="john@example.com", age=30)
```
"""


# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

ANALYSIS_PROMPT = Template("""
Analyze the following $language code and extract the Logic Schema.

## Source Code:
```$language
$source_code
```

## Instructions:
1. Identify all classes, functions, and global variables
2. Map memory allocation patterns (new, malloc, delete, free)
3. Trace control flow (loops, conditionals, exceptions)
4. Build call graph (which functions call which)
5. List external dependencies

Output a JSON Logic Schema following this structure:
```json
{
    "source_file": "$file_path",
    "language": "$language",
    "classes": [...],
    "functions": [...],
    "memory_allocations": [...],
    "control_flow_graph": {...},
    "call_graph": {...}
}
```
""")


DESIGN_PROMPT = Template("""
Map the following Logic Schema to modern Python design patterns.

## Logic Schema:
```json
$logic_schema
```

## Design Pattern Reference:
$pattern_examples

## Instructions:
1. For each legacy pattern, select the best modern equivalent
2. Identify async/await opportunities
3. Find vectorization candidates for loops
4. Design context managers for resource handling
5. Plan the Next.js component structure

Output a Design Mapping with rationale.
""")


GENERATION_PROMPT = Template("""
Generate production Python code from this Design Mapping.

## Design Mapping:
```json
$design_mapping
```

## Original Algorithm Flow:
$flow_description

## Previous Failures (if any):
$previous_failures

## Requirements:
- Python $python_version with full type hints
- Use async/await where indicated
- Include comprehensive docstrings
- Generate pytest test cases
- Create Next.js $nextjs_version components

Generate complete, working code.
""")


def get_analysis_prompt(source_code: str, language: str, file_path: str) -> str:
    """Build the analysis prompt for the Archaeologist."""
    return ANALYSIS_PROMPT.substitute(
        language=language,
        source_code=source_code,
        file_path=file_path,
    )


def get_design_prompt(logic_schema: dict, language: str) -> str:
    """Build the design prompt for the Architect."""
    import json
    examples = CPP_TO_PYTHON_EXAMPLES if language == "cpp" else JAVA_TO_PYTHON_EXAMPLES
    return DESIGN_PROMPT.substitute(
        logic_schema=json.dumps(logic_schema, indent=2),
        pattern_examples=examples,
    )


def get_generation_prompt(
    design_mapping: dict,
    flow_description: str,
    previous_failures: list,
    python_version: str = "3.11",
    nextjs_version: str = "14",
) -> str:
    """Build the generation prompt for the Engineer."""
    import json
    failures_str = json.dumps(previous_failures, indent=2) if previous_failures else "None"
    return GENERATION_PROMPT.substitute(
        design_mapping=json.dumps(design_mapping, indent=2),
        flow_description=flow_description,
        previous_failures=failures_str,
        python_version=python_version,
        nextjs_version=nextjs_version,
    )
