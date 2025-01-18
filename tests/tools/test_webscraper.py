def test_url_to_markdown_basic():
    """Test basic functionality with mocked response"""
    test_url = "example.com"
    expected_markdown = "# Example Content"
    
    with requests_mock.Mocker() as m:
        m.get('https://r.jina.ai/example.com', 
              text=expected_markdown,
              headers={'content-type': 'text/markdown'})
        result = url_to_markdown(test_url)
        assert isinstance(result, str)
        assert result == expected_markdown

def test_url_to_markdown_headers():
    """Test if correct headers are sent"""
    test_url = "example.com"
    
    with requests_mock.Mocker() as m:
        m.get('https://r.jina.ai/example.com', text="content")
        url_to_markdown(test_url)
        
        # Verify headers were sent correctly
        history = m.request_history[0]
        assert history.headers['X-Engine'] == 'readerlm-v2'
        assert history.headers['X-Retain-Images'] == 'none'
        assert history.headers['X-With-Iframe'] == 'true'