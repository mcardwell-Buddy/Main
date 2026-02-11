"""
Mployer Tools - Expose Mployer automation as callable agent tools
"""

import os
import logging
import time
from typing import Dict, List, Optional
from Back_End.mployer_scraper import MployerScraper
from Back_End.screenshot_capture import capture_full_context

logger = logging.getLogger(__name__)

# Global Mployer scraper instance
_mployer_scraper: Optional[MployerScraper] = None


def initialize_mployer():
    """Initialize the global Mployer scraper with credentials"""
    global _mployer_scraper
    
    if _mployer_scraper is not None:
        return True
    
    try:
        # Get credentials from environment
        username = os.getenv('MPLOYER_USERNAME')
        password = os.getenv('MPLOYER_PASSWORD')
        
        if not username or not password:
            logger.warning("Mployer credentials not found in environment")
            return False
        
        _mployer_scraper = MployerScraper(
            mployer_username=username,
            mployer_password=password,
            headless=False  # Visible for debugging
        )
        logger.info("✓ Mployer scraper initialized")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Mployer: {e}")
        return False


def mployer_login() -> Dict:
    """
    Log into Mployer account and capture screenshot.
    
    Returns:
        {
            'success': True/False,
            'message': str,
            'screenshot': base64 screenshot data if successful
        }
    """
    global _mployer_scraper
    
    if not initialize_mployer():
        return {'success': False, 'message': 'Mployer credentials not configured'}
    
    try:
        _mployer_scraper.initialize_browser()
        success = _mployer_scraper.login_to_mployer()
        
        if success:
            # Wait for page to settle and capture
            time.sleep(1)
            context = capture_full_context(_mployer_scraper.driver)
            
            return {
                'success': True,
                'message': 'Successfully logged into Mployer',
                'screenshot': context['screenshot'],
                'page_state': context['page_state'],
                'clickables': context['clickables']
            }
        else:
            return {'success': False, 'message': 'Failed to log into Mployer - check credentials'}
    except Exception as e:
        logger.error(f"mployer_login error: {e}")
        return {'success': False, 'message': f'Login error: {str(e)}'}


def mployer_search_employers(
    state: Optional[str] = None,
    min_employees: Optional[int] = None,
    max_employees: Optional[int] = None,
    industry: Optional[str] = None,
    max_results: int = 50
) -> Dict:
    """
    Search for employers on Mployer with filters.
    
    Args:
        state: State code (e.g., 'MD' for Maryland)
        min_employees: Minimum company size
        max_employees: Maximum company size
        industry: Industry filter
        max_results: Maximum number of results to return
    
    Returns:
        {
            'success': True/False,
            'employers': [list of employer dicts],
            'count': int,
            'message': str
        }
    """
    global _mployer_scraper
    
    if _mployer_scraper is None:
        return {'success': False, 'message': 'Not logged in. Call mployer_login first.'}
    
    try:
        # Build search parameters
        params = {}
        if state:
            params['state'] = state
        if min_employees is not None:
            params['min_employees'] = min_employees
        if max_employees is not None:
            params['max_employees'] = max_employees
        if industry:
            params['industry'] = industry
        
        logger.info(f"Searching Mployer with params: {params}")
        
        # Execute search
        employers = _mployer_scraper.search_employers(
            state=state,
            min_employees=min_employees,
            max_employees=max_employees,
            industry=industry,
            max_results=max_results
        )
        
        # Capture screenshot of results
        time.sleep(0.5)
        context = capture_full_context(_mployer_scraper.driver)
        
        return {
            'success': True,
            'employers': employers,
            'count': len(employers),
            'message': f'Found {len(employers)} employers matching criteria',
            'screenshot': context['screenshot'],
            'page_state': context['page_state'],
            'clickables': context['clickables']
        }
    except Exception as e:
        logger.error(f"mployer_search_employers error: {e}")
        return {'success': False, 'message': f'Search error: {str(e)}', 'employers': []}


def mployer_extract_contacts(employer_name: str, max_contacts: int = 10) -> Dict:
    """
    Extract contacts from a specific employer on Mployer.
    
    Args:
        employer_name: Name of the employer
        max_contacts: Maximum number of contacts to extract
    
    Returns:
        {
            'success': True/False,
            'contacts': [list of contact dicts with name, title, email, phone],
            'count': int,
            'message': str
        }
    """
    global _mployer_scraper
    
    if _mployer_scraper is None:
        return {'success': False, 'message': 'Not logged in. Call mployer_login first.'}
    
    try:
        contacts = _mployer_scraper.extract_contacts(
            employer_name=employer_name,
            max_contacts=max_contacts
        )
        
        # Capture screenshot of contacts
        time.sleep(0.5)
        context = capture_full_context(_mployer_scraper.driver)
        
        return {
            'success': True,
            'contacts': contacts,
            'count': len(contacts),
            'message': f'Extracted {len(contacts)} contacts from {employer_name}',
            'screenshot': context['screenshot'],
            'page_state': context['page_state'],
            'clickables': context['clickables']
        }
    except Exception as e:
        logger.error(f"mployer_extract_contacts error: {e}")
        return {'success': False, 'message': f'Contact extraction error: {str(e)}', 'contacts': []}


def mployer_navigate_to_search() -> Dict:
    """
    Navigate to the employer search page on Mployer.
    
    Returns:
        {'success': True/False, 'message': str, 'url': str}
    """
    global _mployer_scraper
    
    if _mployer_scraper is None:
        return {'success': False, 'message': 'Not logged in. Call mployer_login first.'}
    
    try:
        search_url = "https://portal.mployeradvisor.com/catalyst/employer"
        _mployer_scraper.driver.get(search_url)
        
        import time
        time.sleep(2)
        
        current_url = _mployer_scraper.driver.current_url
        return {
            'success': True,
            'message': 'Navigated to employer search page',
            'url': current_url
        }
    except Exception as e:
        logger.error(f"mployer_navigate_to_search error: {e}")
        return {'success': False, 'message': f'Navigation error: {str(e)}'}


def mployer_close() -> Dict:
    """
    Close the Mployer browser session.
    
    Returns:
        {'success': True/False, 'message': str}
    """
    global _mployer_scraper
    
    if _mployer_scraper is None:
        return {'success': True, 'message': 'No active session'}
    
    try:
        if _mployer_scraper.driver:
            _mployer_scraper.driver.quit()
        _mployer_scraper = None
        return {'success': True, 'message': 'Closed Mployer session'}
    except Exception as e:
        logger.error(f"mployer_close error: {e}")
        return {'success': False, 'message': f'Error closing session: {str(e)}'}


def register_mployer_tools(tool_registry):
    """Register all Mployer tools with the tool registry"""
    
    tool_registry.register(
        'mployer_login',
        mployer_login,
        description='Log into Mployer account. Must be called before any other Mployer operations.'
    )
    
    tool_registry.register(
        'mployer_navigate_to_search',
        mployer_navigate_to_search,
        description='Navigate to the employer search page on Mployer. Call after login.'
    )
    
    tool_registry.register(
        'mployer_search_employers',
        mployer_search_employers,
        description='Search for employers on Mployer. Parameters: state (e.g., "MD"), min_employees, max_employees, industry, max_results.'
    )
    
    tool_registry.register(
        'mployer_extract_contacts',
        mployer_extract_contacts,
        description='Extract contact details from a specific employer on Mployer. Parameters: employer_name, max_contacts.'
    )
    
    tool_registry.register(
        'mployer_close',
        mployer_close,
        description='Close the Mployer browser session and clean up resources.'
    )
    
    logger.info("✓ Registered 5 Mployer tools")

