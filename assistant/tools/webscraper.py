import asyncio
from langchain_community.document_loaders import AsyncHtmlLoader
from markdownify import markdownify as md


def url_to_markdown(url: str) -> str:
    """Convert a URL to markdown content using langchain's AsyncHtmlLoader and markdownify.

    Args:
        url (str): The URL to convert to markdown

    Returns:
        str: The markdown content as text data
    """
    # TODO: Replace with Huggingface ReaderLMv2 locally for performance
    # Load HTML content using AsyncHtmlLoader
    loader = AsyncHtmlLoader([url])
    html_docs = asyncio.run(loader.aload())
    
    if not html_docs:
        return ""
        
    # Convert HTML to markdown using markdownify
    html_content = html_docs[0].page_content
    markdown_content = md(html_content)
    
    return markdown_content
