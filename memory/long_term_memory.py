import uuid
from datetime import datetime, timezone

# -------------------------------
# Long Term Memory
# -------------------------------
class LongTermMemory:
    REQUIRED_FIELDS = ["type", "importance", "confidence"]

    def __init__(
        self,
        store,
    ):
        self.store = store

    # -------------------------------
    # VALIDATE METADATA FROM JUDGE
    # -------------------------------
    def _validate_metadata(self, metadata):
        if not metadata:
            return False, "Metadata missing"

        for field in self.REQUIRED_FIELDS:
            if field not in metadata:
                return False, f"Missing required field: {field}"

        if not isinstance(metadata["importance"], int) or not (1 <= metadata["importance"] <= 5):
            return False, "importance must be int 1–5"

        if not isinstance(metadata["confidence"], (float, int)) or not (0 <= metadata["confidence"] <= 1):
            return False, "confidence must be 0–1"

        return True, None


    # -------------------------------
    # ADD MEMORY (Judge-Controlled)
    # -------------------------------
    def add(self, text: str, metadata: dict):
        """
        text      -> ONE SENTENCE compressed memory from judge
        metadata  -> judge-generated structured metadata
        """

        if not text or not text.strip():
            print("⚠️ Skipping empty memory text")
            return

        ok, err = self._validate_metadata(metadata)
        if not ok:
            print(f"⚠️ Memory rejected due to invalid metadata → {err}")
            return
        memory_id = str(uuid.uuid4())
        metadata = dict(metadata)  # avoid modifying input
        metadata.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        metadata.setdefault("source", "conversation")
        metadata.setdefault("tags", [])
        metadata["memory_id"] = memory_id   # << ⭐ KEY FIX

        try:
            # print(f"💾 SAVING MEMORY → {text}")
            self.store.add_texts(
                texts=[text.strip()],
                metadatas=[metadata],
                ids=[memory_id]
            )

        except Exception as e:
            # print(f"❌ Memory write failed: {e}")
            pass


    # -------------------------------
    # QUERY MEMORY
    # -------------------------------
    def query(self, text: str, k=5, min_importance=3, type_filter=None):
        if not text or not text.strip():
            return []

        try:
            where = {}
            if min_importance is not None:
                where["importance"] = {"$gte": min_importance}

            if type_filter:
                where["type"] = type_filter

            results = self.store.similarity_search(
                query_texts=[text],
                n_results=k,
                where=where if where else None
            )

            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]

            return [
                {
                    "text": d,
                    "metadata": m
                }
                for d, m in zip(docs, metas)
            ]

        except Exception as e:
            print(f"❌ Memory query failed: {e}")
            return []
        
        # -------------------------------
    # SEARCH (LangChain Chroma compatible)
    # -------------------------------
    def search(self, query: str, top_k=5):
        """
        Returns:
        [
            {
                "id": "...",
                "text": "...",
                "metadata": {...},
                "score": float   # 0..1 , higher = better
            },
            ...
        ]
        """

        if not query or not query.strip():
            return []

        try:
            results = self.store.similarity_search_with_score(
                query=query,
                k=top_k
            )

            combined = []
            for doc, dist in results:
                # Convert Chroma distance to similarity (higher = more similar)
                try:
                    distance = float(dist)
                    similarity = 1.0 / (1.0 + distance)
                except:
                    similarity = 0.0

                # Chroma VectorStore does NOT expose ids directly.
                # However since we stored with ids, LangChain places it inside metadata.
                mem_id = (
                    doc.metadata.get("memory_id")
                    or doc.metadata.get("id")
                    or doc.metadata.get("uuid")
                )

                combined.append({
                    "id": mem_id,
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                    "score": similarity
                })

            return combined

        except Exception as e:
            print(f"❌ Memory search failed: {e}")
            return []


    # -------------------------------
    # UPDATE MEMORY
    # -------------------------------
    def update(self, id: str, new_text: str, new_metadata: dict = None):
        """
        Replace an existing memory's text (and optionally metadata).

        If backend doesn't support true update,
        we emulate by deleting + re-adding same ID.
        """

        if not id:
            print("⚠️ Update failed: no memory id provided")
            return

        if not new_text or not new_text.strip():
            print("⚠️ Update skipped: empty text")
            return

        try:
            # Fetch existing entry so we don't lose metadata
            existing = self.store.get(ids=[id])

            if not existing or not existing.get("ids"):
                print("⚠️ Update failed: memory not found")
                return

            old_meta = existing["metadatas"][0]

            # merge metadata if provided
            if new_metadata:
                old_meta.update(new_metadata)

            # delete existing
            try:
                self.store.delete(ids=[id])
            except Exception as e:
                print("⚠️ Delete during update failed:", e)

            # re-insert with same ID
            self.store.add_texts(
                texts=[new_text.strip()],
                metadatas=[old_meta],
                ids=[id]
            )

            print(f"♻️ Memory updated → {new_text}")

        except Exception as e:
            print(f"❌ Memory update failed: {e}")
