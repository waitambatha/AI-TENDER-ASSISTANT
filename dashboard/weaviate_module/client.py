# filepath: dashboard/weaviate_module/client.py
import weaviate
import logging

logger = logging.getLogger(__name__)

# Initialize client as None
client = None

def get_weaviate_client():
    global client
    if client is None:
        try:
            # Use v3 client syntax with timeout
            client = weaviate.Client("http://localhost:8081", startup_period=30)
            logger.info("Connected to Weaviate successfully")
        except Exception as e:
            logger.warning(f"Could not connect to Weaviate: {e}")
            client = None
    return client

def get_collection(client=None):
    if client is None:
        client = get_weaviate_client()
    
    if client is None:
        logger.warning("Weaviate client not available")
        return None
        
    try:
        # Check if schema exists, create if not
        schema = client.schema.get()
        class_exists = any(cls['class'] == 'TenderDocument' for cls in schema.get('classes', []))
        
        if not class_exists:
            class_obj = {
                "class": "TenderDocument",
                "properties": [
                    {
                        "name": "file_name",
                        "dataType": ["text"],
                        "indexFilterable": True,
                        "indexSearchable": True
                    },
                    {
                        "name": "time_created",
                        "dataType": ["date"]
                    },
                    {
                        "name": "text_content",
                        "dataType": ["text"]
                    },
                    {
                        "name": "content_hash",
                        "dataType": ["text"],
                        "indexFilterable": True,
                        "indexSearchable": True
                    },
                    {
                        "name": "summary",
                        "dataType": ["text"]
                    }
                ]
            }
            client.schema.create_class(class_obj)
            logger.info("Created TenderDocument class")
        
        return client
    except Exception as e:
        logger.error(f"Error accessing Weaviate collection: {e}")
        return None

