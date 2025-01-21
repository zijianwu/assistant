import requests
import os


def url_to_markdown(url: str) -> str:
    """Convert a URL to markdown content using Jina Reader service.

    Args:
        url (str): The URL to convert to markdown

    Returns:
        str: The markdown content as text data
    """
    # TODO: Replace with langchain AsyncHtmlLoader
    # and markdownify for better reliability
    JINA_READER = 'https://r.jina.ai/'
    url = JINA_READER + url
    headers = {
        'Authorization': os.environ.get('JINAAI_READER_API_KEY'),
        'X-Retain-Images': 'none',
        'X-With-Iframe': 'true',
    }

    response = requests.get(url, headers=headers)

    return response.text
