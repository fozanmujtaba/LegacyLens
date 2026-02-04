"""
Example: Refactoring a C++ file processor to Python.
"""

# Example legacy C++ code
LEGACY_CPP = '''
#include <fstream>
#include <string>
#include <vector>

class DataProcessor {
private:
    std::ifstream* inputFile;
    std::ofstream* outputFile;
    std::vector<double> buffer;
    
public:
    DataProcessor(const char* inPath, const char* outPath) {
        inputFile = new std::ifstream(inPath);
        outputFile = new std::ofstream(outPath);
        if (!inputFile->is_open() || !outputFile->is_open()) {
            throw std::runtime_error("Failed to open files");
        }
    }
    
    ~DataProcessor() {
        if (inputFile) {
            inputFile->close();
            delete inputFile;
        }
        if (outputFile) {
            outputFile->close();
            delete outputFile;
        }
    }
    
    void processData() {
        double value;
        while (*inputFile >> value) {
            buffer.push_back(value * 2.0);
        }
        
        for (int i = 0; i < buffer.size(); i++) {
            *outputFile << buffer[i] << "\\n";
        }
    }
};

int main() {
    DataProcessor* processor = new DataProcessor("input.txt", "output.txt");
    processor->processData();
    delete processor;
    return 0;
}
'''

# Expected modern Python output
EXPECTED_PYTHON = '''
from pathlib import Path
from dataclasses import dataclass
from contextlib import contextmanager
from typing import Iterator
import numpy as np

@dataclass
class DataProcessor:
    """Process data files with automatic resource management."""
    input_path: Path
    output_path: Path
    
    def __enter__(self):
        self._input_file = open(self.input_path, 'r')
        self._output_file = open(self.output_path, 'w')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._input_file.close()
        self._output_file.close()
        return False
    
    def process_data(self) -> None:
        """Read, transform, and write data using vectorized operations."""
        # Read all values at once
        values = np.array([float(line) for line in self._input_file])
        
        # Vectorized transformation
        processed = values * 2.0
        
        # Write results
        for value in processed:
            self._output_file.write(f"{value}\\n")


def main():
    with DataProcessor(Path("input.txt"), Path("output.txt")) as processor:
        processor.process_data()


if __name__ == "__main__":
    main()
'''

if __name__ == "__main__":
    print("Legacy C++ Code:")
    print("=" * 50)
    print(LEGACY_CPP)
    print()
    print("Expected Modern Python:")
    print("=" * 50)
    print(EXPECTED_PYTHON)
