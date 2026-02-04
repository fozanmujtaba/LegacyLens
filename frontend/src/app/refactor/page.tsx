"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Editor from "@monaco-editor/react";
import JSZip from "jszip";
import {
    Play,
    Download,
    Copy,
    Check,
    FileCode,
    Sparkles,
    ChevronLeft,
    AlertCircle,
    CheckCircle2,
    Clock,
    Loader2,
    Wifi,
    WifiOff,
    Upload,
    Package,
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

const API_BASE = "http://localhost:8000";

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
    const [connected, setConnected] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [modelLoaded, setModelLoaded] = useState(false);
    const [useMock, setUseMock] = useState(true);
    const [fileName, setFileName] = useState<string | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [agents, setAgents] = useState<Agent[]>([
        { id: "archaeologist", name: "Archaeologist", emoji: "🏛️", status: "pending" },
        { id: "architect", name: "Architect", emoji: "📐", status: "pending" },
        { id: "engineer", name: "Engineer", emoji: "⚙️", status: "pending" },
        { id: "validator", name: "Validator", emoji: "✅", status: "pending" },
        { id: "scribe", name: "Scribe", emoji: "📜", status: "pending" },
    ]);

    // Check if model is loaded on mount
    useEffect(() => {
        const checkModelStatus = async () => {
            try {
                const response = await fetch(`${API_BASE}/`);
                if (response.ok) {
                    const data = await response.json();
                    setModelLoaded(data.model_loaded || false);
                    // Auto-enable real mode if model is loaded
                    if (data.model_loaded) {
                        setUseMock(false);
                    }
                }
            } catch {
                // Backend not running, ignore
            }
        };
        checkModelStatus();
        // Check every 30 seconds
        const interval = setInterval(checkModelStatus, 30000);
        return () => clearInterval(interval);
    }, []);

    const resetAgents = useCallback(() => {
        setAgents((prev) =>
            prev.map((a) => ({ ...a, status: "pending" as AgentStatus, message: undefined }))
        );
        setError(null);
        setModernCode("");
    }, []);

    const handleRefactor = useCallback(async () => {
        setIsProcessing(true);
        resetAgents();

        try {
            // Step 1: Create the job
            const response = await fetch(`${API_BASE}/api/refactor`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    source_code: legacyCode,
                    language: language,
                    file_name: `input.${language}`,
                    use_mock: useMock,
                }),
            });

            if (!response.ok) {
                throw new Error("Failed to create refactoring job");
            }

            const { job_id } = await response.json();

            // Step 2: Connect to WebSocket for real-time updates
            const ws = new WebSocket(`ws://localhost:8000/api/ws/${job_id}`);
            wsRef.current = ws;

            ws.onopen = () => {
                setConnected(true);
                console.log("WebSocket connected");
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log("WS message:", data);

                switch (data.type) {
                    case "agent_update":
                        setAgents((prev) =>
                            prev.map((a) =>
                                a.id === data.agent_id
                                    ? { ...a, status: data.status, message: data.message }
                                    : a
                            )
                        );
                        break;

                    case "job_complete":
                        setModernCode(data.generated_code);
                        setIsProcessing(false);
                        setConnected(false);
                        ws.close();
                        break;

                    case "job_error":
                        setError(data.error);
                        setIsProcessing(false);
                        setConnected(false);
                        ws.close();
                        break;
                }
            };

            ws.onerror = (err) => {
                console.error("WebSocket error:", err);
                setError("Connection error. Is the backend server running?");
                setIsProcessing(false);
                setConnected(false);
            };

            ws.onclose = () => {
                setConnected(false);
                console.log("WebSocket closed");
            };

        } catch (err) {
            console.error("Refactor error:", err);
            setError(err instanceof Error ? err.message : "Unknown error occurred");
            setIsProcessing(false);
        }
    }, [legacyCode, language, useMock, resetAgents]);

    // Cleanup WebSocket on unmount
    useEffect(() => {
        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, []);

    const handleCopy = useCallback(() => {
        navigator.clipboard.writeText(modernCode);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    }, [modernCode]);

    const handleDownload = useCallback(() => {
        const blob = new Blob([modernCode], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "modernized_code.py";
        a.click();
        URL.revokeObjectURL(url);
    }, [modernCode]);

    // File upload handlers
    const handleFileUpload = useCallback((file: File) => {
        const extension = file.name.split('.').pop()?.toLowerCase();

        // Detect language from extension
        if (extension === 'cpp' || extension === 'cc' || extension === 'cxx' || extension === 'c' || extension === 'h' || extension === 'hpp') {
            setLanguage('cpp');
        } else if (extension === 'java') {
            setLanguage('java');
        }

        setFileName(file.name);

        const reader = new FileReader();
        reader.onload = (e) => {
            const content = e.target?.result as string;
            setLegacyCode(content);
        };
        reader.readAsText(file);
    }, []);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        const file = e.dataTransfer.files[0];
        if (file) {
            handleFileUpload(file);
        }
    }, [handleFileUpload]);

    const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            handleFileUpload(file);
        }
    }, [handleFileUpload]);

    // Export as ZIP
    const handleExportZip = useCallback(async () => {
        const zip = new JSZip();

        // Get the base name from the original file or use default
        const baseName = fileName ? fileName.replace(/\.[^/.]+$/, '') : 'modernized_code';

        // Add the Python code
        zip.file(`${baseName}.py`, modernCode);

        // Add requirements.txt
        const requirements = `# Requirements for ${baseName}
numpy>=1.20.0
typing-extensions>=4.0.0
`;
        zip.file("requirements.txt", requirements);

        // Add README.md
        const readme = `# ${baseName}

## Overview
This code was modernized from legacy ${language.toUpperCase()} using LegacyLens.

## Installation
\`\`\`bash
pip install -r requirements.txt
\`\`\`

## Usage
\`\`\`python
from ${baseName} import *
# Use the modernized classes and functions
\`\`\`

## Original File
- **Source:** ${fileName || 'pasted code'}
- **Language:** ${language.toUpperCase()}

## Generated by
[LegacyLens](https://github.com/fozanmujtaba/LegacyLens) - AI-powered code modernization
`;
        zip.file("README.md", readme);

        // Generate and download
        const content = await zip.generateAsync({ type: "blob" });
        const url = URL.createObjectURL(content);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${baseName}_modernized.zip`;
        a.click();
        URL.revokeObjectURL(url);
    }, [modernCode, fileName, language]);

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
                        {/* Connection Status */}
                        <div className="flex items-center gap-2 px-3 py-1.5 glass rounded-lg">
                            {connected ? (
                                <>
                                    <Wifi className="w-4 h-4 text-green-400" />
                                    <span className="text-xs text-green-400">Connected</span>
                                </>
                            ) : (
                                <>
                                    <WifiOff className="w-4 h-4 text-muted-foreground" />
                                    <span className="text-xs text-muted-foreground">Disconnected</span>
                                </>
                            )}
                        </div>

                        {/* Mode Toggle */}
                        <div className="flex items-center gap-1 p-1 glass rounded-lg">
                            <button
                                onClick={() => setUseMock(true)}
                                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${useMock
                                    ? "bg-yellow-500/20 text-yellow-400"
                                    : "text-muted-foreground hover:text-foreground"
                                    }`}
                            >
                                Mock
                            </button>
                            <button
                                onClick={() => setUseMock(false)}
                                disabled={!modelLoaded}
                                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${!useMock
                                    ? "bg-green-500/20 text-green-400"
                                    : modelLoaded
                                        ? "text-muted-foreground hover:text-foreground"
                                        : "text-muted-foreground/50 cursor-not-allowed"
                                    }`}
                                title={modelLoaded ? "Use real LLM" : "Model not loaded"}
                            >
                                Real LLM {modelLoaded && "✓"}
                            </button>
                        </div>

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
                            onClick={handleRefactor}
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

            {/* Error Banner */}
            <AnimatePresence>
                {error && (
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="max-w-[1800px] mx-auto px-6 pt-4"
                    >
                        <div className="flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400">
                            <AlertCircle className="w-5 h-5 flex-shrink-0" />
                            <p className="text-sm">{error}</p>
                            <button
                                onClick={() => setError(null)}
                                className="ml-auto text-xs hover:underline"
                            >
                                Dismiss
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Main Content */}
            <div className="max-w-[1800px] mx-auto p-6">
                <div className="grid lg:grid-cols-2 gap-6">
                    {/* Legacy Code Editor */}
                    <div
                        className={`relative glass rounded-xl overflow-hidden transition-all ${isDragging ? 'ring-2 ring-indigo-500 ring-offset-2 ring-offset-background' : ''
                            }`}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                    >
                        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
                            <div className="flex items-center gap-2">
                                <FileCode className="w-4 h-4 text-orange-400" />
                                <span className="font-medium">Legacy Code</span>
                                <span className="text-xs text-muted-foreground px-2 py-0.5 rounded bg-secondary">
                                    {language.toUpperCase()}
                                </span>
                                {fileName && (
                                    <span className="text-xs text-indigo-400 px-2 py-0.5 rounded bg-indigo-400/10">
                                        {fileName}
                                    </span>
                                )}
                            </div>
                            <div className="flex items-center gap-2">
                                <input
                                    type="file"
                                    ref={fileInputRef}
                                    onChange={handleFileInputChange}
                                    accept=".cpp,.cc,.cxx,.c,.h,.hpp,.java"
                                    className="hidden"
                                />
                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                                >
                                    <Upload className="w-3 h-3" />
                                    Upload
                                </button>
                                <button
                                    onClick={() => {
                                        setLegacyCode(SAMPLE_CPP);
                                        setFileName(null);
                                    }}
                                    className="text-xs text-muted-foreground hover:text-foreground transition-colors"
                                >
                                    Load Sample
                                </button>
                            </div>
                        </div>

                        {/* Drag overlay */}
                        {isDragging && (
                            <div className="absolute inset-0 bg-indigo-500/10 z-10 flex items-center justify-center pointer-events-none">
                                <div className="text-center">
                                    <Upload className="w-12 h-12 mx-auto mb-2 text-indigo-400" />
                                    <p className="text-indigo-400 font-medium">Drop your file here</p>
                                </div>
                            </div>
                        )}

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
                                    <button
                                        onClick={handleDownload}
                                        className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                                    >
                                        <Download className="w-3 h-3" />
                                        .py
                                    </button>
                                    <button
                                        onClick={handleExportZip}
                                        className="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                                    >
                                        <Package className="w-3 h-3" />
                                        Export ZIP
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
                                    <p className="text-xs mt-2 opacity-50">Make sure the backend server is running</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Pipeline Status */}
                <div className="mt-6 glass rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold">Pipeline Status</h3>
                        {isProcessing && (
                            <div className="flex items-center gap-2 text-sm text-indigo-400">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Processing...
                            </div>
                        )}
                    </div>
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
                                        ? "bg-indigo-500/10 border-indigo-500 animate-pulse"
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
                                                    className="text-xs text-muted-foreground mt-1 max-w-[200px]"
                                                >
                                                    {agent.message}
                                                </motion.p>
                                            )}
                                        </AnimatePresence>
                                    </div>
                                </motion.div>
                                {index < agents.length - 1 && (
                                    <div
                                        className={`w-8 h-0.5 transition-colors ${agents[index + 1].status !== "pending"
                                            ? "bg-gradient-to-r from-green-500 to-indigo-500"
                                            : "bg-border"
                                            }`}
                                    />
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Instructions */}
                <div className="mt-6 glass rounded-xl p-6">
                    <h3 className="text-lg font-semibold mb-3">Getting Started</h3>
                    <div className="grid md:grid-cols-2 gap-4 text-sm text-muted-foreground">
                        <div>
                            <p className="font-medium text-foreground mb-2">1. Start the Backend</p>
                            <code className="block p-3 rounded-lg bg-secondary text-xs font-mono">
                                source .venv/bin/activate && python server.py
                            </code>
                        </div>
                        <div>
                            <p className="font-medium text-foreground mb-2">2. Paste Your Code</p>
                            <p>Enter your legacy C++ or Java code in the left editor, then click &quot;Refactor Code&quot;.</p>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}
