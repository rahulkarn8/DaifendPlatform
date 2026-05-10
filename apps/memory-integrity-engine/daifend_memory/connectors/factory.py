from __future__ import annotations

import logging
import os

from daifend_memory.connectors.base import VectorConnector
from daifend_memory.connectors.pgvector_connector import connector_from_env as pgvector_from_env
from daifend_memory.connectors.pinecone_connector import connector_from_env as pinecone_from_env
from daifend_memory.connectors.qdrant_connector import QdrantConnector
from daifend_memory.connectors.weaviate_connector import connector_from_env as weaviate_from_env

logger = logging.getLogger(__name__)


def build_connector(backend: str) -> VectorConnector:
    b = backend.lower().strip()
    if b == "qdrant":
        url = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")
        return QdrantConnector(url=url)
    if b == "pgvector":
        c = pgvector_from_env()
        if c is None:
            raise ValueError("PGVECTOR_DSN and PGVECTOR_TABLE required for pgvector backend")
        return c
    if b == "pinecone":
        c = pinecone_from_env()
        if c is None:
            raise ValueError("PINECONE_API_KEY and PINECONE_INDEX required for pinecone backend")
        return c
    if b == "weaviate":
        c = weaviate_from_env()
        if c is None:
            raise ValueError("WEAVIATE_URL and WEAVIATE_CLASS required for weaviate backend")
        return c
    raise ValueError(f"Unknown vector backend: {backend}")
