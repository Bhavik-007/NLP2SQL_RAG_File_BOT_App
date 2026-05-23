import logging
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

from app.core.config import config
from app.engine.document_loader import DocumentChunk


class DocumentVectorStore:
    def __init__(self):
        rag_settings = config.rag_settings.get("rag", {})
        self.collection = rag_settings.get("collection_name", "document_chunks")
        self.client = QdrantClient(url=config.qdrant_url)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.available = self._setup_collection()
        self.memory_points: list[dict] = []

    def _setup_collection(self) -> bool:
        try:
            collections = self.client.get_collections().collections
            if not any(item.name == self.collection for item in collections):
                self.client.create_collection(
                    collection_name=self.collection,
                    vectors_config=models.VectorParams(
                        size=384,
                        distance=models.Distance.COSINE,
                    ),
                )
            return True
        except Exception as exc:
            logging.error(f"Document Qdrant Init Error: {exc}")
            return False

    def add_chunks(self, chunks: list[DocumentChunk]) -> int:
        if not chunks:
            return 0

        vectors = self.model.encode([chunk.text for chunk in chunks]).tolist()

        if self.available:
            points = []
            for chunk, vector in zip(chunks, vectors):
                points.append(
                    models.PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vector,
                        payload={
                            "text": chunk.text,
                            **chunk.metadata,
                        },
                    )
                )
            try:
                self.client.upsert(collection_name=self.collection, points=points)
                return len(points)
            except Exception as exc:
                logging.error(f"Document Qdrant Upsert Error: {exc}")
                self.available = False

        for chunk, vector in zip(chunks, vectors):
            self.memory_points.append(
                {
                    "vector": vector,
                    "text": chunk.text,
                    "metadata": chunk.metadata,
                }
            )
        return len(chunks)

    def search(self, query: str, top_k: int = 4) -> list[dict]:
        query_vector = self.model.encode(query).tolist()

        if self.available:
            try:
                results = self.client.search(
                    collection_name=self.collection,
                    query_vector=query_vector,
                    limit=top_k,
                )
                return [
                    {
                        "text": item.payload.get("text", ""),
                        "metadata": {
                            key: value
                            for key, value in item.payload.items()
                            if key != "text"
                        },
                        "score": item.score,
                    }
                    for item in results
                ]
            except Exception as exc:
                logging.error(f"Document Qdrant Search Error: {exc}")
                self.available = False

        scored = []
        for point in self.memory_points:
            scored.append(
                {
                    "text": point["text"],
                    "metadata": point["metadata"],
                    "score": self._cosine_similarity(query_vector, point["vector"]),
                }
            )
        return sorted(scored, key=lambda item: item["score"], reverse=True)[:top_k]

    def has_content(self) -> bool:
        if self.memory_points:
            return True

        if not self.available:
            return False

        try:
            info = self.client.count(collection_name=self.collection, exact=False)
            return bool(info.count)
        except Exception as exc:
            logging.error(f"Document Qdrant Count Error: {exc}")
            self.available = False
            return False

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        dot = sum(a * b for a, b in zip(left, right))
        left_norm = sum(a * a for a in left) ** 0.5
        right_norm = sum(b * b for b in right) ** 0.5
        if not left_norm or not right_norm:
            return 0.0
        return dot / (left_norm * right_norm)
