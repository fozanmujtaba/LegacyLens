"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
    Sparkles,
    ArrowRight,
    Zap,
    Shield,
    Code2,
    Cpu,
    GitBranch,
    FileCode,
    CheckCircle2,
} from "lucide-react";
import Link from "next/link";

export default function Home() {
    const [hoveredFeature, setHoveredFeature] = useState<number | null>(null);

    const features = [
        {
            icon: <Cpu className="w-6 h-6" />,
            title: "Local LLM Inference",
            description: "Run Mistral-Small or Llama 3.2 locally on Apple Silicon with Metal acceleration",
        },
        {
            icon: <GitBranch className="w-6 h-6" />,
            title: "5-Agent Pipeline",
            description: "Archaeologist → Architect → Engineer → Validator → Scribe workflow",
        },
        {
            icon: <Shield className="w-6 h-6" />,
            title: "Self-Healing Validation",
            description: "Automatic retry loops with intelligent fix suggestions on test failures",
        },
        {
            icon: <Code2 className="w-6 h-6" />,
            title: "Pattern Mapping",
            description: "Few-shot translation from manual memory to context managers, callbacks to async/await",
        },
    ];

    const agents = [
        { name: "Archaeologist", emoji: "🏛️", desc: "Parses legacy code" },
        { name: "Architect", emoji: "📐", desc: "Maps design patterns" },
        { name: "Engineer", emoji: "⚙️", desc: "Generates modern code" },
        { name: "Validator", emoji: "✅", desc: "Runs tests & validates" },
        { name: "Scribe", emoji: "📜", desc: "Creates documentation" },
    ];

    return (
        <main className="min-h-screen bg-grid-pattern relative overflow-hidden">
            {/* Background blobs */}
            <div className="hero-blob hero-blob-1" />
            <div className="hero-blob hero-blob-2" />

            {/* Navbar */}
            <nav className="fixed top-0 left-0 right-0 z-50 glass-strong">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                            <Sparkles className="w-5 h-5 text-white" />
                        </div>
                        <span className="text-xl font-bold gradient-text">LegacyLens</span>
                    </div>
                    <div className="flex items-center gap-6">
                        <a href="https://github.com/fozanmujtaba/LegacyLens"
                            target="_blank"
                            className="text-muted-foreground hover:text-foreground transition-colors">
                            GitHub
                        </a>
                        <Link
                            href="/refactor"
                            className="px-4 py-2 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium hover:opacity-90 transition-opacity"
                        >
                            Launch App
                        </Link>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="pt-32 pb-20 px-6 relative">
                <div className="max-w-7xl mx-auto text-center">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6 }}
                    >
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-6">
                            <Zap className="w-4 h-4 text-yellow-400" />
                            <span className="text-sm text-muted-foreground">Powered by LangGraph + Local LLMs</span>
                        </div>

                        <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
                            Transform <span className="gradient-text">Legacy Code</span>
                            <br />into Modern Masterpieces
                        </h1>

                        <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
                            AI-powered agentic workflow that converts C++/Java codebases to Python/Next.js
                            using local Mistral or Llama models on your Apple Silicon Mac.
                        </p>

                        <div className="flex items-center justify-center gap-4">
                            <Link
                                href="/refactor"
                                className="group px-8 py-4 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-semibold text-lg hover:opacity-90 transition-all glow-primary flex items-center gap-2"
                            >
                                Start Refactoring
                                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                            </Link>
                            <a
                                href="#features"
                                className="px-8 py-4 rounded-xl glass text-foreground font-semibold text-lg hover:bg-secondary transition-colors"
                            >
                                Learn More
                            </a>
                        </div>
                    </motion.div>

                    {/* Code transformation preview */}
                    <motion.div
                        initial={{ opacity: 0, y: 40 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, delay: 0.3 }}
                        className="mt-16 relative"
                    >
                        <div className="grid md:grid-cols-2 gap-4 max-w-5xl mx-auto">
                            {/* Legacy Code */}
                            <div className="glass rounded-xl p-4 text-left">
                                <div className="flex items-center gap-2 mb-3">
                                    <FileCode className="w-4 h-4 text-orange-400" />
                                    <span className="text-sm font-medium text-orange-400">Legacy C++</span>
                                </div>
                                <pre className="text-sm text-muted-foreground font-mono overflow-x-auto">
                                    {`class DataProcessor {
  unsigned char* buffer;
public:
  DataProcessor() {
    buffer = new unsigned char[1024];
  }
  ~DataProcessor() {
    delete[] buffer;
  }
};`}
                                </pre>
                            </div>

                            {/* Arrow */}
                            <div className="hidden md:flex absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-10">
                                <div className="w-12 h-12 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-center glow-primary">
                                    <ArrowRight className="w-6 h-6 text-white" />
                                </div>
                            </div>

                            {/* Modern Code */}
                            <div className="glass rounded-xl p-4 text-left">
                                <div className="flex items-center gap-2 mb-3">
                                    <FileCode className="w-4 h-4 text-green-400" />
                                    <span className="text-sm font-medium text-green-400">Modern Python</span>
                                </div>
                                <pre className="text-sm text-muted-foreground font-mono overflow-x-auto">
                                    {`@dataclass
class DataProcessor:
    _buffer: NDArray[np.uint8] = None
    
    def __enter__(self):
        self._buffer = np.zeros(1024)
        return self
    
    def __exit__(self, *args):
        self._buffer = None`}
                                </pre>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Pipeline Section */}
            <section className="py-20 px-6 relative" id="pipeline">
                <div className="max-w-7xl mx-auto">
                    <motion.div
                        initial={{ opacity: 0 }}
                        whileInView={{ opacity: 1 }}
                        viewport={{ once: true }}
                        className="text-center mb-16"
                    >
                        <h2 className="text-3xl md:text-4xl font-bold mb-4">
                            5-Agent <span className="gradient-text">Agentic Pipeline</span>
                        </h2>
                        <p className="text-muted-foreground max-w-xl mx-auto">
                            Each agent specializes in a specific phase of the modernization workflow
                        </p>
                    </motion.div>

                    <div className="flex flex-wrap justify-center gap-4">
                        {agents.map((agent, index) => (
                            <motion.div
                                key={agent.name}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: index * 0.1 }}
                                className="glass rounded-xl p-6 text-center min-w-[160px] hover:glow-primary transition-shadow"
                            >
                                <div className="text-4xl mb-3">{agent.emoji}</div>
                                <h3 className="font-semibold mb-1">{agent.name}</h3>
                                <p className="text-sm text-muted-foreground">{agent.desc}</p>
                                {index < agents.length - 1 && (
                                    <div className="hidden md:block absolute right-0 top-1/2 -translate-y-1/2 translate-x-full">
                                        <ArrowRight className="w-4 h-4 text-muted-foreground" />
                                    </div>
                                )}
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section className="py-20 px-6 relative" id="features">
                <div className="max-w-7xl mx-auto">
                    <motion.div
                        initial={{ opacity: 0 }}
                        whileInView={{ opacity: 1 }}
                        viewport={{ once: true }}
                        className="text-center mb-16"
                    >
                        <h2 className="text-3xl md:text-4xl font-bold mb-4">
                            Built for <span className="gradient-text">Performance</span>
                        </h2>
                        <p className="text-muted-foreground max-w-xl mx-auto">
                            Optimized for Apple Silicon with local LLM inference
                        </p>
                    </motion.div>

                    <div className="grid md:grid-cols-2 gap-6">
                        {features.map((feature, index) => (
                            <motion.div
                                key={feature.title}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: index * 0.1 }}
                                className="glass rounded-xl p-6 hover:glow-accent transition-shadow cursor-default"
                                onMouseEnter={() => setHoveredFeature(index)}
                                onMouseLeave={() => setHoveredFeature(null)}
                            >
                                <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 transition-colors ${hoveredFeature === index
                                        ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white'
                                        : 'bg-secondary text-muted-foreground'
                                    }`}>
                                    {feature.icon}
                                </div>
                                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                                <p className="text-muted-foreground">{feature.description}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-20 px-6 relative">
                <div className="max-w-4xl mx-auto text-center">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        viewport={{ once: true }}
                        className="glass-strong rounded-2xl p-12"
                    >
                        <CheckCircle2 className="w-16 h-16 text-green-400 mx-auto mb-6" />
                        <h2 className="text-3xl md:text-4xl font-bold mb-4">
                            Ready to Modernize?
                        </h2>
                        <p className="text-muted-foreground mb-8 max-w-lg mx-auto">
                            Drop your legacy C++ or Java code and watch as LegacyLens transforms it into
                            modern, type-safe Python with comprehensive documentation.
                        </p>
                        <Link
                            href="/refactor"
                            className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-semibold text-lg hover:opacity-90 transition-all glow-primary"
                        >
                            <Sparkles className="w-5 h-5" />
                            Start Refactoring Now
                        </Link>
                    </motion.div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-8 px-6 border-t border-border">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-indigo-500" />
                        <span className="font-semibold">LegacyLens</span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                        Built with LangGraph, llama.cpp, and ❤️ on Apple Silicon
                    </p>
                    <a
                        href="https://github.com/fozanmujtaba/LegacyLens"
                        target="_blank"
                        className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                        GitHub Repository
                    </a>
                </div>
            </footer>
        </main>
    );
}
