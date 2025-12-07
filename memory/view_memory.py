from chromadb import PersistentClient
import json
import os

# ⚠️ MUST MATCH YOUR REAL MEMORY PATH
CHROMA_PATH = "memory_store"    # change if yours is different
COLLECTION_NAME = "jarvis_memory"  # must match exactly

print("📂 CHROMA PATH IN VIEWER:", os.path.abspath(CHROMA_PATH))

def main():
    print("🔍 Connecting to ChromaDB...")
    client = PersistentClient(CHROMA_PATH)
    collection = client.get_or_create_collection(COLLECTION_NAME)

    print("✅ Connected.")
    print("📦 Fetching all memories...\n")

    data = collection.get()

    documents = data.get("documents", [])
    metadatas = data.get("metadatas", [])
    ids = data.get("ids", [])

    if not documents:
        print("❌ NO MEMORY FOUND AT ALL.")
        print("→ This means your memory is NOT being saved.")
        return

    print(f"✅ TOTAL MEMORIES: {len(documents)}\n")

    for i, (doc, meta, _id) in enumerate(zip(documents, metadatas, ids), start=1):
        print("=" * 60)
        print(f"🧠 MEMORY #{i}")
        print(f"🆔 ID: {_id}")
        print(f"📄 TEXT:\n{doc}")
        print(f"🏷️ METADATA:\n{json.dumps(meta, indent=2)}")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
