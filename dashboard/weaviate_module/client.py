# filepath: dashboard/weaviate_module/client.py
import weaviate
import logging
from weaviate.classes.config import Configure,Property,DataType,Tokenization

logger = logging.getLogger(__name__)

# Initialize client as None
client = None

def get_weaviate_client():
    global client
    if client is None:
        try:
            client = weaviate.connect_to_local() or weaviate.connect_to_local(port=8081)
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
        if not client.collections.exists("TenderDocument"):
            documents = client.collections.create(
                name="TenderDocument",
                vector_config=Configure.Vectors.text2vec_transformers(
                    vector_index_config=Configure.VectorIndex.hnsw(),
                    source_properties=[
                        "text_content",
                        "summary"
                    ]
                ),
                properties=[
                    Property(
                        name="file_name",
                        index_filterable=True,
                        index_searchable=True,
                        data_type=DataType.TEXT
                    ),
                    Property(
                        name="time_created",
                        data_type=DataType.DATE,
                    ),
                    Property(
                        name="text_content",
                        data_type=DataType.TEXT
                    ),
                    Property(
                        name="content_hash",
                        index_filterable=True,
                        index_searchable=True,
                        data_type=DataType.TEXT
                    ),
                    Property(
                        name="summary",
                        data_type=DataType.TEXT
                    )
    
                ]
            )
            return documents
        
        else:
            documents = client.collections.get("TenderDocument")
            
            return documents
    except Exception as e:
        logger.warning(f"Error obtained while getting collection: {str(e)}")