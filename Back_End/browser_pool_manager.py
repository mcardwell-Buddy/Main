"""
Browser Pool Manager for Buddy Local Agent
Phase 3: Dynamic WebDriver pool management

Manages:
- Creation and destruction of browser instances
- Health monitoring and auto-restart
- Dynamic scaling based on resources
- Browser session caching
- Connection pooling
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading
import uuid

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchWindowException
)

from resource_monitor import ResourceMonitor

# Setup logging
logger = logging.getLogger('BrowserPoolManager')


class BrowserInstance:
    """Represents a single browser instance."""
    
    def __init__(self, browser_id: str, driver: webdriver.Chrome):
        self.browser_id = browser_id
        self.driver = driver
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.last_health_check = datetime.now()
        self.health_check_count = 0
        self.failed_health_checks = 0
        self.pages_loaded = 0
        self.is_healthy = True
        self.task_count = 0
        self.session_data = {}
    
    def update_last_used(self):
        """Update last used timestamp."""
        self.last_used = datetime.now()
    
    def get_uptime(self) -> float:
        """Get browser uptime in seconds."""
        return (datetime.now() - self.created_at).total_seconds()
    
    def get_idle_time(self) -> float:
        """Get idle time in seconds."""
        return (datetime.now() - self.last_used).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for logging."""
        return {
            'browser_id': self.browser_id,
            'created_at': self.created_at.isoformat(),
            'uptime_seconds': self.get_uptime(),
            'idle_seconds': self.get_idle_time(),
            'health_checks': self.health_check_count,
            'failed_checks': self.failed_health_checks,
            'pages_loaded': self.pages_loaded,
            'tasks_completed': self.task_count,
            'is_healthy': self.is_healthy
        }


