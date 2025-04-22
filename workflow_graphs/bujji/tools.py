import re
from typing import Annotated
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.document_loaders import UnstructuredURLLoader
from duckduckgo_search.exceptions import RatelimitException
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import WikipediaQueryRun

api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=2000)
wiki = WikipediaQueryRun(api_wrapper=api_wrapper)

@tool("DuckDuckGo")
def duckduckgo_search_tool(query: Annotated[str, "The search term to find information from DuckDuckGo."], **kwargs) -> str:
    """
    Searches the web using DuckDuckGo and returns the results.

    Returns:
        str: The search results obtained from DuckDuckGo or a rate limiting error message.
    """
    try:
        search = DuckDuckGoSearchRun(name="Search")
        return search.run(query)
    except RatelimitException:
        return "Failed to get context from the web due to rate limiting."


@tool("Web URL")
def web_url_tool(url: Annotated[str, "A single URL to retrieve content from."], **kwargs) -> str:
    """
    Web Scrap the content from the given URL.

    Returns:
        str: A string summarizing the content retrieved from the URL.
    """
    if not url:
        return "No URL provided."

    loader: UnstructuredURLLoader = UnstructuredURLLoader(urls=[url])  
    docs: list = loader.load()  
    content: str = ""  

    for doc in docs:
        content += f"Content: {doc.page_content.strip()}\n\n"  
    return content  


@tool("Calculator")
def calculator_tool(expression: Annotated[str, "A string containing a mathematical expression"], **kwargs) -> float:
    """
    Evaluates a basic arithmetic expression and returns the result.
        
    Returns:
        float: The result of the evaluated expression or an error message if invalid.
    """
    
    valid_pattern = r'^[\d\s+\-*/().]+$'
    
    
    if not re.match(valid_pattern, expression):
        return "Error: Invalid expression. Only numbers and +, -, *, / operators are allowed."
    
    try:
        # Evaluate the expression
        result = eval(expression)
        return result
    except Exception as e:
        return f"Error: {str(e)}"


@tool("Wikipedia")
def wikipedia_search_tool(query: Annotated[str, "Search query for Wikipedia"], **kwargs) -> str:
    """
    Searches Wikipedia and returns the result.
    """
    return wiki.invoke(input=query)
    