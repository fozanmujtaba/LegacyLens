"""
LegacyLens - Task 2: Model Integration
======================================
Robust implementation for loading quantized Mistral/Llama models
on Apple Silicon using llama-cpp-python with Metal acceleration.

Author: LegacyLens AI Architect
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, Literal, Generator
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelBackend(str, Enum):
    """Supported inference backends."""
    LLAMA_CPP = "llama_cpp"
    MLX = "mlx"
    LANGCHAIN = "langchain"


class QuantizationType(str, Enum):
    """GGUF quantization levels."""
    Q4_0 = "Q4_0"
    Q4_K_M = "Q4_K_M"
    Q5_K_M = "Q5_K_M"
    Q6_K = "Q6_K"
    Q8_0 = "Q8_0"

    
@dataclass
class ModelConfig:
    """Configuration for model loading and inference."""
    model_path: str
    model_name: str = "mistral-small-3"
    quantization: QuantizationType = QuantizationType.Q4_K_M
    n_gpu_layers: int = -1  # -1 = all layers on Metal GPU
    n_batch: int = 512
    n_ctx: int = 8192
    max_tokens: int = 4096
    temperature: float = 0.1
    top_p: float = 0.95
    top_k: int = 40
    repeat_penalty: float = 1.1
    n_threads: int = 8  # M2 Pro performance cores
    n_threads_batch: int = 8
    use_mmap: bool = True
    use_mlock: bool = False
    verbose: bool = False
    
    @classmethod
    def for_mistral_small(cls, model_path: str, quantization: QuantizationType = QuantizationType.Q4_K_M):
        """Optimized config for Mistral-Small-3 24B."""
        return cls(model_path=model_path, model_name="mistral-small-3-24b", 
                   quantization=quantization, n_ctx=8192, n_batch=512)
    
    @classmethod
    def for_qwen_coder(cls, model_path: str, quantization: QuantizationType = QuantizationType.Q4_K_M):
        """Optimized config for Qwen2.5-Coder-7B."""
        return cls(
            model_path=model_path, 
            model_name="qwen2.5-coder-7b",
            quantization=quantization, 
            n_ctx=8192,  # Qwen supports up to 32K but 8K is more efficient
            n_batch=512,
            max_tokens=4096,
            temperature=0.1,  # Low temp for code generation
            n_gpu_layers=-1,  # All layers on Metal
        )


class LegacyLensLLM:
    """High-performance LLM wrapper optimized for Apple Silicon."""
    
    def __init__(self, config: ModelConfig, backend: ModelBackend = ModelBackend.LLAMA_CPP):
        self.config = config
        self.backend = backend
        self._model = None
        self._tokenizer = None
        self._load_model()
    
    def _load_model(self) -> None:
        if self.backend == ModelBackend.LLAMA_CPP:
            self._load_llama_cpp()
        elif self.backend == ModelBackend.MLX:
            self._load_mlx()
        elif self.backend == ModelBackend.LANGCHAIN:
            self._load_langchain()
    
    def _load_llama_cpp(self) -> None:
        from llama_cpp import Llama
        logger.info(f"Loading model: {self.config.model_path}")
        self._model = Llama(
            model_path=self.config.model_path, n_ctx=self.config.n_ctx,
            n_batch=self.config.n_batch, n_gpu_layers=self.config.n_gpu_layers,
            n_threads=self.config.n_threads, use_mmap=self.config.use_mmap,
            verbose=self.config.verbose,
        )
        logger.info("Model loaded with Metal acceleration")
    
    def _load_mlx(self) -> None:
        from mlx_lm import load, generate
        self._model, self._tokenizer = load(self.config.model_path)
        self._mlx_generate = generate
    
    def _load_langchain(self) -> None:
        from langchain_community.llms import LlamaCpp
        self._model = LlamaCpp(
            model_path=self.config.model_path, n_ctx=self.config.n_ctx,
            n_gpu_layers=self.config.n_gpu_layers, temperature=self.config.temperature,
        )
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 max_tokens: Optional[int] = None, stop: Optional[list[str]] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self._model.create_chat_completion(
            messages=messages, max_tokens=max_tokens or self.config.max_tokens,
            temperature=self.config.temperature, stop=stop or ["```\n\n"],
        )
        return response["choices"][0]["message"]["content"]
    
    def count_tokens(self, text: str) -> int:
        return len(self._model.tokenize(text.encode()))
    
    @property
    def context_size(self) -> int:
        return self.config.n_ctx


# Global model instance (loaded once)
_global_model: Optional[LegacyLensLLM] = None


def load_model(model_path: str, model_type: Literal["mistral", "llama", "qwen"] = "qwen") -> LegacyLensLLM:
    """Load a model with sensible defaults."""
    if model_type == "qwen":
        config = ModelConfig.for_qwen_coder(model_path)
    elif model_type == "mistral":
        config = ModelConfig.for_mistral_small(model_path)
    else:
        config = ModelConfig.for_llama_3_2(model_path)
    return LegacyLensLLM(config)


def get_model() -> Optional[LegacyLensLLM]:
    """Get the global model instance."""
    global _global_model
    return _global_model


def initialize_model(model_path: str, model_type: str = "qwen") -> LegacyLensLLM:
    """Initialize and cache the global model."""
    global _global_model
    if _global_model is None:
        _global_model = load_model(model_path, model_type)
    return _global_model
