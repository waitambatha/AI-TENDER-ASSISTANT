import weaviate
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

class WeaviateService:
    def __init__(self):
        self.client = None
        self._connect()
    
    def _connect(self):
        try:
            self.client = weaviate.Client("http://localhost:8080")
            self.setup_schema()
        except Exception as e:
            logger.warning(f"Weaviate connection failed: {e}")
            self.client = None
    
    def setup_schema(self):
        if not self.client:
            return
            
        schema = {
            "classes": [{
                "class": "DocumentSummary",
                "properties": [
                    {"name": "content", "dataType": ["text"]},
                    {"name": "document_id", "dataType": ["int"]},
                    {"name": "title", "dataType": ["text"]},
                    {"name": "summary", "dataType": ["text"]},
                ]
            }]
        }
        
        try:
            if not self.client.schema.exists("DocumentSummary"):
                self.client.schema.create(schema)
        except Exception as e:
            logger.error(f"Schema setup error: {e}")
    
    def add_document(self, document_id, title, content, summary):
        if not self.client:
            logger.warning("Weaviate not connected, skipping document addition")
            return
            
        try:
            self.client.data_object.create({
                "content": content,
                "document_id": document_id,
                "title": title,
                "summary": summary
            }, "DocumentSummary")
        except Exception as e:
            logger.error(f"Error adding document: {e}")
    
    def search_documents(self, query, limit=10):
        if not self.client:
            logger.warning("Weaviate not connected, returning empty results")
            return []
            
        try:
            result = (
                self.client.query
                .get("DocumentSummary", ["content", "document_id", "title", "summary"])
                .with_bm25(query=query)
                .with_limit(limit)
                .do()
            )
            return result.get("data", {}).get("Get", {}).get("DocumentSummary", [])
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
