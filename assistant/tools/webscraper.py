import requests


def url_to_markdown(url: str) -> str:
    """Convert a URL to markdown content using Jina Reader service.
    
    Args:
        url (str): The URL to convert to markdown
        
    Returns:
        bytes: The markdown content as bytes data
    """
    JINA_READER = 'https://r.jina.ai/'
    url = JINA_READER + url
    headers = {
        'X-Retain-Images': 'none',
        'X-With-Iframe': 'true',
    }

    response = requests.get(url, headers=headers)

    print(response.text)
