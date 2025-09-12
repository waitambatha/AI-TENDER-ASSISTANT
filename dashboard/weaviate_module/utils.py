# filepath: dashboard/weaviate_module/utils.py
from .client import client
from .client import get_collection
from datetime import datetime
import hashlib
from weaviate.classes.query import Filter
import os
import json
from django.conf import settings
from ollama import chat,ChatResponse

def send_to_weaviate(document_name,text_content) -> tuple[bool,str]:
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

def get_related_text(query):
    documents = get_collection()  
    response = documents.query.near_text(
        query=query,
        limit=2
    )
    return response
    