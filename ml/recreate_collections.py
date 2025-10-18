"""Script to recreate Qdrant collections with correct dimensions and populate them."""

import os
import sys
import json
import asyncio
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.qdrant_service import qdrant_service
from app.core.config import settings
from app.core.logging import logger


async def recreate_collections():
    """Recreate all knowledge base collections with correct dimensions."""
    
    # Collections to create
    collections = ["it", "hr", "finance", "office"]
    
    print(f"\n{'='*60}")
    print(f"  RECREATING QDRANT COLLECTIONS")
    print(f"{'='*60}\n")
    print(f"📋 Embedding Model: {settings.EMBEDDING_MODEL}")
    print(f"📏 Embedding Dimension: {settings.EMBEDDING_DIMENSION}")
    print(f"🎯 Qdrant Host: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    print(f"\n{'='*60}\n")
    
    # Step 1: List existing collections
    print("📊 Listing existing collections...")
    try:
        existing = qdrant_service.list_collections()
        if existing:
            print("\n  Existing collections:")
            for col in existing:
                print(f"    - {col['name']}: {col['vectors_count']} vectors, dimension {col['vector_size']}")
        else:
            print("  No existing collections found.")
    except Exception as e:
        print(f"  ⚠️  Warning: Could not list collections: {e}")
    
    print()
    
    # Step 2: Delete and recreate each collection
    for collection_name in collections:
        print(f"{'─'*60}")
        print(f"🔄 Processing collection: {collection_name}")
        print(f"{'─'*60}")
        
        # Delete if exists
        try:
            existing_names = [c['name'] for c in qdrant_service.list_collections()]
            if collection_name in existing_names:
                print(f"  🗑️  Deleting existing collection '{collection_name}'...")
                qdrant_service.delete_collection(collection_name)
                print(f"  ✅ Deleted successfully")
            else:
                print(f"  ℹ️  Collection '{collection_name}' does not exist")
        except Exception as e:
            print(f"  ⚠️  Could not delete collection: {e}")
        
        # Create new collection
        try:
            print(f"  🆕 Creating collection '{collection_name}' with dimension {settings.EMBEDDING_DIMENSION}...")
            result = qdrant_service.create_collection(
                collection_name=collection_name,
                embedding_size=settings.EMBEDDING_DIMENSION,
                distance="Cosine"
            )
            print(f"  ✅ Created successfully")
        except Exception as e:
            print(f"  ❌ Error creating collection: {e}")
            continue
    
    print(f"\n{'='*60}")
    print("✅ Collections recreation completed!")
    print(f"{'='*60}\n")
    
    # Step 3: Verify collections
    print("🔍 Verifying created collections...")
    try:
        collections_info = qdrant_service.list_collections()
        print("\n  Created collections:")
        for col in collections_info:
            print(f"    - {col['name']}: dimension {col['vector_size']}")
    except Exception as e:
        print(f"  ⚠️  Could not verify collections: {e}")
    
    print()


async def load_knowledge_base():
    """Load knowledge base data from JSON files into collections."""
    
    print(f"\n{'='*60}")
    print(f"  LOADING KNOWLEDGE BASE DATA")
    print(f"{'='*60}\n")
    
    # Map category files to collections
    category_files = {
        "it": "/root/Turm/ml/category_it.json",
        "hr": "/root/Turm/ml/category_hr.json",
        "finance": "/root/Turm/ml/category_finance.json",
        "office": "/root/Turm/ml/category_office.json"
    }
    
    for category, file_path in category_files.items():
        print(f"{'─'*60}")
        print(f"📂 Loading data for category: {category}")
        print(f"{'─'*60}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"  ⚠️  File not found: {file_path}")
            print(f"  ⏭️  Skipping {category}")
            continue
        
        # Load JSON data
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data:
                print(f"  ⚠️  File is empty: {file_path}")
                print(f"  ⏭️  Skipping {category}")
                continue
            
            print(f"  📄 Loaded {len(data)} items from {file_path}")
        except Exception as e:
            print(f"  ❌ Error loading file: {e}")
            continue
        
        # Upload each item as a document
        print(f"  ⬆️  Uploading documents to collection '{category}'...")
        uploaded_count = 0
        error_count = 0
        
        for idx, item in enumerate(data, 1):
            try:
                # Get text content
                text = item.get('text', '')
                if not text or not text.strip():
                    continue
                
                # Create metadata
                metadata = {
                    "category": category,
                    "line": item.get('line', idx),
                    "original_file": file_path
                }
                
                # Upload document
                result = await qdrant_service.upload_document(
                    file_path=f"{category}_{idx}.txt",
                    content=text,
                    user_id=0,  # System user
                    metadata=metadata,
                    collection_name=category,
                    chunk_size=512,
                    chunk_overlap=128,
                    chunker_type="token"
                )
                
                uploaded_count += 1
                
                # Progress indicator
                if uploaded_count % 10 == 0:
                    print(f"    Progress: {uploaded_count}/{len(data)} documents uploaded...")
                    
            except Exception as e:
                error_count += 1
                if error_count <= 3:  # Only show first 3 errors
                    print(f"    ⚠️  Error uploading item {idx}: {e}")
        
        print(f"  ✅ Uploaded {uploaded_count} documents")
        if error_count > 0:
            print(f"  ⚠️  Failed to upload {error_count} documents")
        
        # Verify collection
        try:
            col_info = qdrant_service.get_collection_info(category)
            print(f"  📊 Collection '{category}' now has {col_info['points_count']} vectors")
        except Exception as e:
            print(f"  ⚠️  Could not verify collection: {e}")
    
    print(f"\n{'='*60}")
    print("✅ Knowledge base loading completed!")
    print(f"{'='*60}\n")


async def main():
    """Main function."""
    try:
        # Step 1: Recreate collections
        await recreate_collections()
        
        # Step 2: Load knowledge base data
        print("\n⏳ Proceeding to load knowledge base data...\n")
        await asyncio.sleep(1)  # Brief pause
        await load_knowledge_base()
        
        print("\n" + "="*60)
        print("🎉 ALL DONE!")
        print("="*60)
        print("\n✨ Your Qdrant collections are now ready with correct dimensions.")
        print("✨ Knowledge base data has been loaded successfully.")
        print("\nYou can now restart your application and test the search functionality.\n")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

