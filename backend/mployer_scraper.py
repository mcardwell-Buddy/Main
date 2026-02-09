"""
Mployer Automation Scraper

Automatically searches Mployer for contacts matching your criteria
and adds them to GoHighLevel.
"""

import os
import json
import logging
import pickle
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

from backend.gohighlevel_client import ghl_client
from backend.gohighlevel_tools import ghl_add_contact, ghl_search_contact

logger = logging.getLogger(__name__)

COOKIES_FILE = "mployer_cookies.pkl"


class MployerScraper:
    """Automates Mployer searches and contact extraction"""
    
    def __init__(self, mployer_username: str, mployer_password: str, headless: bool = False):
        """
        Initialize Mployer scraper.
        
        Args:
            mployer_username: Your Mployer login email
            mployer_password: Your Mployer login password
            headless: Run browser in background (True) or visible (False)
        """
        self.username = mployer_username
        self.password = mployer_password
        self.headless = headless
        self.driver = None
        self.base_url = "https://mployeradvisor.com"
        
    def initialize_browser(self):
        """Start Chrome browser with Selenium"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        try:
            # Use cached ChromeDriver from local .wdm folder if available
            chromedriver_path = Path.home() / ".wdm" / "drivers" / "chromedriver" / "win64" / "144.0.7559.133" / "chromedriver-win32" / "chromedriver.exe"
            
            if chromedriver_path.exists():
                logger.info(f"Using cached ChromeDriver")
                service = Service(str(chromedriver_path))
                # Increase timeout for connectable check
                service.creationflags = 0x08000000  # CREATE_NO_WINDOW
            else:
                # Fallback to webdriver-manager
                logger.info("Cached ChromeDriver not found, using webdriver-manager...")
                service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("✓ Browser initialized")
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
        
    def save_cookies(self):
        """Save cookies to file for session persistence"""
        try:
            cookies = self.driver.get_cookies()
            with open(COOKIES_FILE, 'wb') as f:
                pickle.dump(cookies, f)
            logger.info(f"✓ Cookies saved to {COOKIES_FILE}")
        except Exception as e:
            logger.warning(f"Could not save cookies: {e}")
    
    def load_cookies(self):
        """Load cookies from file if available"""
        if not Path(COOKIES_FILE).exists():
            logger.info("No saved cookies found")
            return False
        
        try:
            with open(COOKIES_FILE, 'rb') as f:
                cookies = pickle.load(f)
            
            if not cookies:
                logger.info("Cookies file is empty")
                return False
            
            # Don't navigate first - just try to add cookies directly
            # Navigate to domain first (required to set cookies)
            try:
                logger.info("Navigating to Mployer to set cookies...")
                self.driver.get(self.base_url)
                time.sleep(1)
            except Exception as e:
                logger.warning(f"Could not navigate for cookie setup: {e}")
                # Try adding cookies anyway
                pass
            
            # Add each cookie
            added_count = 0
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                    added_count += 1
                except Exception as e:
                    logger.debug(f"Could not add cookie {cookie.get('name', '?')}: {e}")
            
            if added_count > 0:
                logger.info(f"✓ Added {added_count} cookies from file")
                # Verify cookies work by navigating to search
                try:
                    logger.info("Verifying cookies by navigating to search page...")
                    self.driver.get("https://portal.mployeradvisor.com/catalyst/employer")
                    time.sleep(2)
                    if "auth0" not in self.driver.current_url.lower():
                        logger.info("✓ Cookies valid - logged in!")
                        return True
                except Exception as e:
                    logger.debug(f"Could not verify cookies: {e}")
                    return False
            else:
                logger.info("No cookies were successfully added")
                return False
                
        except Exception as e:
            logger.warning(f"Could not load cookies: {e}")
            return False
        
    def login_to_mployer(self) -> bool:
        """
        Log into Mployer account. Uses saved cookies if available.
        If MFA is required, pauses for manual code entry.
        
        Returns:
            True if login successful, False otherwise
        """
        try:
            # Try loading saved cookies first
            if self.load_cookies():
                logger.info("Attempting login with saved cookies...")
                self.driver.get(f"{self.base_url}/")
                time.sleep(3)
                
                # Check if we're logged in
                if self._check_login_status():
                    logger.info("✓ Successfully logged in with saved cookies!")
                    return True
                else:
                    logger.info("Saved cookies expired, performing full login...")
            
            logger.info("Logging into Mployer...")
            logger.info(f"Navigating to {self.base_url}/login")
            self.driver.get(f"{self.base_url}/login")
            logger.info(f"Page title: {self.driver.title}")
            logger.info(f"Current URL: {self.driver.current_url}")
            
            # Wait for login form
            wait = WebDriverWait(self.driver, 20)
            
            # Step 1: Email/username (Auth0 identifier page)
            logger.info("Step 1: Entering email...")
            username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
            username_field.clear()
            username_field.send_keys(self.username)
            logger.info("Email entered successfully")
            
            logger.info("Clicking continue button...")
            continue_button = self.driver.find_element(By.CSS_SELECTOR, "button._button-login-id")
            continue_button.click()
            logger.info("Continue button clicked")
            
            # Step 2: Password (wait for password input to appear)
            logger.info("Step 2: Waiting for password field...")
            password_field = wait.until(EC.presence_of_element_located((By.ID, "password")))
            logger.info("Password field found")
            password_field.clear()
            password_field.send_keys(self.password)
            logger.info("Password entered successfully")
            
            # Click the password-step submit button if present
            try:
                logger.info("Clicking login button...")
                login_button = self.driver.find_element(By.CSS_SELECTOR, "button._button-login-password")
                login_button.click()
                logger.info("Login button clicked")
            except Exception as e:
                logger.info(f"Login button not found, using Enter key: {e}")
                password_field.send_keys(Keys.ENTER)
            
            # Check for MFA challenge
            time.sleep(3)
            if "mfa-email-challenge" in self.driver.current_url:
                logger.info("⚠️ Email MFA verification required")
                
                # Check "Remember this device for 30 days" automatically
                try:
                    remember_label = self.driver.find_element(By.CSS_SELECTOR, "label[for='rememberBrowser']")
                    remember_label.click()
                    logger.info("✓ 'Remember device' checkbox selected")
                except Exception as e:
                    logger.warning(f"Could not check 'Remember device' box: {e}")
                
                # Try to get code from email
                logger.info("Attempting to retrieve verification code from email...")
                code = self._get_mfa_code_from_email()
                
                if code:
                    logger.info(f"✓ Retrieved code: {code}")
                    try:
                        code_field = self.driver.find_element(By.ID, "code")
                        code_field.clear()
                        code_field.send_keys(code)
                        logger.info("✓ Code entered")
                        
                        # Click continue button
                        continue_btn = self.driver.find_element(By.CSS_SELECTOR, "button[value='default']")
                        continue_btn.click()
                        logger.info("✓ Continue button clicked, waiting for verification...")
                        time.sleep(5)
                    except Exception as e:
                        logger.error(f"Failed to enter code: {e}")
                        if not self.headless:
                            input("Please enter the code manually and press Enter...")
                        else:
                            return False
                else:
                    logger.warning("Could not retrieve code automatically")
                    logger.warning("=" * 60)
                    logger.warning("Please check your email for the verification code")
                    logger.warning("Enter the code in the browser window, then press Enter here...")
                    logger.warning("=" * 60)
                    
                    if not self.headless:
                        input("Press Enter after completing MFA in the browser...")
                        # Give more time for the page to process the MFA code
                        logger.info("Waiting for MFA verification to complete...")
                        time.sleep(5)
                    else:
                        logger.error("Cannot complete MFA in headless mode!")
                        return False
            
            # Wait for redirect away from Auth0 and into Mployer app
            logger.info("Waiting for redirect from Auth0...")
            redirect_success = False
            try:
                wait.until(lambda d: "auth0.com" not in d.current_url.lower())
                logger.info(f"Redirected to: {self.driver.current_url}")
                redirect_success = True
            except Exception as e:
                # Check if we're still on the MFA page and not in headless mode
                # If so, wait for user to manually complete MFA
                if "mfa-email-challenge" in self.driver.current_url and not self.headless:
                    logger.warning(f"Still on MFA page - waiting for manual completion...")
                    logger.warning("=" * 60)
                    logger.warning("Please check your email for the verification code")
                    logger.warning("Enter the code in the browser window, then press Enter here...")
                    logger.warning("=" * 60)
                    input("Press Enter after completing MFA in the browser...")
                    # Give more time for the page to process the MFA code
                    logger.info("Waiting for MFA verification to complete...")
                    time.sleep(5)
                    
                    # Try again to wait for redirect
                    try:
                        WebDriverWait(self.driver, 20).until(lambda d: "auth0.com" not in d.current_url.lower())
                        logger.info(f"Redirected to: {self.driver.current_url}")
                        redirect_success = True
                    except Exception as retry_error:
                        logger.error(f"Still on Auth0 after MFA manual entry. URL: {self.driver.current_url}")
                        redirect_success = False
                else:
                    logger.error(f"Redirect timeout. Current URL: {self.driver.current_url}")
                    logger.error(f"Page title: {self.driver.title}")
                    # Take screenshot for debugging
                    screenshot_path = "login_error_screenshot.png"
                    self.driver.save_screenshot(screenshot_path)
                    logger.error(f"Screenshot saved to {screenshot_path}")
                    # Check for error messages
                    try:
                        error_msgs = self.driver.find_elements(By.CLASS_NAME, "error")
                        if error_msgs:
                            for err in error_msgs:
                                logger.error(f"Error on page: {err.text}")
                    except:
                        pass
                    redirect_success = False
            
            if not redirect_success:
                logger.error("Could not complete redirect from Auth0")
                raise Exception("Auth0 redirect failed")
            
            # Confirm dashboard loaded
            logger.info("Waiting for dashboard to load...")
            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//span[contains(normalize-space(.), 'Employer Search')]")
                )
            )
            
            logger.info("✓ Successfully logged into Mployer")
            
            # Save cookies for future use
            self.save_cookies()
            
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def _check_login_status(self) -> bool:
        """Check if currently logged into Mployer"""
        try:
            # Check for dashboard element
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//span[contains(normalize-space(.), 'Employer Search')]")
                )
            )
            return True
        except:
            return False
    
    def _get_mfa_code_from_email(self, max_wait: int = 60) -> Optional[str]:
        """
        Attempt to retrieve MFA code from email.
        Priority: Microsoft Graph (OAuth), then fallback to IMAP if configured.
        
        Args:
            max_wait: Maximum seconds to wait for email
            
        Returns:
            Verification code or None if not found
        """
        # Try Microsoft Graph first (preferred method)
        try:
            from backend.msgraph_email import get_mfa_code_from_msgraph
            logger.info("Attempting to retrieve code via Microsoft Graph...")
            code = get_mfa_code_from_msgraph(from_sender="mployeradvisor", max_wait=max_wait)
            if code:
                return code
            logger.info("Microsoft Graph: No code found, trying IMAP fallback...")
        except Exception as e:
            logger.warning(f"Microsoft Graph retrieval failed: {e}")
            logger.info("Falling back to IMAP...")
        
        # Fallback to IMAP if Graph fails or isn't configured
        return self._get_mfa_code_from_imap(max_wait=max_wait)

    def _get_mfa_code_from_imap(self, max_wait: int = 60) -> Optional[str]:
        """Retrieve MFA code from IMAP (Microsoft 365 or any IMAP host)."""
        try:
            import re
            import imaplib
            import email
            from datetime import datetime, timedelta
            
            imap_server = os.getenv("EMAIL_IMAP_SERVER", "outlook.office365.com")
            email_address = os.getenv("EMAIL_IMAP_USER") or self.username
            email_password = os.getenv("EMAIL_IMAP_PASSWORD")
            
            if not email_password:
                logger.info("EMAIL_IMAP_PASSWORD not set - skipping IMAP retrieval")
                logger.info("To enable: Add EMAIL_IMAP_USER and EMAIL_IMAP_PASSWORD to .env")
                return None
            
            logger.info(f"Connecting to IMAP server {imap_server} for {email_address}...")
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(email_address, email_password)
            mail.select("inbox")
            
            cutoff = (datetime.now() - timedelta(minutes=5)).strftime("%d-%b-%Y")
            _, message_ids = mail.search(None, f'(FROM "mployer" SINCE {cutoff})')
            
            if not message_ids[0]:
                logger.info("No recent Mployer emails found")
                mail.logout()
                return None
            
            latest_email_id = message_ids[0].split()[-1]
            _, msg_data = mail.fetch(latest_email_id, "(RFC822)")
            
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            code_pattern = r"\b(\d{6})\b"
            
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="ignore")
                    match = re.search(code_pattern, body)
                    if match:
                        mail.logout()
                        logger.info("✓ Found verification code in IMAP")
                        return match.group(1)
                elif part.get_content_type() == "text/html":
                    body = part.get_payload(decode=True).decode(errors="ignore")
                    match = re.search(code_pattern, body)
                    if match:
                        mail.logout()
                        logger.info("✓ Found verification code in IMAP")
                        return match.group(1)
            
            mail.logout()
            logger.warning("Could not find verification code in IMAP")
            return None
        except Exception as e:
            logger.warning(f"IMAP retrieval failed: {e}")
            return None

    
    def search_contacts(self, 
                       job_title: str = "Head of HR",
                       location: str = "Baltimore, Maryland",
                       company_size_min: int = 10,
                       company_size_max: int = 500,
                       exclude_keywords: List[str] = None) -> List[Dict]:
        """
        Search Mployer for contacts matching criteria.
        
        Args:
            job_title: Target job title
            location: Geographic location
            company_size_min: Minimum employees
            company_size_max: Maximum employees
            exclude_keywords: Industries/types to exclude (government, union, etc)
            
        Returns:
            List of contact dictionaries
        """
        if exclude_keywords is None:
            exclude_keywords = ["government", "union", "federal", "military"]
        
        try:
            logger.info(f"Searching Mployer for {job_title} in {location}...")
            
            # Navigate to search/contacts page
            # NOTE: Adjust URL based on actual Mployer structure
            self.driver.get(f"{self.base_url}/search")
            
            wait = WebDriverWait(self.driver, 10)
            
            # Fill search criteria
            # NOTE: These selectors will need to be adjusted to Mployer's actual fields
            
            # Search by title
            title_field = wait.until(EC.presence_of_element_located((By.NAME, "job_title")))
            title_field.clear()
            title_field.send_keys(job_title)
            
            # Search by location
            location_field = self.driver.find_element(By.NAME, "location")
            location_field.clear()
            location_field.send_keys(location)
            
            # Set company size range
            size_min_field = self.driver.find_element(By.NAME, "company_size_min")
            size_min_field.clear()
            size_min_field.send_keys(str(company_size_min))
            
            size_max_field = self.driver.find_element(By.NAME, "company_size_max")
            size_max_field.clear()
            size_max_field.send_keys(str(company_size_max))
            
            # Click search button
            search_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Search')]")
            search_button.click()
            
            # Wait for results to load
            time.sleep(3)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-results")))
            
            # Extract contacts from results
            contacts = self._extract_contacts_from_results(exclude_keywords)
            
            logger.info(f"✓ Found {len(contacts)} contacts matching criteria")
            return contacts
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _extract_contacts_from_results(self, exclude_keywords: List[str]) -> List[Dict]:
        """
        Extract contact information from search results page.
        
        Args:
            exclude_keywords: Keywords to filter out
            
        Returns:
            List of contact data dictionaries
        """
        contacts = []
        
        try:
            # Find all result rows
            # NOTE: Adjust selector based on Mployer's actual HTML structure
            result_rows = self.driver.find_elements(By.CLASS_NAME, "contact-row")
            
            logger.info(f"Processing {len(result_rows)} result rows...")
            
            for row in result_rows:
                try:
                    # Extract data from each row
                    # NOTE: These selectors will need adjustment
                    contact = {}
                    
                    # Get name
                    name_elem = row.find_element(By.CLASS_NAME, "contact-name")
                    full_name = name_elem.text.strip()
                    
                    # Split first and last name
                    name_parts = full_name.split()
                    contact["firstName"] = name_parts[0] if len(name_parts) > 0 else ""
                    contact["lastName"] = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                    
                    # Get job title
                    title_elem = row.find_element(By.CLASS_NAME, "job-title")
                    contact["jobTitle"] = title_elem.text.strip()
                    
                    # Get company
                    company_elem = row.find_element(By.CLASS_NAME, "company-name")
                    contact["companyName"] = company_elem.text.strip()
                    
                    # Get email
                    try:
                        email_elem = row.find_element(By.CLASS_NAME, "email")
                        contact["email"] = email_elem.text.strip()
                    except:
                        contact["email"] = ""
                    
                    # Get phone
                    try:
                        phone_elem = row.find_element(By.CLASS_NAME, "phone")
                        contact["phone"] = phone_elem.text.strip()
                    except:
                        contact["phone"] = ""
                    
                    # Get address
                    try:
                        address_elem = row.find_element(By.CLASS_NAME, "address")
                        contact["address"] = address_elem.text.strip()
                    except:
                        contact["address"] = ""
                    
                    # Get company size
                    try:
                        size_elem = row.find_element(By.CLASS_NAME, "company-size")
                        contact["companySize"] = size_elem.text.strip()
                    except:
                        contact["companySize"] = ""
                    
                    # Get LinkedIn URL
                    try:
                        linkedin_elem = row.find_element(By.CLASS_NAME, "linkedin-url")
                        contact["linkedinUrl"] = linkedin_elem.get_attribute("href")
                    except:
                        contact["linkedinUrl"] = ""
                    
                    # Filter out excluded types
                    should_exclude = any(
                        keyword.lower() in contact.get("companyName", "").lower() 
                        for keyword in exclude_keywords
                    )
                    
                    if not should_exclude and contact.get("firstName") and contact.get("email"):
                        contacts.append(contact)
                        logger.info(f"  ✓ Extracted: {contact['firstName']} {contact['lastName']} ({contact['companyName']})")
                    
                except Exception as row_error:
                    logger.warning(f"Could not extract row: {row_error}")
                    continue
            
            return contacts
            
        except Exception as e:
            logger.error(f"Contact extraction failed: {e}")
            return contacts
    
    def add_contacts_to_ghl(self, contacts: List[Dict], workflow_id: Optional[str] = None) -> Dict:
        """
        Add extracted contacts to GoHighLevel.
        
        Args:
            contacts: List of contact dictionaries
            workflow_id: Optional workflow ID to trigger after adding
            
        Returns:
            Summary of added contacts
        """
        results = {
            "total": len(contacts),
            "successful": 0,
            "failed": 0,
            "contact_ids": [],
            "errors": []
        }
        
        for contact in contacts:
            try:
                # Check if contact already exists
                search_result = ghl_search_contact(contact.get("email", ""))
                
                if search_result.get("status") == "success" and search_result.get("count", 0) > 0:
                    logger.info(f"Contact already exists: {contact['firstName']} {contact['lastName']}")
                    continue
                
                # Prepare GHL contact format
                ghl_contact = {
                    "firstName": contact.get("firstName", ""),
                    "lastName": contact.get("lastName", ""),
                    "email": contact.get("email", ""),
                    "phone": contact.get("phone", ""),
                    "address": contact.get("address", ""),
                    "companyName": contact.get("companyName", ""),
                    "tags": ["Buddy List", "Mployer Research"],
                    "customFields": {
                        "job_title": contact.get("jobTitle", ""),
                        "company_size": contact.get("companySize", ""),
                        "linkedin_url": contact.get("linkedinUrl", ""),
                        "source": "Buddy Mployer Scraper"
                    }
                }
                
                # Add to GHL
                result = ghl_add_contact(json.dumps(ghl_contact))
                
                if result.get("status") == "success":
                    results["successful"] += 1
                    results["contact_ids"].append(result.get("contact_id"))
                    logger.info(f"✓ Added to GHL: {contact['firstName']} {contact['lastName']}")
                else:
                    results["failed"] += 1
                    error_msg = f"Failed to add {contact['firstName']}: {result.get('message')}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
                
            except Exception as e:
                results["failed"] += 1
                error_msg = f"Error processing {contact.get('firstName')}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
        
        logger.info(f"✓ Mployer import complete: {results['successful']} added, {results['failed']} failed")
        return results
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")
    
    def run_full_workflow(self, workflow_id: Optional[str] = None,
                         job_title: str = "Head of HR",
                         location: str = "Baltimore, Maryland",
                         company_size_min: int = 10,
                         company_size_max: int = 500,
                         exclude_keywords: List[str] = None,
                         max_contacts: int = 50) -> Dict:
        """
        Run complete workflow: login → search → extract → add to GHL
        
        Args:
            workflow_id: GHL workflow ID to trigger after adding
            job_title: Target job title
            location: Target location
            company_size_min: Min company size
            company_size_max: Max company size
            exclude_keywords: Keywords to exclude
            max_contacts: Maximum contacts to process
            
        Returns:
            Summary of results
        """
        try:
            self.initialize_browser()
            
            if not self.login_to_mployer():
                return {"status": "error", "message": "Login failed"}
            
            contacts = self.search_contacts(
                job_title=job_title,
                location=location,
                company_size_min=company_size_min,
                company_size_max=company_size_max,
                exclude_keywords=exclude_keywords
            )
            
            # Limit to max_contacts
            contacts = contacts[:max_contacts]
            
            results = self.add_contacts_to_ghl(contacts, workflow_id)
            
            return {
                "status": "success",
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            return {"status": "error", "message": str(e)}
        
        finally:
            self.close()
    
    def search_employers(self, 
                        employer_name: str = None,
                        employees_min: int = None,
                        employees_max: int = None,
                        revenue_min: int = None,
                        revenue_max: int = None,
                        city: str = None,
                        state: str = None,
                        industry: str = None,
                        exclude_industry: str = None,
                        zip_code: str = None,
                        street_address: str = None,
                        ein: str = None,
                        website: str = None) -> List[Dict]:
        """
        Search for employers on Mployer Catalyst using ALL available filters.
        
        Args:
            employer_name: Search by employer name
            employees_min: Minimum number of employees
            employees_max: Maximum number of employees
            revenue_min: Minimum revenue (millions)
            revenue_max: Maximum revenue (millions)
            city: Filter by city
            state: Filter by state
            industry: Include specific industry
            exclude_industry: Exclude specific industry
            zip_code: Filter by zip code
            street_address: Filter by street address
            ein: Filter by EIN (Employer ID Number)
            website: Filter by website domain
            
        Returns:
            List of employer dictionaries with all extracted data
        """
        try:
            logger.info("Navigating to Employer Search page...")
            self.driver.get("https://portal.mployeradvisor.com/catalyst/employer")
            time.sleep(3)
            
            wait = WebDriverWait(self.driver, 10)
            
            # APPLY ALL FILTERS using the discovered mapping
            logger.info("="*60)
            logger.info("APPLYING ALL AVAILABLE FILTERS")
            logger.info("="*60)
            
            # 1. EMPLOYER NAME FILTER
            if employer_name:
                logger.info(f"Applying filter: Employer Name = {employer_name}")
                try:
                    self.driver.execute_script(f"""
                    let inputs = document.querySelectorAll('input[type="text"]');
                    for (let input of inputs) {{
                        if (input.placeholder.includes('Search') && input.className.includes('rz-lookup')) {{
                            input.value = '{employer_name}';
                            input.dispatchEvent(new Event('input', {{bubbles: true}}));
                            input.dispatchEvent(new Event('change', {{bubbles: true}}));
                            break;
                        }}
                    }}
                    """)
                    time.sleep(0.5)
                except Exception as e:
                    logger.warning(f"Could not apply employer name filter: {e}")
            
            # 2. EMPLOYEE COUNT MIN/MAX
            if employees_min is not None or employees_max is not None:
                logger.info(f"Applying filter: Employee Range = {employees_min} - {employees_max}")
                try:
                    self.driver.execute_script(f"""
                    let inputs = document.querySelectorAll('input[id="minFilter"], input[id="maxFilter"]');
                    for (let input of inputs) {{
                        if (input.id === 'minFilter' && {employees_min}) {{
                            input.value = {employees_min};
                            input.dispatchEvent(new Event('input', {{bubbles: true}}));
                            input.dispatchEvent(new Event('change', {{bubbles: true}}));
                        }} else if (input.id === 'maxFilter' && {employees_max}) {{
                            input.value = {employees_max};
                            input.dispatchEvent(new Event('input', {{bubbles: true}}));
                            input.dispatchEvent(new Event('change', {{bubbles: true}}));
                        }}
                    }}
                    """)
                    time.sleep(0.5)
                except Exception as e:
                    logger.warning(f"Could not apply employee range filter: {e}")
            
            # 3. REVENUE MIN/MAX
            if revenue_min is not None or revenue_max is not None:
                logger.info(f"Applying filter: Revenue Range = ${revenue_min}M - ${revenue_max}M")
                try:
                    inputs = self.driver.find_elements(By.XPATH, "//input[@placeholder='Min' or @placeholder='Max']")
                    # Find the revenue fields (they come after employee filters)
                    idx = 0
                    for input_elem in inputs:
                        placeholder = input_elem.get_attribute('placeholder')
                        if placeholder == 'Min' or placeholder == 'Max':
                            idx += 1
                            # Skip first two (employee min/max) and use next two (revenue)
                            if idx == 3 and revenue_min is not None:
                                self.driver.execute_script(f"arguments[0].value = {revenue_min}; arguments[0].dispatchEvent(new Event('input', {{bubbles: true}})); arguments[0].dispatchEvent(new Event('change', {{bubbles: true}}));", input_elem)
                            elif idx == 4 and revenue_max is not None:
                                self.driver.execute_script(f"arguments[0].value = {revenue_max}; arguments[0].dispatchEvent(new Event('input', {{bubbles: true}})); arguments[0].dispatchEvent(new Event('change', {{bubbles: true}}));", input_elem)
                    time.sleep(0.5)
                except Exception as e:
                    logger.warning(f"Could not apply revenue filter: {e}")
            
            # 4. EIN FILTER
            if ein:
                logger.info(f"Applying filter: EIN = {ein}")
                try:
                    self.driver.execute_script(f"""
                    let inputs = document.querySelectorAll('input[data-intercom-target="employersearch_input_ein"]');
                    if (inputs.length > 0) {{
                        inputs[0].value = '{ein}';
                        inputs[0].dispatchEvent(new Event('input', {{bubbles: true}}));
                        inputs[0].dispatchEvent(new Event('change', {{bubbles: true}}));
                    }}
                    """)
                    time.sleep(0.5)
                except Exception as e:
                    logger.warning(f"Could not apply EIN filter: {e}")
            
            # 5. WEBSITE FILTER
            if website:
                logger.info(f"Applying filter: Website = {website}")
                try:
                    self.driver.execute_script(f"""
                    let inputs = document.querySelectorAll('input[data-intercom-target="employersearch_input_website"]');
                    if (inputs.length > 0) {{
                        inputs[0].value = '{website}';
                        inputs[0].dispatchEvent(new Event('input', {{bubbles: true}}));
                        inputs[0].dispatchEvent(new Event('change', {{bubbles: true}}));
                    }}
                    """)
                    time.sleep(0.5)
                except Exception as e:
                    logger.warning(f"Could not apply website filter: {e}")
            
            # 6. STATE FILTER
            if state:
                logger.info(f"Applying filter: State = {state}")
                try:
                    self.driver.execute_script(f"""
                    let inputs = document.querySelectorAll('input[data-intercom-target*="state"]');
                    for (let input of inputs) {{
                        if (input.placeholder.includes('Search')) {{
                            input.value = '{state}';
                            input.dispatchEvent(new Event('input', {{bubbles: true}}));
                            input.dispatchEvent(new Event('change', {{bubbles: true}}));
                            input.dispatchEvent(new Event('blur', {{bubbles: true}}));
                            break;
                        }}
                    }}
                    """)
                    time.sleep(1)
                except Exception as e:
                    logger.warning(f"Could not apply state filter: {e}")
            
            # 7. CITY FILTER
            if city:
                logger.info(f"Applying filter: City = {city}")
                try:
                    self.driver.execute_script(f"""
                    let inputs = document.querySelectorAll('input[data-intercom-target*="city"]');
                    for (let input of inputs) {{
                        if (input.placeholder.includes('Search')) {{
                            input.value = '{city}';
                            input.dispatchEvent(new Event('input', {{bubbles: true}}));
                            input.dispatchEvent(new Event('change', {{bubbles: true}}));
                            input.dispatchEvent(new Event('blur', {{bubbles: true}}));
                            break;
                        }}
                    }}
                    """)
                    time.sleep(1)
                except Exception as e:
                    logger.warning(f"Could not apply city filter: {e}")
            
            # 8. ZIP CODE FILTER
            if zip_code:
                logger.info(f"Applying filter: Zip Code = {zip_code}")
                try:
                    self.driver.execute_script(f"""
                    let inputs = document.querySelectorAll('input[data-intercom-target="employersearch_input_zipcode"]');
                    if (inputs.length > 0) {{
                        inputs[0].value = '{zip_code}';
                        inputs[0].dispatchEvent(new Event('input', {{bubbles: true}}));
                        inputs[0].dispatchEvent(new Event('change', {{bubbles: true}}));
                    }}
                    """)
                    time.sleep(0.5)
                except Exception as e:
                    logger.warning(f"Could not apply zip code filter: {e}")
            
            # 9. STREET ADDRESS FILTER
            if street_address:
                logger.info(f"Applying filter: Street Address = {street_address}")
                try:
                    self.driver.execute_script(f"""
                    let inputs = document.querySelectorAll('input[data-intercom-target="employersearch_input_streetaddress"]');
                    if (inputs.length > 0) {{
                        inputs[0].value = '{street_address}';
                        inputs[0].dispatchEvent(new Event('input', {{bubbles: true}}));
                        inputs[0].dispatchEvent(new Event('change', {{bubbles: true}}));
                    }}
                    """)
                    time.sleep(0.5)
                except Exception as e:
                    logger.warning(f"Could not apply street address filter: {e}")
            
            # 10. INDUSTRY FILTER (INCLUDE)
            if industry:
                logger.info(f"Applying filter: Industry (Include) = {industry}")
                try:
                    self.driver.execute_script(f"""
                    let inputs = document.querySelectorAll('input[data-intercom-target*="industry_"]');
                    for (let input of inputs) {{
                        if (input.placeholder.includes('Search') && !input.getAttribute('data-intercom-target').includes('exclude')) {{
                            input.value = '{industry}';
                            input.dispatchEvent(new Event('input', {{bubbles: true}}));
                            input.dispatchEvent(new Event('change', {{bubbles: true}}));
                            input.dispatchEvent(new Event('blur', {{bubbles: true}}));
                            break;
                        }}
                    }}
                    """)
                    time.sleep(1)
                except Exception as e:
                    logger.warning(f"Could not apply industry filter: {e}")
            
            # 11. INDUSTRY FILTER (EXCLUDE)
            if exclude_industry:
                logger.info(f"Applying filter: Industry (Exclude) = {exclude_industry}")
                try:
                    self.driver.execute_script(f"""
                    let inputs = document.querySelectorAll('input[data-intercom-target*="excludeindustry"]');
                    for (let input of inputs) {{
                        if (input.placeholder.includes('Search')) {{
                            input.value = '{exclude_industry}';
                            input.dispatchEvent(new Event('input', {{bubbles: true}}));
                            input.dispatchEvent(new Event('change', {{bubbles: true}}));
                            input.dispatchEvent(new Event('blur', {{bubbles: true}}));
                            break;
                        }}
                    }}
                    """)
                    time.sleep(1)
                except Exception as e:
                    logger.warning(f"Could not apply exclude industry filter: {e}")
            
            logger.info("="*60)
            
            # CLICK APPLY FILTERS
            logger.info("Clicking 'Apply Filters' button...")
            try:
                apply_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Apply Filters')]")
                self.driver.execute_script("arguments[0].click();", apply_button)
                logger.info("✓ Apply Filters clicked")
            except Exception as e:
                logger.warning(f"Could not click Apply Filters: {e}")
            
            # Wait for results to load
            logger.info("Waiting for search results...")
            time.sleep(5)
            
            # Extract results
            employers = self._extract_employer_results()
            
            logger.info(f"✓ Found {len(employers)} employers")
            return employers
            
        except Exception as e:
            logger.error(f"Employer search failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_employer_results(self) -> List[Dict]:
        """Extract employer data from search results table"""
        employers = []
        
        try:
            # Wait for results table to appear
            time.sleep(2)
            
            # Look for result rows in various possible structures
            # Mployer might use table rows, divs, or custom components
            result_selectors = [
                "tr",  # Table rows
                "[role='row']",  # Accessible rows
                ".result-row",
                ".employer-card",
                ".employer-result",
                "div[class*='row'][class*='result']"
            ]
            
            result_elements = []
            for selector in result_selectors:
                try:
                    result_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(result_elements) > 2:  # Found results
                        logger.info(f"Found {len(result_elements)} result elements using selector: {selector}")
                        break
                except:
                    continue
            
            if not result_elements:
                logger.warning("No result elements found, checking for table cells")
                # Try to find any table cells with company info
                result_elements = self.driver.find_elements(By.TAG_NAME, "td")
            
            logger.info(f"Processing {len(result_elements)} result elements...")
            
            # Process results - skip header rows
            for i, element in enumerate(result_elements):
                try:
                    # Get all text from the element
                    text = element.text.strip()
                    
                    if not text or len(text) < 2:
                        continue
                    
                    # Skip common header/footer text
                    if any(skip in text.lower() for skip in ["employer name", "employees", "rating", "export", "loading", "no results"]):
                        continue
                    
                    # Try to extract structured data
                    cells = element.find_elements(By.TAG_NAME, "td")
                    
                    if cells:
                        # Table row with multiple columns
                        employer_name = cells[0].text.strip() if cells else ""
                        
                        employer_data = {
                            "name": employer_name,
                            "employees": cells[1].text.strip() if len(cells) > 1 else None,
                            "location": cells[2].text.strip() if len(cells) > 2 else None,
                            "industry": cells[3].text.strip() if len(cells) > 3 else None,
                            "rating": cells[4].text.strip() if len(cells) > 4 else None,
                            "source": "mployer"
                        }
                        
                        if employer_name:
                            employers.append(employer_data)
                            logger.debug(f"Added employer: {employer_name}")
                    else:
                        # Single element with combined text (div or custom component)
                        # Split by common patterns
                        lines = text.split('\n')
                        if lines:
                            employer_data = {
                                "name": lines[0],
                                "employees": lines[1] if len(lines) > 1 else None,
                                "location": lines[2] if len(lines) > 2 else None,
                                "industry": lines[3] if len(lines) > 3 else None,
                                "raw_text": text,
                                "source": "mployer"
                            }
                            employers.append(employer_data)
                            logger.debug(f"Added employer: {lines[0]}")
                
                except Exception as e:
                    logger.debug(f"Error extracting employer {i}: {e}")
                    continue
            
            # Remove duplicates and empty entries
            unique_employers = []
            seen_names = set()
            
            for emp in employers:
                name = emp.get('name', '').lower().strip()
                if name and name not in seen_names:
                    seen_names.add(name)
                    unique_employers.append(emp)
            
            logger.info(f"Extracted {len(unique_employers)} unique employers")
            return unique_employers
            
        except Exception as e:
            logger.error(f"Error extracting results: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def inspect_page_elements(self) -> Dict:
        """
        Extract ALL element information from the page using developer inspection.
        This reads the DOM structure like the browser's Elements Inspector would show.
        
        Returns:
            Dictionary containing:
            - filters: All filter sections with their structure
            - inputs: All input fields with attributes
            - buttons: All buttons with their properties
            - tables: Table structure information
            - page_state: Current page state (title, URL, counts)
            - element_map: Complete mapping of how to access each element
        """
        try:
            logger.info("Inspecting page elements...")
            
            # Run comprehensive JavaScript inspection
            inspection = self.driver.execute_script("""
            const inspection = {
                timestamp: new Date().toISOString(),
                url: window.location.href,
                title: document.title,
                filters: {
                    sections: [],
                    allFilters: []
                },
                inputs: [],
                buttons: [],
                tables: [],
                forms: [],
                counts: {
                    total_inputs: 0,
                    total_buttons: 0,
                    total_tables: 0
                }
            };
            
            // ========== 1. FIND ALL FILTER SECTIONS ==========
            // Look for accordion/collapse sections (common filter pattern)
            document.querySelectorAll('[class*="accordion"], [class*="filter"], [class*="expand"], [class*="section"]').forEach((elem) => {
                const text = elem.textContent?.substring(0, 100) || '';
                if (text && /filter|employee|location|industry|size/i.test(text)) {
                    inspection.filters.sections.push({
                        tag: elem.tagName,
                        id: elem.id,
                        classes: elem.className,
                        text: text,
                        xpath: null, // Will be calculated separately
                        children_count: elem.children.length,
                        is_visible: elem.offsetHeight > 0
                    });
                }
            });
            
            // ========== 2. FIND ALL INPUT FIELDS ==========
            // Capture all text inputs, number inputs, selects, textareas
            document.querySelectorAll('input[type="text"], input[type="number"], input[type="email"], select, textarea').forEach((input) => {
                if (input.id || input.name || input.placeholder) {
                    const rect = input.getBoundingClientRect();
                    const styles = window.getComputedStyle(input);
                    
                    inspection.inputs.push({
                        tag: input.tagName,
                        type: input.type,
                        id: input.id,
                        name: input.name,
                        placeholder: input.placeholder,
                        value: input.value,
                        class: input.className,
                        // Visual properties
                        is_visible: rect.height > 0 && rect.width > 0 && styles.display !== 'none',
                        is_enabled: !input.disabled,
                        is_required: input.required,
                        // Position for debugging
                        position: { x: Math.round(rect.x), y: Math.round(rect.y), width: Math.round(rect.width), height: Math.round(rect.height) },
                        // Find parent container info
                        parent_class: input.parentElement?.className,
                        parent_id: input.parentElement?.id,
                        // For filter fields specifically
                        is_filter_field: /filter|min|max|range|employee/i.test(input.id + input.name + input.placeholder)
                    });
                }
            });
            
            inspection.counts.total_inputs = inspection.inputs.length;
            
            // ========== 3. FIND ALL BUTTONS ==========
            document.querySelectorAll('button, [role="button"]').forEach((btn) => {
                const text = btn.textContent?.trim() || '';
                const rect = btn.getBoundingClientRect();
                const styles = window.getComputedStyle(btn);
                
                if (text.length > 0 && text.length < 100) {
                    inspection.buttons.push({
                        tag: btn.tagName,
                        text: text,
                        id: btn.id,
                        class: btn.className,
                        is_visible: rect.height > 0 && styles.display !== 'none',
                        is_enabled: !btn.disabled,
                        position: { x: Math.round(rect.x), y: Math.round(rect.y) },
                        // Special markers for common button types
                        is_apply_button: /apply|filter|search|submit/i.test(text),
                        is_clear_button: /clear|reset/i.test(text)
                    });
                }
            });
            
            inspection.counts.total_buttons = inspection.buttons.length;
            
            // ========== 4. FIND ALL TABLES ==========
            document.querySelectorAll('table, [role="table"], [class*="table"]').forEach((table) => {
                const rows = table.querySelectorAll('tr, [role="row"]');
                const cols = table.querySelectorAll('td, [role="cell"]');
                
                inspection.tables.push({
                    tag: table.tagName,
                    id: table.id,
                    class: table.className,
                    row_count: rows.length,
                    col_count: cols.length,
                    has_header: !!table.querySelector('thead, [role="rowheader"]'),
                    is_visible: table.offsetHeight > 0
                });
            });
            
            inspection.counts.total_tables = inspection.tables.length;
            
            // ========== 5. GET PAGE STATE INFO ==========
            // Look for employer count display
            const bodyText = document.body.innerText;
            const countMatch = bodyText.match(/(\\d+[,\\d]*) employers? found/i);
            inspection.page_state = {
                employer_count: countMatch ? countMatch[1] : null,
                has_results: countMatch ? true : false,
                page_length: bodyText.length,
                visible_elements: document.querySelectorAll(':visible').length
            };
            
            // ========== 6. BUILD ELEMENT MAP (How to find each element) ==========
            inspection.element_map = {};
            
            // Map filter inputs
            inspection.inputs.filter(inp => inp.is_filter_field).forEach((inp) => {
                const key = inp.id || inp.name || inp.placeholder;
                if (key) {
                    inspection.element_map[key] = {
                        type: 'input',
                        selector_id: inp.id ? `document.getElementById('${inp.id}')` : null,
                        selector_name: inp.name ? `document.querySelector('[name="${inp.name}"]')` : null,
                        selector_xpath: null, // Would need xpath library
                        value_current: inp.value,
                        how_to_set: 'element.value = "X"; element.dispatchEvent(new Event("input", {bubbles: true}));',
                        visible: inp.is_visible,
                        enabled: inp.is_enabled
                    };
                }
            });
            
            // Map apply button
            const applyBtn = inspection.buttons.find(b => b.is_apply_button && /apply.*filter/i.test(b.text));
            if (applyBtn) {
                inspection.element_map['ApplyFilters'] = {
                    type: 'button',
                    text: applyBtn.text,
                    selector_text: `document.querySelector('button:contains("${applyBtn.text}")')`,
                    how_to_click: 'element.click(); or execute_script("arguments[0].click();", element)',
                    visible: applyBtn.is_visible,
                    enabled: applyBtn.is_enabled
                };
            }
            
            return inspection;
            """)
            
            logger.info(f"Inspection complete: {inspection['counts']['total_inputs']} inputs, {inspection['counts']['total_buttons']} buttons, {inspection['counts']['total_tables']} tables")
            return inspection
            
        except Exception as e:
            logger.error(f"Page inspection failed: {e}")
            return {}
    
    def save_inspection_to_file(self, inspection: Dict, filename: str = "page_inspection.json") -> Path:
        """Save inspection data to JSON file for reference"""
        try:
            filepath = Path(filename)
            with open(filepath, 'w') as f:
                json.dump(inspection, f, indent=2)
            logger.info(f"Inspection saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Could not save inspection: {e}")
            return None


def run_mployer_automation(username: str, password: str, config: Dict) -> Dict:
    """
    Run Mployer automation with configuration.
    
    Args:
        username: Mployer username
        password: Mployer password
        config: Configuration dictionary with search criteria
        
    Returns:
        Results dictionary
    """
    # Use visible browser to support MFA if needed
    scraper = MployerScraper(username, password, headless=False)
    
    return scraper.run_full_workflow(
        workflow_id=config.get("workflow_id"),
        job_title=config.get("job_title", "Head of HR"),
        location=config.get("location", "Baltimore, Maryland"),
        company_size_min=config.get("company_size_min", 10),
        company_size_max=config.get("company_size_max", 500),
        exclude_keywords=config.get("exclude_keywords", ["government", "union", "federal"]),
        max_contacts=config.get("max_contacts", 50)
    )
