import os
from typing import Union
from urllib.parse import urlparse

from langchain_community.document_loaders.excel import UnstructuredExcelLoader
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.document_loaders.tsv import UnstructuredTSVLoader
from langchain_community.document_loaders.text import TextLoader
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_community.document_loaders.base import BaseLoader
from langchain_community.document_loaders import JSONLoader
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_core.documents import Document
from langchain_text_splitters import Language
from langchain.text_splitter import RecursiveCharacterTextSplitter


class DynamicLoader:
    def __init__(self, input_source: Union[str], metadata : dict = {}):
        self.input_source = input_source
        self.metadata = metadata
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        
    def load(self) -> list[Document]:
        ext = os.path.splitext(self.input_source)[1].lower()
        loader_func : BaseLoader = self._get_loader_by_extension(ext)()        
        docs : list[Document] = loader_func.load_and_split(self.splitter)
        final_docs : list[Document] = []

        for doc in docs:
            doc.metadata.update(self.metadata)
            final_docs.append(doc)
        return final_docs

    def _get_loader_by_extension(self, ext: str):
        loaders = {
            # Plain Text Files
            '.txt': lambda: TextLoader(file_path=self.input_source),
            '.log': lambda: TextLoader(file_path=self.input_source),
            '.ini': lambda: TextLoader(file_path=self.input_source),
            '.conf': lambda: TextLoader(file_path=self.input_source),
            '.cfg': lambda: TextLoader(file_path=self.input_source),

            # Structured Data
            '.csv': lambda: CSVLoader(file_path=self.input_source),
            '.tsv': lambda: UnstructuredTSVLoader(file_path=self.input_source),
            '.json': lambda: JSONLoader(file_path=self.input_source),
            '.pdf': lambda: PyPDFLoader(file_path=self.input_source),
            '.md': lambda: UnstructuredMarkdownLoader(file_path=self.input_source),
            '.xlsx': lambda: UnstructuredExcelLoader(file_path=self.input_source),
            '.xls': lambda: UnstructuredExcelLoader(file_path=self.input_source),

            # Programming Languages
            '.py': lambda: self._load_from_code(Language.PYTHON),
            '.java': lambda: self._load_from_code(Language.JAVA),
            '.cpp': lambda: self._load_from_code(Language.CPP),
            '.c': lambda: self._load_from_code(Language.C),
            '.cs': lambda: self._load_from_code(Language.CSHARP),
            '.go': lambda: self._load_from_code(Language.GO),
            '.rb': lambda: self._load_from_code(Language.RUBY),
            '.rs': lambda: self._load_from_code(Language.RUST),
            '.kt': lambda: self._load_from_code(Language.KOTLIN),
            '.scala': lambda: self._load_from_code(Language.SCALA),
            '.lua': lambda: self._load_from_code(Language.LUA),
            '.ex': lambda: self._load_from_code(Language.ELIXIR),
            '.pl': lambda: self._load_from_code(Language.PERL),
            '.cob': lambda: self._load_from_code(Language.COBOL),
        }

        return loaders.get(ext, 'txt')

    def _load_from_code(self, language: Language):
        loader = GenericLoader.from_filesystem(
            path=self.input_source,
            parser=LanguageParser(language=language),
        )
        return loader
