"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Editor from "@monaco-editor/react";
import {
    Play,
    Download,
    Copy,
    Check,
    RefreshCw,
    FileCode,
    Sparkles,
    ChevronLeft,
    AlertCircle,
    CheckCircle2,
    Clock,
    Loader2,
} from "lucide-react";
import Link from "next/link";

// Sample legacy code
const SAMPLE_CPP = `#include <iostream>
#include <fstream>

class ImageProcessor {
private:
    unsigned char* pixelBuffer;
    int width, height;
    FILE* outputFile;
    
public:
    ImageProcessor(int w, int h) {
        width = w;
        height = h;
        pixelBuffer = new unsigned char[w * h * 3];
        outputFile = nullptr;
    }
    
    ~ImageProcessor() {
        if (pixelBuffer) delete[] pixelBuffer;
        if (outputFile) fclose(outputFile);
    }
    
    void applyGamma(float gamma) {
        for (int i = 0; i < width * height * 3; i++) {
            float val = pixelBuffer[i] / 255.0f;
            pixelBuffer[i] = (unsigned char)(pow(val, gamma) * 255.0f);
        }
    }
};`;

const SAMPLE_PYTHON = `from pathlib import Path
from dataclasses import dataclass
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
    
    def apply_gamma(self, gamma: float) -> None:
        """Apply gamma correction using vectorized NumPy operations."""
        normalized = self._pixel_buffer.astype(np.float32) / 255.0
        corrected = np.power(normalized, gamma)
        self._pixel_buffer = (corrected * 255.0).astype(np.uint8)


# Usage with context manager
def main():
    with ImageProcessor(1920, 1080) as processor:
        processor.apply_gamma(2.2)


if __name__ == "__main__":
    main()`;

type AgentStatus = "pending" | "running" | "completed" | "failed";

interface Agent {
    id: string;
    name: string;
    emoji: string;
    status: AgentStatus;
    message?: string;
}

