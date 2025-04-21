from langchain.text_splitter import RecursiveCharacterTextSplitter


class DynamicSplitter:
    def __init__(self, text: str):
        self.text = text