"""Script to check Qdrant collections status."""

import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.qdrant_service import qdrant_service
from app.core.config import settings


def check_collections():
    """Check status of all collections."""
    
    print(f"\n{'='*70}")
    print(f"  QDRANT COLLECTIONS STATUS")
    print(f"{'='*70}\n")
    print(f"📋 Embedding Model: {settings.EMBEDDING_MODEL}")
    print(f"📏 Expected Dimension: {settings.EMBEDDING_DIMENSION}")
    print(f"🎯 Qdrant Host: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    print(f"\n{'='*70}\n")
    
    try:
        collections = qdrant_service.list_collections()
        
        if not collections:
            print("❌ No collections found!\n")
            print("You need to create collections with the command:")
            print("  python3 recreate_collections.py\n")
            return
        
        print(f"✅ Found {len(collections)} collection(s):\n")
        
        # Collections we expect for knowledge base
        expected_collections = ["it", "hr", "finance", "office"]
        
        for col in collections:
            name = col['name']
            vectors_count = col['vectors_count']
            vector_size = col['vector_size']
            
            # Check if dimension is correct
            dimension_status = "✅" if vector_size == settings.EMBEDDING_DIMENSION else "❌"
            
            # Check if it's a knowledge base collection
            is_kb = "📚 KB" if name in expected_collections else "📄 Doc"
            
            print(f"  {dimension_status} {is_kb} Collection: {name}")
            print(f"     - Vectors: {vectors_count}")
            print(f"     - Dimension: {vector_size} (expected: {settings.EMBEDDING_DIMENSION})")
            print()
        
        # Check for missing knowledge base collections
        existing_names = [col['name'] for col in collections]
        missing = [name for name in expected_collections if name not in existing_names]
        
        if missing:
            print(f"⚠️  Missing knowledge base collections: {', '.join(missing)}\n")
        
        # Check for wrong dimensions
        wrong_dim = [col for col in collections if col['vector_size'] != settings.EMBEDDING_DIMENSION]
        
        if wrong_dim:
            print(f"{'─'*70}")
            print(f"❌ WARNING: {len(wrong_dim)} collection(s) have WRONG dimension!")
            print(f"{'─'*70}\n")
            for col in wrong_dim:
                print(f"  - {col['name']}: has {col['vector_size']}, expected {settings.EMBEDDING_DIMENSION}")
            print("\nThese collections need to be recreated with correct dimension:")
            print("  python3 recreate_collections.py\n")
        else:
            print(f"{'─'*70}")
            print(f"✅ All collections have correct dimension ({settings.EMBEDDING_DIMENSION})")
            print(f"{'─'*70}\n")
    
    except Exception as e:
        print(f"❌ Error checking collections: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_collections()

