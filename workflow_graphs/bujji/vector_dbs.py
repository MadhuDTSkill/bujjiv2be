import os
import time
import weaviate
from abc import ABC, abstractmethod
from uuid import uuid4
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_weaviate import WeaviateVectorStore
from langchain_community.vectorstores.zilliz import Zilliz
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient, models
from langchain_qdrant import QdrantVectorStore
from langchain_cohere import CohereEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

class BaseVectorDB(ABC):
    @abstractmethod
    def add_documents(self, documents: list[Document]) -> None:
        pass
    
    @abstractmethod
    def query(self, query: str, k: int = 5) -> str:
        ...
        
    @abstractmethod
    def delete_index(self):
        ...
    
    @abstractmethod
    def delete_vectors(self):
        ...



class PineconeVectorDB(BaseVectorDB):
    def __init__(self, index_name: str):
        self.client = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
        self.index_name = index_name
        self.index = None
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        existing_indexes = [index_info["name"] for index_info in self.client.list_indexes()]
        
        if index_name not in existing_indexes:
            self.client.create_index(
                name=index_name,
                dimension=1024,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            while not self.client.describe_index(index_name).status["ready"]:
                time.sleep(1)
                
        self.index = self.client.Index(index_name)
        self.embeddings = CohereEmbeddings(model="embed-english-v3.0")
        self.store : PineconeVectorStore = PineconeVectorStore(index=self.index, embedding=self.embeddings)
        
            
    def add_documents(self, documents : list[Document]) -> None:
        uuids = [str(uuid4()) for _ in range(len(documents))]
        return self.store.add_documents(documents=documents, ids=uuids)
        
        
    def query(self, query: str, k: int = 5) -> list[Document]:
        results = self.store.similarity_search(query, k=k)
        response = [result.page_content for result in results]
        return "\n\n".join(response)
    
    
    def delete_index(self):
        self.client.delete_index(index_name=self.index_name)
        
    def delete_vectors(self, filter: dict = None) -> None:
        self.store.delete(filter=filter)
            
        
class QdrantVectorDB(BaseVectorDB):
    def __init__(self, collection_name: str):
        self.client =  QdrantClient(url=os.environ.get("QDRANT_HOST"), api_key = os.environ.get("QDRANT_API_KEY"))
        self.collection_name = collection_name
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                
        if not self.client.collection_exists(collection_name=self.collection_name):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
                )
                
        self.embeddings = CohereEmbeddings(model="embed-english-v3.0")
        self.store = QdrantVectorStore(client=self.client, collection_name=self.collection_name, embedding=self.embeddings)
        
            
    def add_documents(self, documents : list[Document]) -> None:
        uuids = [str(uuid4()) for _ in range(len(documents))]
        self.store.add_documents(documents=documents, ids=uuids)
        
        
    def query(self, query: str, k: int = 5) -> str:
        results = self.store.similarity_search(query, k=k)
        return "\n\n".join([f"{i+1}. {doc.page_content}" for i, doc in enumerate(results)])
    
    def delete_index(self):
        self.client.delete_collection(collection_name=self.collection_name)
        
    def delete_vectors(self, filter: dict = None) -> None:
        self.store.delete(filter=filter)
      

class WeaviateVectorDB:
    def __init__(self, index_name: str):
        self.client =  weaviate.connect_to_weaviate_cloud(cluster_url=os.environ.get("WEAVIATE_CLUSTER_URL"), auth_credentials=weaviate.auth.AuthApiKey(api_key=os.environ.get("WEAVIATE_API_KEY")), skip_init_checks=True)
        self.index_name = index_name
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                
        self.embeddings = CohereEmbeddings(model="embed-english-v3.0")
        self.store = WeaviateVectorStore(index_name=index_name, client=self.client, embedding=self.embeddings, text_key='content')
            
    
    def add_documents(self, documents : list[Document]) -> None:
        
        uuids = [str(uuid4()) for _ in range(len(documents))]
        self.store.add_documents(documents=documents, ids=uuids)
        
        
    def query(self, query: str, k: int = 5) -> str:
        results = self.store.similarity_search(query, k=k)
        return "\n\n".join([f"{i+1}. {doc.page_content}" for i, doc in enumerate(results)])
    
    
class ZillizVectorDB:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.connection_args = { 'uri': os.environ.get("ZILLIZ_CLOUD_URI"), 'token': os.environ.get("ZILLIZ_CLOUD_API_KEY") }
        
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                
        self.embeddings = CohereEmbeddings(model="embed-english-v3.0")
        self.store = Zilliz(embedding_function=self.embeddings, connection_args=self.connection_args, collection_name = self.collection_name)
    
    def add_documents(self, documents : list[Document]) -> None:
        uuids = [str(uuid4()) for _ in range(len(documents))]
        self.store.add_documents(documents=documents, ids=uuids)
        
        
    def query(self, query: str, k: int = 5) -> str:
        results = self.store.similarity_search(query, k=k)
        return "\n\n".join([f"{i+1}. {doc.page_content}" for i, doc in enumerate(results)])       

