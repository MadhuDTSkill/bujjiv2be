from langchain_community.document_loaders.excel import UnstructuredExcelLoader
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.document_loaders.tsv import UnstructuredTSVLoader
from langchain_community.document_loaders.text import TextLoader
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_community.document_loaders.image import UnstructuredImageLoader
from langchain_community.document_loaders import JSONLoader
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_text_splitters import Language
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_community.document_loaders import UnstructuredURLLoader


# loader = UnstructuredURLLoader(file_path="test.md")

# data = loader.load()

# print(data)

loader = UnstructuredURLLoader(urls=['https://python.langchain.com/docs/integrations/document_loaders/url/'])
data = loader.load()

print(data)

# loader = GenericLoader.from_filesystem(
#     "test.py",
#     parser=LanguageParser(),
# )
# docs = loader.load()

# print(docs)