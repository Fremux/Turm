"""DeepInfra embeddings wrapper for Chonkie integration."""

from typing import List, Union
import numpy as np
from openai import OpenAI

try:
    from chonkie.embeddings.base import BaseEmbeddings
except ImportError:
    # Fallback if BaseEmbeddings is not available
    BaseEmbeddings = object

from app.core.config import settings
from app.core.logging import logger


class DeepInfraEmbeddings(BaseEmbeddings):
    """Custom embeddings class for DeepInfra that works with Chonkie."""
    
    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = None,
        dimension: int = None
    ):
        """Initialize DeepInfra embeddings client.
        
        Args:
            api_key: DeepInfra API key (defaults to settings.EMBEDDING_KEY)
            base_url: DeepInfra base URL (defaults to settings.EMBEDDING_URL)
            model: Model name (defaults to settings.EMBEDDING_MODEL)
            dimension: Embedding dimension (defaults to settings.EMBEDDING_DIMENSION)
        """
        # Initialize parent class if it's BaseEmbeddings
        if BaseEmbeddings != object:
            super().__init__()
        
        self.api_key = api_key or settings.EMBEDDING_KEY
        self.base_url = base_url or settings.EMBEDDING_URL
        self.model = model or settings.EMBEDDING_MODEL
        self._dimension = dimension or settings.EMBEDDING_DIMENSION
        
        # Create OpenAI client configured for DeepInfra
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        
        logger.info(
            "deepinfra_embeddings_initialized",
            model=self.model,
            base_url=self.base_url,
            dimension=self._dimension
        )
    
    def embed(self, text: str) -> np.ndarray:
        """Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            return np.array(embedding, dtype=np.float32)
            
        except Exception as e:
            logger.error(
                "embedding_error",
                error=str(e),
                text_length=len(text),
                exc_info=True
            )
            raise
    
    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors as numpy arrays
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
                encoding_format="float"
            )
            
            embeddings = [
                np.array(data.embedding, dtype=np.float32)
                for data in response.data
            ]
            
            logger.info(
                "batch_embeddings_generated",
                count=len(embeddings),
                total_tokens=response.usage.prompt_tokens
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(
                "batch_embedding_error",
                error=str(e),
                batch_size=len(texts),
                exc_info=True
            )
            raise
    
    def __call__(self, text: Union[str, List[str]]) -> Union[np.ndarray, List[np.ndarray]]:
        """Make the embeddings callable.
        
        Args:
            text: Single text or list of texts
            
        Returns:
            Single embedding or list of embeddings
        """
        if isinstance(text, str):
            return self.embed(text)
        else:
            return self.embed_batch(text)
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension.
        
        Returns:
            Embedding dimension
        """
        return self._dimension
    
    def get_tokenizer(self):
        """Return a simple token counter (required by BaseEmbeddings).
        
        This is required by Chonkie's BaseEmbeddings interface.
        For DeepInfra, we'll use a simple character-based approximation.
        
        Returns:
            A callable that takes text and returns token count
        """
        return lambda text: len(text) // 4  # Rough approximation: ~4 chars per token
    
    def get_tokenizer_or_token_counter(self):
        """Return a simple token counter (alias for compatibility).
        
        This is required by Chonkie's BaseEmbeddings interface.
        For DeepInfra, we'll use a simple character-based approximation.
        """
        return self.get_tokenizer()
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text (convenience method).
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Approximate token count
        """
        return self.get_tokenizer()(text)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"DeepInfraEmbeddings(model={self.model}, dimension={self._dimension})"


# Create a global instance
deepinfra_embeddings = DeepInfraEmbeddings()

