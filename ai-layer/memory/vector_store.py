"""FAISS-backed vector store for user preference memory."""
import os
import json
import hashlib
import numpy as np
from typing import Optional
from dataclasses import dataclass


@dataclass
class MemoryEntry:
    user_id: str
    content: str
    metadata: dict
    embedding: Optional[list[float]] = None


class VectorStore:
    def __init__(self, dimension: int = 1536, index_path: Optional[str] = None):
        try:
            import faiss
            self._faiss = faiss
            self.index = faiss.IndexFlatL2(dimension)
        except ImportError:
            self._faiss = None
            self.index = None

        self.dimension = dimension
        self.entries: list[MemoryEntry] = []
        self.index_path = index_path or os.getenv("FAISS_INDEX_PATH", "/tmp/travel_ai_faiss")

        if os.path.exists(f"{self.index_path}.json"):
            self._load()

    def _embed_mock(self, text: str) -> list[float]:
        """Deterministic mock embedding using hashing (dev fallback, no API key needed)."""
        h = hashlib.sha256(text.encode()).digest()
        floats = [((b / 255.0) - 0.5) * 2 for b in h]
        full = (floats * (self.dimension // len(floats) + 1))[: self.dimension]
        norm = (sum(x * x for x in full) ** 0.5) or 1.0
        return [x / norm for x in full]

    async def embed(self, text: str) -> list[float]:
        """Embed text using OpenAI-compatible embeddings or a mock for dev."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return self._embed_mock(text)

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"model": "text-embedding-3-small", "input": text},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    return resp.json()["data"][0]["embedding"]
        except Exception:
            pass
        return self._embed_mock(text)

    async def add(self, entry: MemoryEntry) -> None:
        if entry.embedding is None:
            entry.embedding = await self.embed(entry.content)

        self.entries.append(entry)
        if self.index is not None:
            vec = np.array([entry.embedding], dtype=np.float32)
            self.index.add(vec)
        self._save()

    async def search(self, query: str, user_id: str, top_k: int = 5) -> list[MemoryEntry]:
        if not self.entries:
            return []

        user_entries = [(i, e) for i, e in enumerate(self.entries) if e.user_id == user_id]
        if not user_entries:
            return []

        query_vec = await self.embed(query)

        if self.index is not None and len(user_entries) > 0:
            q = np.array([query_vec], dtype=np.float32)
            _, indices = self.index.search(q, min(top_k * 2, len(self.entries)))
            idx_set = {i for i, _ in user_entries}
            return [
                self.entries[i] for i in indices[0]
                if i in idx_set and i < len(self.entries)
            ][:top_k]

        # Fallback: cosine similarity
        def cosine(a: list[float], b: list[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            na = sum(x * x for x in a) ** 0.5
            nb = sum(x * x for x in b) ** 0.5
            return dot / (na * nb + 1e-9)

        scored = [
            (cosine(query_vec, e.embedding or []), e)
            for _, e in user_entries
            if e.embedding
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:top_k]]

    async def store_preference(self, user_id: str, preference: str, metadata: dict = None) -> None:
        await self.add(MemoryEntry(
            user_id=user_id,
            content=preference,
            metadata=metadata or {},
        ))

    async def get_user_context(self, user_id: str, query: str) -> str:
        memories = await self.search(query, user_id)
        if not memories:
            return ""
        lines = [f"- {m.content}" for m in memories]
        return "User's past preferences:\n" + "\n".join(lines)

    def _save(self) -> None:
        try:
            if self.index is not None:
                self._faiss.write_index(self.index, f"{self.index_path}.faiss")
            with open(f"{self.index_path}.json", "w") as f:
                json.dump(
                    [{"user_id": e.user_id, "content": e.content, "metadata": e.metadata, "embedding": e.embedding}
                     for e in self.entries],
                    f,
                )
        except Exception:
            pass

    def _load(self) -> None:
        try:
            with open(f"{self.index_path}.json") as f:
                raw = json.load(f)
            self.entries = [MemoryEntry(**r) for r in raw]
            faiss_path = f"{self.index_path}.faiss"
            if self.index is not None and os.path.exists(faiss_path):
                self.index = self._faiss.read_index(faiss_path)
        except Exception:
            pass


_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
