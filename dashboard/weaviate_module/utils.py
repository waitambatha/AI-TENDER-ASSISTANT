# filepath: dashboard/weaviate_module/utils.py
from .client import client
from .client import get_collection
from datetime import datetime
import hashlib
from weaviate.classes.query import Filter

def send_to_weaviate(document_name,text_content):
    documents = get_collection()

    content_hash = hashlib.sha256(text_content.encode('utf-8')).hexdigest()
    existing = documents.query.fetch_objects(
        filters=Filter.by_property("content_hash").equal(content_hash),
        limit=1
    )
    
    if existing and getattr(existing, "objects", None) and len(existing.objects) > 0:
        return False 
    
    document = documents.data.insert({
        "file_name":document_name,
        "time_created": datetime.now(),
        "text_content":text_content,
        "content_hash":content_hash
    }) 
    
    return True

def get_related_text(query):
    documents = get_collection()  
    response = documents.query.near_text(
        query=query,
        limit=2
    )
    return response
    