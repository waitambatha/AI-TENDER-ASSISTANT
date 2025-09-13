# filepath: dashboard/weaviate_module/utils.py
from .client import get_weaviate_client, get_collection
from datetime import datetime
import hashlib
import os
import json
from django.conf import settings
from ollama import chat,ChatResponse
import logging

logger = logging.getLogger(__name__)

def send_to_weaviate(document_name,text_content) -> tuple[bool,str]:
    client = get_collection()
    
    if client is None:
        raise Exception("Weaviate connection failed")

    try:
        content_hash = hashlib.sha256(text_content.encode('utf-8')).hexdigest()
        
        # Check for existing document with same hash
        where_filter = {
            "path": ["content_hash"],
            "operator": "Equal",
            "valueText": content_hash
        }
        
        existing = client.query.get("TenderDocument", ["file_name"]).with_where(where_filter).with_limit(1).do()
        
        if existing.get("data", {}).get("Get", {}).get("TenderDocument"):
            return False, ""
        
        response: ChatResponse = chat(model='dolphin-phi', messages=[
            {
                'role': 'user',
                'content': f'Summarize this content: {text_content}',
            },
        ])
        
        summary_filename = f"{document_name}_ai_summarized.json"
        summary_path = os.path.join(settings.MEDIA_ROOT, 'summaries', summary_filename)
        
        # Ensure summaries directory exists
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(response.message.content, f, indent=2, ensure_ascii=False)
        
        # Insert document into Weaviate
        data_object = {
            "file_name": document_name,
            "time_created": datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            "text_content": text_content,
            "content_hash": content_hash,
            "summary": response.message.content
        }
        
        client.data_object.create(data_object, "TenderDocument")
        
        return True, summary_filename
    except Exception as e:
        logger.error(f"Error in send_to_weaviate: {e}")
        raise Exception(f"Weaviate processing failed: {e}")

def get_related_text(query):
    client = get_collection()
    
    if client is None:
        logger.warning("Weaviate not available, returning empty results")
        return None
        
    try:
        response = client.query.get("TenderDocument", ["file_name", "summary", "text_content"]).with_near_text({"concepts": [query]}).with_limit(2).do()
        return response
    except Exception as e:
        logger.error(f"Error in get_related_text: {e}")
        return None
    