# filepath: dashboard/weaviate_module/client.py
import weaviate
from weaviate.classes.config import Configure,Property,DataType,Tokenization
import logging

logger = logging.getLogger(__name__)

try:
    client = weaviate.connect_to_local()
    client.is_ready()
except Exception as e:
    logger.warning(f"Weaviate connection failed: {e}")
    client = None

def get_collection(client=client):
    if not client:
        logger.warning("Weaviate client not available")
        return None
        
    try:
        if not client.collections.exists("Documents"):
            documents = client.collections.create(
                name="Documents",
                vector_config=Configure.Vectors.text2vec_transformers(
                    vector_index_config=Configure.VectorIndex.hnsw(),
                    source_properties=[
                        "text_content"
                    ]
                ),
                generative_config=Configure.Generative.ollama(model="llama3.1"),
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
       
                ]
            )
            return documents
        
        else:
            documents = client.collections.get("Documents")
            return documents
    except Exception as e:
        logger.error(f"Error getting collection: {e}")
        return None
