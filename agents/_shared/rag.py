"""
TRADO RAG System — Retrieval Augmented Generation
Qdrant Vector DB لاسترجاع المعرفة المتخصصة لكل agent
"""
import os
from typing import Optional
from pathlib import Path
from loguru import logger


class RAGSystem:
    """
    نظام استرجاع المعرفة باستخدام Qdrant
    كل agent له collection خاصة في قاعدة المتجهات
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.collection_name = f"trado_{agent_id}"
        self._client = None
        self._embedder = None

    async def _get_client(self):
        if self._client is None:
            try:
                from qdrant_client import QdrantClient
                from config.settings import settings
                self._client = QdrantClient(
                    url=settings.qdrant_url,
                    api_key=settings.qdrant_api_key or None
                )
            except Exception as e:
                logger.warning(f"Qdrant unavailable: {e} — RAG disabled")
        return self._client

    async def _get_embedder(self):
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e:
                logger.warning(f"Embedder unavailable: {e}")
        return self._embedder

    async def ingest_documents(self, docs_dir: str):
        """استيعاب ملفات المعرفة في قاعدة المتجهات"""
        client = await self._get_client()
        embedder = await self._get_embedder()

        if not client or not embedder:
            logger.warning("RAG ingestion skipped — services unavailable")
            return

        docs_path = Path(docs_dir)
        if not docs_path.exists():
            logger.warning(f"Docs dir not found: {docs_dir}")
            return

        chunks = []
        for md_file in docs_path.glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            # تقطيع المحتوى إلى أجزاء
            paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 50]
            for i, para in enumerate(paragraphs):
                chunks.append({
                    "id": f"{md_file.stem}_{i}",
                    "text": para,
                    "source": md_file.name
                })

        if not chunks:
            return

        try:
            from qdrant_client.models import VectorParams, Distance, PointStruct

            # إنشاء collection إذا لم تكن موجودة
            collections = client.get_collections().collections
            existing = [c.name for c in collections]

            if self.collection_name not in existing:
                client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )

            # توليد embeddings
            texts = [c["text"] for c in chunks]
            embeddings = embedder.encode(texts, show_progress_bar=False)

            points = [
                PointStruct(
                    id=abs(hash(c["id"])) % (2**63),
                    vector=emb.tolist(),
                    payload={"text": c["text"], "source": c["source"]}
                )
                for c, emb in zip(chunks, embeddings)
            ]

            client.upsert(collection_name=self.collection_name, points=points)
            logger.info(f"RAG: ingested {len(points)} chunks for {self.agent_id}")

        except Exception as e:
            logger.error(f"RAG ingestion error: {e}")

    async def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        """استرجاع أكثر النصوص صلة بالاستعلام"""
        client = await self._get_client()
        embedder = await self._get_embedder()

        if not client or not embedder:
            return []

        try:
            query_vector = embedder.encode(query).tolist()
            # Qdrant v1.10+ uses query_points instead of deprecated search()
            results = client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k,
                score_threshold=0.5
            )
            # query_points returns QueryResponse, points are in .points attribute
            points = results.points if hasattr(results, "points") else results
            return [p.payload["text"] for p in points if p.payload]
        except Exception as e:
            logger.error(f"RAG retrieval error: {e}")
            return []

    def format_context(self, chunks: list[str]) -> str:
        """تنسيق المعرفة المسترجعة كـ context"""
        if not chunks:
            return ""
        return "\n\n[KNOWLEDGE BASE]\n" + "\n---\n".join(chunks) + "\n[/KNOWLEDGE BASE]\n"