class BrowserPoolManager:
    """Manages a pool of Selenium WebDriver browsers."""
    
    def __init__(self, resource_monitor: ResourceMonitor):
        """
        Initialize browser pool manager.
        
        Args:
            resource_monitor: ResourceMonitor instance for resource limits
        """
        self.resource_monitor = resource_monitor
        self.browsers: Dict[str, BrowserInstance] = {}
        self.lock = threading.Lock()
        self.running = False
        
        # Configuration
        self.health_check_interval = 30  # seconds
        self.max_browser_age = 3600  # 1 hour before restart
        self.max_failed_health_checks = 3
        self.browser_startup_timeout = 10  # seconds
        self.health_check_timeout = 5  # seconds
        self.idle_timeout = 300  # 5 minutes
        
        # Scaling
        self.target_browser_count = 5
        self.scale_check_interval = 30  # seconds
        self.next_scale_check = datetime.now()
        
        # Stats
        self.total_browsers_created = 0
        self.total_browsers_destroyed = 0
        self.total_health_checks = 0
        self.total_failed_checks = 0
        self.start_time = None
        
        logger.info("BrowserPoolManager initialized")
        logger.info(f"  Health check interval: {self.health_check_interval}s")
        logger.info(f"  Max browser age: {self.max_browser_age}s")
        logger.info(f"  Browser startup timeout: {self.browser_startup_timeout}s")
    
    def start(self):
        """Start browser pool manager."""
        if self.running:
            logger.warning("Browser pool already running")
            return
        
        self.running = True
        self.start_time = datetime.now()
        
        logger.info("🚀 Browser pool starting...")
        logger.info(f"Target browser count: {self.target_browser_count}")
    
    def stop(self):
        """Stop browser pool and destroy all browsers."""
        logger.info("🛑 Stopping browser pool...")
        
        with self.lock:
            # Close all browsers
            for browser_id in list(self.browsers.keys()):
                self._destroy_browser(browser_id)
        
        self.running = False
        
        # Log stats
        uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
        logger.info(f"Browser pool stopped:")
        logger.info(f"  Uptime: {uptime}")
        logger.info(f"  Browsers created: {self.total_browsers_created}")
        logger.info(f"  Browsers destroyed: {self.total_browsers_destroyed}")
        logger.info(f"  Health checks: {self.total_health_checks}")
        logger.info(f"  Failed checks: {self.total_failed_checks}")
    
    def update(self):
        """
        Update browser pool.
        Call this periodically from main loop.
        """
        if not self.running:
            return
        
        try:
            # Perform health checks
            self._check_browser_health()
            
            # Auto-scale based on resources
            if datetime.now() >= self.next_scale_check:
                self._auto_scale()
                self.next_scale_check = datetime.now() + timedelta(seconds=self.scale_check_interval)
            
            # Clean up idle browsers
            self._cleanup_idle_browsers()
        
        except Exception as e:
            logger.error(f"Error updating browser pool: {e}", exc_info=True)
    
    def get_available_browser(self) -> Optional[BrowserInstance]:
        """
        Get an available browser from the pool.
        
        Returns:
            BrowserInstance or None if no browsers available
        """
        if not self.running:
            return None
        
        with self.lock:
            # Find healthy, idle browser
            for browser in self.browsers.values():
                if browser.is_healthy and browser.get_idle_time() < 1:
                    browser.update_last_used()
                    browser.task_count += 1
                    logger.debug(f"Assigned browser {browser.browser_id}")
                    return browser
            
            # No available browsers
            logger.warning("No available browsers in pool")
            return None
    
    def get_browser_count(self) -> Dict[str, int]:
        """Get current browser counts."""
        with self.lock:
            healthy = sum(1 for b in self.browsers.values() if b.is_healthy)
            unhealthy = len(self.browsers) - healthy
            
            return {
                'total': len(self.browsers),
                'healthy': healthy,
                'unhealthy': unhealthy
            }
    
    def _create_browser(self) -> Optional[BrowserInstance]:
        """Create a new browser instance."""
        try:
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-notifications")
            
            # Create driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(
                service=service,
                options=chrome_options
            )
            
            # Set timeouts
            driver.set_page_load_timeout(self.browser_startup_timeout)
            
            # Create browser instance
            browser_id = f"browser-{str(uuid.uuid4())[:8]}"
            browser = BrowserInstance(browser_id, driver)
            
            self.browsers[browser_id] = browser
            self.total_browsers_created += 1
            
            logger.info(f"✅ Browser created: {browser_id}")
            return browser
        
        except Exception as e:
            logger.error(f"Failed to create browser: {e}")
            return None
    
    def _destroy_browser(self, browser_id: str):
        """Destroy a browser instance."""
        try:
            if browser_id not in self.browsers:
                return
            
            browser = self.browsers[browser_id]
            
            try:
                browser.driver.quit()
            except Exception as e:
                logger.warning(f"Error quitting driver: {e}")
            
            del self.browsers[browser_id]
            self.total_browsers_destroyed += 1
            
            logger.info(f"🗑️ Browser destroyed: {browser_id}")
        
        except Exception as e:
            logger.error(f"Error destroying browser {browser_id}: {e}")
    
    def _check_browser_health(self):
        """Check health of all browsers."""
        with self.lock:
            current_time = datetime.now()
            
            for browser_id, browser in list(self.browsers.items()):
                # Check if health check interval has passed
                if (current_time - browser.last_health_check).total_seconds() < self.health_check_interval:
                    continue
                
                try:
                    # Try to get window handles (quick health check)
                    _ = browser.driver.window_handles
                    
                    browser.is_healthy = True
                    browser.failed_health_checks = 0
                    browser.health_check_count += 1
                    browser.last_health_check = current_time
                    
                    logger.debug(f"✅ Health check passed: {browser_id}")
                
                except (WebDriverException, NoSuchWindowException) as e:
                    browser.failed_health_checks += 1
                    logger.warning(f"❌ Health check failed for {browser_id}: {e}")
                    
                    # Mark unhealthy after too many failures
                    if browser.failed_health_checks >= self.max_failed_health_checks:
                        browser.is_healthy = False
                        logger.error(f"🔴 Browser marked unhealthy: {browser_id}")
                        self._destroy_browser(browser_id)
                    
                    self.total_failed_checks += 1
            
            self.total_health_checks += 1
    
    def _auto_scale(self):
        """Auto-scale browser pool based on resources."""
        try:
            # Get safe browser count from resource monitor
            safe_count = self.resource_monitor.get_safe_browser_count('comfortable')
            resource_status = self.resource_monitor.get_system_status()
            
            current_count = len(self.browsers)
            
            # Adjust target based on resource mode
            if resource_status['mode'] == 'optimal':
                self.target_browser_count = min(safe_count, 10)
            elif resource_status['mode'] == 'throttled':
                self.target_browser_count = min(safe_count // 2, 5)
            elif resource_status['mode'] == 'paused':
                self.target_browser_count = 1
            else:  # critical
                self.target_browser_count = 0
            
            # Scale up if needed
            while current_count < self.target_browser_count:
                if self._create_browser():
                    current_count += 1
                else:
                    break
            
            # Scale down if needed
            excess = current_count - self.target_browser_count
            if excess > 0 and current_count > 1:
                # Destroy excess browsers (prefer older ones)
                to_destroy = sorted(
                    self.browsers.items(),
                    key=lambda x: x[1].created_at
                )[:excess]
                
                for browser_id, _ in to_destroy:
                    self._destroy_browser(browser_id)
            
            logger.info(f"Auto-scale: {current_count} → {len(self.browsers)} browsers")
            logger.info(f"  Resource mode: {resource_status['mode']}")
            logger.info(f"  RAM: {resource_status['ram_percent']:.1f}%")
            logger.info(f"  Safe count: {safe_count}")
        
        except Exception as e:
            logger.error(f"Error auto-scaling: {e}")
    
    def _cleanup_idle_browsers(self):
        """Clean up idle browsers."""
        try:
            with self.lock:
                current_time = datetime.now()
                
                for browser_id, browser in list(self.browsers.items()):
                    # Check age
                    if browser.get_uptime() > self.max_browser_age:
                        logger.info(f"Restarting old browser: {browser_id} (age: {browser.get_uptime():.0f}s)")
                        self._destroy_browser(browser_id)
        
        except Exception as e:
            logger.error(f"Error cleaning up idle browsers: {e}")
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get current pool status."""
        with self.lock:
            counts = self.get_browser_count()
            
            return {
                'running': self.running,
                'total_browsers': counts['total'],
                'healthy_browsers': counts['healthy'],
                'unhealthy_browsers': counts['unhealthy'],
                'target_count': self.target_browser_count,
                'total_created': self.total_browsers_created,
                'total_destroyed': self.total_browsers_destroyed,
                'health_checks': self.total_health_checks,
                'failed_checks': self.total_failed_checks,
                'uptime': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            }
    
    def get_browsers_info(self) -> List[Dict[str, Any]]:
        """Get info about all browsers."""
        with self.lock:
            return [browser.to_dict() for browser in self.browsers.values()]
    
    def navigate_to_url(self, url: str, timeout: int = 10) -> bool:
        """
        Navigate an available browser to URL.
        
        Args:
            url: URL to navigate to
            timeout: Navigation timeout in seconds
        
        Returns:
            True if successful, False otherwise
        """
        browser = self.get_available_browser()
        if not browser:
            logger.warning("No available browser for navigation")
            return False
        
        try:
            browser.driver.set_page_load_timeout(timeout)
            browser.driver.get(url)
            browser.pages_loaded += 1
            logger.debug(f"Navigated to {url}")
            return True
        
        except TimeoutException:
            logger.error(f"Timeout navigating to {url}")
            browser.failed_health_checks += 1
            return False
        
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return False
    
    def get_page_source(self, browser_instance: Optional[BrowserInstance] = None) -> Optional[str]:
        """Get page source from a browser."""
        if browser_instance is None:
            browser_instance = self.get_available_browser()
        
        if not browser_instance:
            return None
        
        try:
            return browser_instance.driver.page_source
        except Exception as e:
            logger.error(f"Error getting page source: {e}")
            return None
    
    def screenshot(self, filename: str, browser_instance: Optional[BrowserInstance] = None) -> bool:
        """Take screenshot from browser."""
        if browser_instance is None:
            browser_instance = self.get_available_browser()
        
        if not browser_instance:
            return False
        
        try:
            browser_instance.driver.save_screenshot(filename)
            logger.debug(f"Screenshot saved: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return False
