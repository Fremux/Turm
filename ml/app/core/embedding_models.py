"""Centralized embedding model configurations."""

from typing import Dict, Tuple

# Available embedding models with their dimensions
EMBEDDING_MODELS: Dict[str, Tuple[str, int]] = {
    "qwen-0.6b": ("Qwen/Qwen3-Embedding-0.6B", 768),
    "qwen-4b": ("Qwen/Qwen3-Embedding-4B", 2048),
    "qwen-8b": ("Qwen/Qwen3-Embedding-8B", 4096),
    "bge-m3": ("BAAI/bge-m3", 1024),
    "gemma-300m": ("google/embeddinggemma-300m", 256),
}

# Default model
DEFAULT_MODEL = "bge-m3"
DEFAULT_MODEL_NAME, DEFAULT_DIMENSION = EMBEDDING_MODELS[DEFAULT_MODEL]


def get_model_info(model_key: str) -> Tuple[str, int]:
    """Get model name and dimension by key.
    
    Args:
        model_key: Short key like 'qwen-8b', 'bge-m3', etc.
        
    Returns:
        Tuple of (model_name, dimension)
    """
    if model_key in EMBEDDING_MODELS:
        return EMBEDDING_MODELS[model_key]
    
    # If full model name is provided, try to find it
    for key, (name, dim) in EMBEDDING_MODELS.items():
        if name == model_key:
            return name, dim
    
    # Default fallback
    return DEFAULT_MODEL_NAME, DEFAULT_DIMENSION


def get_model_key_by_name(model_name: str) -> str:
    """Get model key by full model name.
    
    Args:
        model_name: Full model name like 'Qwen/Qwen3-Embedding-8B'
        
    Returns:
        Model key like 'qwen-8b'
    """
    for key, (name, _) in EMBEDDING_MODELS.items():
        if name == model_name:
            return key
    return DEFAULT_MODEL




