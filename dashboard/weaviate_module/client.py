# filepath: dashboard/weaviate_module/client.py
import weaviate
from weaviate.classes.config import Configure,Property,DataType,Tokenization

client = weaviate.connect_to_local()

client.is_ready()

def get_collection(client=client):
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

