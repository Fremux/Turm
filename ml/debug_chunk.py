"""Debug script to inspect chunk structure."""
from chonkie import SemanticChunker
from app.services.deepinfra_embeddings import deepinfra_embeddings

# Sample text
text = "Это тестовый текст. " * 100  # Create long text

# Create chunker
chunker = SemanticChunker(
    embedding_model=deepinfra_embeddings,
    chunk_size=512,
    threshold=0.7
)

# Chunk the text
chunks = chunker.chunk(text)

if chunks:
    chunk = chunks[0]
    print("Chunk attributes:")
    print(dir(chunk))
    print("\nChunk.__dict__:")
    print(chunk.__dict__)
    print("\nChunk.text length:", len(chunk.text) if hasattr(chunk, 'text') else 'N/A')
