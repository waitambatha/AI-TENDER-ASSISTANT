# filepath: dashboard/weaviate_module/utils.py
from .client import get_weaviate_client, get_collection
from datetime import datetime
import hashlib
import os
import json
from django.conf import settings
from ollama import chat,ChatResponse
import logging
from weaviate.classes.query import Filter

logger = logging.getLogger(__name__)

    
def send_to_weaviate(document_name,text_content) -> tuple[bool,str]:
    try:
        documents = get_collection()
        
        content_hash = hashlib.sha256(text_content.encode('utf-8')).hexdigest()
        existing = documents.query.fetch_objects(
            filters=Filter.by_property("content_hash").equal(content_hash),
            limit=1
        )
        
        if existing and getattr(existing, "objects", None) and len(existing.objects) > 0:
            return False,""
        
        response: ChatResponse = chat(model='dolphin-phi', messages=[
            {
                'role':'system',
                'content':'You are an assistant capable of analysing tender documents. You role is to: Extract tender information, Identifies key dates and deadlines, Lists requirements and eligibility and Provides opportunity assessment.'
            },
            {
                'role': 'user',
                'content': f'Summarize this content: {text_content}',
            },
        ])    
        summary_filename = f"{document_name}_ai_summarized.json"
        summary_path = os.path.join(settings.MEDIA_ROOT, 'summaries', summary_filename)
        
        # Ensure summaries directory exists
        os.makedirs(os.path.dirname(document_name), exist_ok=True)
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(response.message.content, f, indent=2, ensure_ascii=False)
        
        document = documents.data.insert({
            "file_name":document_name,
            "time_created": datetime.now(),
            "text_content":text_content,
            "content_hash":content_hash,
            "summary":response.message.content
        }) 
        
        return True,summary_filename
    except Exception as e:
        logger.warning(f"Error obtained while getting collection: {str(e)}")
        return False,str(e)

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
    