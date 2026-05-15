from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from datetime import datetime
import uuid

class QdrantManager:
    COLLECTIONS = ["trading_expertise","market_intelligence","user_behavior","brand_knowledge"]
    VECTOR_SIZE = 1536

    def __init__(self, config):
        self.client = QdrantClient(url=config["QDRANT_URL"], api_key=config.get("QDRANT_API_KEY"))

    def setup_collections(self):
        for name in self.COLLECTIONS:
            existing = [c.name for c in self.client.get_collections().collections]
            if name not in existing:
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(size=self.VECTOR_SIZE, distance=Distance.COSINE))
                print(f"[Qdrant] Created collection: {name}")

    def store_trade_pattern(self, symbol, pattern, outcome, confidence, vector=None):
        vec = vector or [0.1] * self.VECTOR_SIZE
        self.client.upsert(collection_name="trading_expertise", points=[
            PointStruct(id=str(uuid.uuid4()), vector=vec, payload={
                "symbol": symbol, "pattern": pattern,
                "outcome": outcome, "confidence": confidence,
                "recorded_at": datetime.utcnow().isoformat()})])

    def search_similar(self, collection, vector, limit=5, filters=None):
        results = self.client.search(
            collection_name=collection, query_vector=vector,
            limit=limit, query_filter=filters)
        return [{"score": r.score, "payload": r.payload} for r in results]