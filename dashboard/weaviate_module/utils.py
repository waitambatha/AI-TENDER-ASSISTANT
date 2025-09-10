# filepath: dashboard/weaviate_module/utils.py
from .client import client
from .client import get_collection
from datetime import datetime
import hashlib
import logging

logger = logging.getLogger(__name__)

try:
    from weaviate.classes.query import Filter
except ImportError:
    Filter = None

def send_to_weaviate(document_name, text_content):
    try:
        documents = get_collection()
        if not documents:
            logger.warning("Weaviate collection not available, skipping duplicate check")
            return True  # Allow processing if Weaviate is not available

        content_hash = hashlib.sha256(text_content.encode('utf-8')).hexdigest()
        
        if Filter:
            existing = documents.query.fetch_objects(
                filters=Filter.by_property("content_hash").equal(content_hash),
                limit=1
            )
            
            if existing and getattr(existing, "objects", None) and len(existing.objects) > 0:
                return False 
        
        document = documents.data.insert({
            "file_name": document_name,
            "time_created": datetime.now(),
            "text_content": text_content,
            "content_hash": content_hash
        }) 
        
        return True
    except Exception as e:
        logger.error(f"Error in send_to_weaviate: {e}")
        return True  # Allow processing if there's an error

def get_related_text(query):
    try:
        documents = get_collection()
        if not documents:
            return None
            
        response = documents.query.near_text(
            query=query,
            limit=2
        )
        return response
    except Exception as e:
        logger.error(f"Error in get_related_text: {e}")
        return None