export default function RefactorPage() {
    const [legacyCode, setLegacyCode] = useState(SAMPLE_CPP);
    const [modernCode, setModernCode] = useState("");
    const [language, setLanguage] = useState<"cpp" | "java">("cpp");
    const [isProcessing, setIsProcessing] = useState(false);
    const [copied, setCopied] = useState(false);
    const [agents, setAgents] = useState<Agent[]>([
        { id: "archaeologist", name: "Archaeologist", emoji: "🏛️", status: "pending" },
        { id: "architect", name: "Architect", emoji: "📐", status: "pending" },
        { id: "engineer", name: "Engineer", emoji: "⚙️", status: "pending" },
        { id: "validator", name: "Validator", emoji: "✅", status: "pending" },
        { id: "scribe", name: "Scribe", emoji: "📜", status: "pending" },
    ]);

    const resetAgents = useCallback(() => {
        setAgents((prev) =>
            prev.map((a) => ({ ...a, status: "pending" as AgentStatus, message: undefined }))
        );
    }, []);

    const simulateRefactor = useCallback(async () => {
        setIsProcessing(true);
        setModernCode("");
        resetAgents();

        const delays = [1500, 1200, 2000, 1500, 1000];
        const messages = [
            "Parsed 1 class, 3 methods, 2 memory allocations",
            "Mapped: new/delete → context manager, loop → NumPy",
            "Generated Python module with type hints",
            "All 5 tests passed (100% coverage)",
            "Created README.md and Architecture.md",
        ];

        for (let i = 0; i < agents.length; i++) {
            // Set current agent to running
            setAgents((prev) =>
                prev.map((a, idx) =>
                    idx === i ? { ...a, status: "running" as AgentStatus } : a
                )
            );

            await new Promise((resolve) => setTimeout(resolve, delays[i]));

            // Set current agent to completed
            setAgents((prev) =>
                prev.map((a, idx) =>
                    idx === i
                        ? { ...a, status: "completed" as AgentStatus, message: messages[i] }
                        : a
                )
            );
        }

        // Show the result
        setModernCode(SAMPLE_PYTHON);
        setIsProcessing(false);
    }, [agents.length, resetAgents]);

    const handleCopy = useCallback(() => {
        navigator.clipboard.writeText(modernCode);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    }, [modernCode]);

    const getStatusIcon = (status: AgentStatus) => {
        switch (status) {
            case "pending":
                return <Clock className="w-4 h-4 text-muted-foreground" />;
            case "running":
                return <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />;
            case "completed":
                return <CheckCircle2 className="w-4 h-4 text-green-400" />;
            case "failed":
                return <AlertCircle className="w-4 h-4 text-red-400" />;
        }
    };

    return (
        <main className="min-h-screen bg-grid-pattern">
            {/* Header */}
            <header className="glass-strong border-b border-border sticky top-0 z-50">
                <div className="max-w-[1800px] mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link
                            href="/"
                            className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
                        >
                            <ChevronLeft className="w-4 h-4" />
                            Back
                        </Link>
                        <div className="w-px h-6 bg-border" />
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                                <Sparkles className="w-5 h-5 text-white" />
                            </div>
                            <span className="text-xl font-bold gradient-text">LegacyLens</span>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        {/* Language Selector */}
                        <div className="flex items-center gap-1 p-1 glass rounded-lg">
                            <button
                                onClick={() => setLanguage("cpp")}
                                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${language === "cpp"
                                        ? "bg-indigo-500/20 text-indigo-400"
                                        : "text-muted-foreground hover:text-foreground"
                                    }`}
                            >
                                C++
                            </button>
                            <button
                                onClick={() => setLanguage("java")}
                                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${language === "java"
                                        ? "bg-indigo-500/20 text-indigo-400"
                                        : "text-muted-foreground hover:text-foreground"
                                    }`}
                            >
                                Java
                            </button>
                        </div>

                        {/* Refactor Button */}
                        <button
                            onClick={simulateRefactor}
                            disabled={isProcessing || !legacyCode.trim()}
                            className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isProcessing ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Processing...
                                </>
                            ) : (
                                <>
                                    <Play className="w-4 h-4" />
                                    Refactor Code
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <div className="max-w-[1800px] mx-auto p-6">
                <div className="grid lg:grid-cols-2 gap-6">
                    {/* Legacy Code Editor */}
                    <div className="glass rounded-xl overflow-hidden">
                        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
                            <div className="flex items-center gap-2">
                                <FileCode className="w-4 h-4 text-orange-400" />
                                <span className="font-medium">Legacy Code</span>
                                <span className="text-xs text-muted-foreground px-2 py-0.5 rounded bg-secondary">
                                    {language.toUpperCase()}
                                </span>
                            </div>
                            <button
                                onClick={() => setLegacyCode(SAMPLE_CPP)}
                                className="text-xs text-muted-foreground hover:text-foreground transition-colors"
                            >
                                Load Sample
                            </button>
                        </div>
                        <Editor
                            height="500px"
                            language={language === "cpp" ? "cpp" : "java"}
                            value={legacyCode}
                            onChange={(value) => setLegacyCode(value || "")}
                            theme="vs-dark"
                            options={{
                                minimap: { enabled: false },
                                fontSize: 14,
                                padding: { top: 16 },
                                scrollBeyondLastLine: false,
                                wordWrap: "on",
                            }}
                        />
                    </div>

                    {/* Modern Code Output */}
                    <div className="glass rounded-xl overflow-hidden">
                        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
                            <div className="flex items-center gap-2">
                                <FileCode className="w-4 h-4 text-green-400" />
                                <span className="font-medium">Modern Python</span>
                                {modernCode && (
                                    <span className="text-xs text-green-400 px-2 py-0.5 rounded bg-green-400/10">
                                        Generated
                                    </span>
                                )}
                            </div>
                            {modernCode && (
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={handleCopy}
                                        className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                                    >
                                        {copied ? (
                                            <>
                                                <Check className="w-3 h-3 text-green-400" />
                                                Copied!
                                            </>
                                        ) : (
                                            <>
                                                <Copy className="w-3 h-3" />
                                                Copy
                                            </>
                                        )}
                                    </button>
                                    <button className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors">
                                        <Download className="w-3 h-3" />
                                        Download
                                    </button>
                                </div>
                            )}
                        </div>
                        {modernCode ? (
                            <Editor
                                height="500px"
                                language="python"
                                value={modernCode}
                                theme="vs-dark"
                                options={{
                                    minimap: { enabled: false },
                                    fontSize: 14,
                                    padding: { top: 16 },
                                    scrollBeyondLastLine: false,
                                    wordWrap: "on",
                                    readOnly: true,
                                }}
                            />
                        ) : (
                            <div className="h-[500px] flex items-center justify-center text-muted-foreground">
                                <div className="text-center">
                                    <Sparkles className="w-12 h-12 mx-auto mb-4 opacity-20" />
                                    <p>Click &quot;Refactor Code&quot; to generate modern Python</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Pipeline Status */}
                <div className="mt-6 glass rounded-xl p-6">
                    <h3 className="text-lg font-semibold mb-4">Pipeline Status</h3>
                    <div className="flex flex-wrap items-center gap-3">
                        {agents.map((agent, index) => (
                            <div key={agent.id} className="flex items-center gap-3">
                                <motion.div
                                    initial={false}
                                    animate={{
                                        scale: agent.status === "running" ? 1.05 : 1,
                                        borderColor:
                                            agent.status === "running"
                                                ? "rgb(99, 102, 241)"
                                                : agent.status === "completed"
                                                    ? "rgb(34, 197, 94)"
                                                    : "rgb(39, 39, 42)",
                                    }}
                                    className={`flex items-center gap-3 px-4 py-3 rounded-xl border transition-colors ${agent.status === "running"
                                            ? "bg-indigo-500/10 border-indigo-500"
                                            : agent.status === "completed"
                                                ? "bg-green-500/10 border-green-500/30"
                                                : "bg-secondary border-border"
                                        }`}
                                >
                                    <span className="text-2xl">{agent.emoji}</span>
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <span className="font-medium text-sm">{agent.name}</span>
                                            {getStatusIcon(agent.status)}
                                        </div>
                                        <AnimatePresence>
                                            {agent.message && (
                                                <motion.p
                                                    initial={{ opacity: 0, height: 0 }}
                                                    animate={{ opacity: 1, height: "auto" }}
                                                    exit={{ opacity: 0, height: 0 }}
                                                    className="text-xs text-muted-foreground mt-1"
                                                >
                                                    {agent.message}
                                                </motion.p>
                                            )}
                                        </AnimatePresence>
                                    </div>
                                </motion.div>
                                {index < agents.length - 1 && (
                                    <div
                                        className={`w-8 h-0.5 ${agents[index + 1].status !== "pending"
                                                ? "bg-gradient-to-r from-green-500 to-indigo-500"
                                                : "bg-border"
                                            }`}
                                    />
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </main>
    );
}
