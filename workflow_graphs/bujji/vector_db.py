import os
import time
from uuid import uuid4
from pinecone import Pinecone, ServerlessSpec
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.runnables import Runnable
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


model_name = "sentence-transformers/all-mpnet-base-v2"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': False}



class PineconeVectorDB:
    def __init__(self, index_name: str):
        self.client = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
        self.index_name = index_name
        self.index = None
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        existing_indexes = [index_info["name"] for index_info in self.client.list_indexes()]
        
        if index_name not in existing_indexes:
            self.client.create_index(
                name=index_name,
                dimension=768,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            while not self.client.describe_index(index_name).status["ready"]:
                time.sleep(1)
                
        self.index = self.client.Index(index_name)
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs)
        self.store = PineconeVectorStore(index=self.index, embedding=self.embeddings)
        
        
    
    def split_to_documents(self, text) -> list[Document]:
        return self.text_splitter.create_documents([text])
    
    
    def add_documents(self, text: str) -> None:
        documents = self.split_to_documents(text)
        uuids = [str(uuid4()) for _ in range(len(documents))]
        self.store.add_documents(documents=documents, ids=uuids)
        
        
    def query(self, query: str, k: int = 5) -> list[Document]:
        results = self.store.similarity_search(query, k=k)
        response = [result.page_content for result in results]
        return "\n\n".join(response)
    
    
    def as_retriever(self) -> Runnable:
        return self.store.as_retriever(
        search_type="mmr",
        search_kwargs={'k': 5, 'fetch_k': 50},
    )
        