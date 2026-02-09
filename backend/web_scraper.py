"""
Web scraping tool that clicks links and extracts full content.
Enhances the basic web_search that only returns snippets.
"""
import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from backend.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_webpage(url: str, max_length: int = 5000, timeout: int = 10) -> Dict:
    """
    Fetch and extract main content from a webpage.
    
    Args:
        url: The URL to scrape
        max_length: Maximum content length to return (chars)
        timeout: Request timeout in seconds
        
    Returns:
        dict with 'url', 'content', 'summary', 'success', 'error'
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script, style, and nav elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Try to find main content area
        main_content = None
        
        # Priority order for content extraction
        selectors = [
            'article',
            'main',
            '[role="main"]',
            '.content',
            '.post-content',
            '.article-content',
            '#content',
            'body'
        ]
        
        for selector in selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            main_content = soup.body
        
        if not main_content:
            return {
                'url': url,
                'content': None,
                'summary': 'Failed to extract content',
                'success': False,
                'error': 'No content found'
            }
        
        # Extract text
        text = main_content.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        # Truncate to max_length
        truncated = text[:max_length]
        was_truncated = len(text) > max_length
        
        # Generate summary (first 200 chars)
        summary = text[:200] + '...' if len(text) > 200 else text
        
        return {
            'url': url,
            'content': truncated,
            'full_length': len(text),
            'truncated': was_truncated,
            'summary': summary,
            'success': True,
            'error': None
        }
        
    except requests.Timeout:
        return {
            'url': url,
            'content': None,
            'summary': f'Timeout after {timeout}s',
            'success': False,
            'error': 'timeout'
        }
    except requests.RequestException as e:
        return {
            'url': url,
            'content': None,
            'summary': f'Request failed: {str(e)}',
            'success': False,
            'error': str(e)
        }
    except Exception as e:
        logger.error(f"Scraping failed for {url}: {e}")
        return {
            'url': url,
            'content': None,
            'summary': f'Parsing failed: {str(e)}',
            'success': False,
            'error': str(e)
        }


def web_search_deep(query: str, click_top_n: int = 3, max_content_length: int = 5000) -> Dict:
    """
    Enhanced web search that clicks links and reads full content.
    
    Args:
        query: Search query
        click_top_n: Number of top results to scrape (1-5)
        max_content_length: Max chars to extract from each page
        
    Returns:
        dict with 'results' (list), 'query', 'depth', 'sources_read'
    """
    from backend.tools import web_search
    
    # First get search results (snippets)
    search_results = web_search(query)
    
    if not search_results.get('results'):
        return {
            'query': query,
            'results': [],
            'depth': 'deep',
            'sources_read': 0,
            'error': 'No search results'
        }
    
    # Click top N links and extract full content
    detailed_results = []
    sources_read = 0
    
    for i, result in enumerate(search_results['results'][:click_top_n]):
        link = result.get('link')
        if not link:
            # No link, use snippet only
            detailed_results.append({
                'rank': i + 1,
                'title': result.get('title', 'Untitled'),
                'url': None,
                'snippet': result.get('snippet', ''),
                'full_content': None,
                'content_length': 0,
                'depth': 'snippet',
                'confidence': 0.3  # Low confidence - snippet only
            })
            continue
        
        logger.info(f"Scraping #{i+1}: {link}")
        scraped = scrape_webpage(link, max_length=max_content_length)
        
        if scraped['success']:
            sources_read += 1
            detailed_results.append({
                'rank': i + 1,
                'title': result.get('title', 'Untitled'),
                'url': link,
                'snippet': result.get('snippet', ''),
                'full_content': scraped['content'],
                'content_length': scraped.get('full_length', 0),
                'truncated': scraped.get('truncated', False),
                'depth': 'full',
                'confidence': 0.9  # High confidence - full article
            })
        else:
            # Scraping failed, fallback to snippet
            detailed_results.append({
                'rank': i + 1,
                'title': result.get('title', 'Untitled'),
                'url': link,
                'snippet': result.get('snippet', ''),
                'full_content': None,
                'content_length': 0,
                'scrape_error': scraped.get('error'),
                'depth': 'snippet',
                'confidence': 0.3  # Low confidence - snippet only
            })
    
    return {
        'query': query,
        'results': detailed_results,
        'depth': 'deep',
        'sources_read': sources_read,
        'total_results': len(detailed_results)
    }


def register_scraping_tools(tool_registry):
    """Register web scraping tools"""
    tool_registry.register(
        name='scrape_webpage',
        func=scrape_webpage,
        description='Fetch and extract main content from a webpage URL. Returns full article text, not just snippets. Parameters: url (required), max_length (default 5000), timeout (default 10)',
        mock_func=lambda url, **kwargs: {
            'url': url,
            'content': f'[MOCK] Full content from {url}...',
            'summary': f'[MOCK] Article about {url}',
            'success': True,
            'error': None
        }
    )
    
    tool_registry.register(
        name='web_search_deep',
        func=web_search_deep,
        description='Enhanced web search that clicks links and reads full articles (not just snippets). More comprehensive but slower. Parameters: query (required), click_top_n (default 3), max_content_length (default 5000)',
        mock_func=lambda query, **kwargs: {
            'query': query,
            'results': [
                {
                    'rank': 1,
                    'title': f'[MOCK] Article about {query}',
                    'url': f'https://example.com/{query.replace(" ", "-")}',
                    'snippet': f'[MOCK] Summary of {query}...',
                    'full_content': f'[MOCK] Full detailed article about {query} with extensive information...',
                    'content_length': 1500,
                    'depth': 'full',
                    'confidence': 0.9
                }
            ],
            'depth': 'deep',
            'sources_read': 1
        }
    )
    
    logger.info("Registered web scraping tools: scrape_webpage, web_search_deep")
