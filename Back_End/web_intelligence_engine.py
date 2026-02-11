"""
WEB INTELLIGENCE ENGINE (v2.0)
================================

Intelligent web research agent that:
1. Understands user intent dynamically (no rigid templates)
2. Searches the web using SerpAPI
3. Crawls discovered sites intelligently
4. Extracts structured information via LLM
5. Caches results to Firebase for 48 hours
6. Respects rate limiting with human-like behavior
7. Adapts depth based on results and time spent
8. Uses webhooks for async user approval on deeper dives

Key Features:
- Flexible task understanding (no templates needed)
- SerpAPI integration for discovery
- Multi-page crawling with intelligent prioritization
- LLM-powered semantic extraction
- Firebase caching (48-hour TTL)
- Rate limiting (human-like delays, jitter, etc.)
- Progressive depth with webhook-based user confirmation
- Contact extraction for B2B research
"""

import logging
import time
import hashlib
import json
import random
import uuid
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from urllib.parse import urljoin, urlparse

from Back_End.config import Config
from Back_End.llm_client import llm_client
from Back_End.web_scraper import scrape_webpage
from Back_End.tool_registry import tool_registry
from Back_End.search_engines_registry import search_engines

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class ResearchDepth(Enum):
    """How deep to research"""
    QUICK = "quick"          # 1-2 pages, 30 sec max
    STANDARD = "standard"    # 3-5 pages, 60 sec max
    COMPREHENSIVE = "comp"   # 6-10 pages, 120 sec max


class TaskCategory(Enum):
    """Auto-detected task types"""
    COMPANY_RESEARCH = "company"      # Tell me about X company
    CONTACT_EXTRACTION = "contacts"   # Find contact info for X
    PRODUCT_RESEARCH = "product"      # What is product X
    COMPARISON = "comparison"         # Compare X vs Y
    LOCATION_SEARCH = "location"      # Find locations of X
    PRICING_RESEARCH = "pricing"      # What are prices for X
    CUSTOM = "custom"                 # Unknown/flexible


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class SearchResult:
    """Single search result from SerpAPI"""
    title: str
    link: str
    snippet: str
    position: int
    source: str = "google"


@dataclass
class PageContent:
    """Extracted content from a single page"""
    url: str
    title: str
    content: str
    extracted_data: Dict[str, Any]
    crawled_at: str
    word_count: int


@dataclass
class ResearchSession:
    """Active research tracking"""
    session_id: str
    query: str
    task_category: TaskCategory
    start_time: float
    current_depth: ResearchDepth
    pages_crawled: List[str]
    findings: Dict[str, Any]
    status: str  # "in_progress", "paused_for_approval", "complete"


# ============================================================================
# CONFIGURATION
# ============================================================================

class WebIntelligenceConfig:
    """Dynamic configuration for web intelligence"""
    
    # Rate limiting - human-like behavior
    REQUEST_DELAY_MIN = 1.0      # seconds
    REQUEST_DELAY_MAX = 3.0      # seconds
    JITTER_FACTOR = 0.3          # 30% random variance
    
    # Search parameters
    SEARCH_RESULTS_PER_QUERY = 10
    MAX_DOMAIN_REQUESTS = 5       # Don't hammer one domain
    
    # Crawling depths
    CRAWL_LIMITS = {
        ResearchDepth.QUICK: (1, 30),          # (pages, seconds)
        ResearchDepth.STANDARD: (5, 60),
        ResearchDepth.COMPREHENSIVE: (10, 120),
    }
    
    # Content extraction
    MAX_CONTENT_PER_PAGE = 15000  # characters
    MAX_TOTAL_CONTENT = 50000     # for LLM
    
    # Timeout
    PAGE_LOAD_TIMEOUT = 15  # seconds


# ============================================================================
# FIREBASE CACHING LAYER
# ============================================================================

class FirebaseResearchCache:
    """Firebase-backed cache for research results (48-hour TTL)"""
    
    def __init__(self):
        self.db = None
        self.collection_name = "web_research_cache"
        self._init_firebase()
    
    def _init_firebase(self):
        """Initialize Firebase connection if enabled"""
        if not Config.FIREBASE_ENABLED:
            logger.warning("[CACHE] Firebase not enabled, caching disabled")
            return
        
        try:
            from Back_End.memory import FirebaseMemory
            self.firebase = FirebaseMemory()
            logger.info("[CACHE] Firebase cache initialized")
        except Exception as e:
            logger.warning(f"[CACHE] Firebase init failed: {e}")
            self.firebase = None
    
    def _make_key(self, query: str) -> str:
        """Create consistent cache key"""
        return f"research_{hashlib.md5(query.lower().encode()).hexdigest()}"
    
    def get(self, query: str) -> Optional[Dict]:
        """Get cached research result if fresh"""
        if not Config.FIREBASE_ENABLED or not self.firebase:
            return None
        
        try:
            key = self._make_key(query)
            cached = self.firebase.retrieve(key, "research_cache")
            
            if cached:
                cached_result = json.loads(cached) if isinstance(cached, str) else cached
                cached_at = datetime.fromisoformat(cached_result.get('cached_at', ''))
                age_hours = (datetime.now() - cached_at).total_seconds() / 3600
                
                if age_hours < 48:
                    logger.info(f"[CACHE_HIT] Query: {query[:50]}... (age: {age_hours:.1f}h)")
                    return cached_result['result']
                else:
                    logger.info(f"[CACHE_EXPIRED] Query: {query[:50]}...")
                    self.firebase.delete(key, "research_cache")
            
            return None
        except Exception as e:
            logger.warning(f"[CACHE_ERROR] Failed to get cache: {e}")
            return None
    
    def set(self, query: str, result: Dict) -> None:
        """Cache research result to Firebase for 48 hours"""
        if not Config.FIREBASE_ENABLED or not self.firebase:
            return
        
        try:
            key = self._make_key(query)
            cache_data = {
                'result': result,
                'cached_at': datetime.now().isoformat(),
                'query': query[:200]
            }
            
            self.firebase.save(key, json.dumps(cache_data), "research_cache")
            logger.info(f"[CACHE_STORED] Query: {query[:50]}...")
        except Exception as e:
            logger.warning(f"[CACHE_ERROR] Failed to set cache: {e}")


# ============================================================================
# RATE LIMITING WITH HUMAN-LIKE BEHAVIOR
# ============================================================================

class RateLimiter:
    """Enforce human-like rate limiting"""
    
    def __init__(self):
        self.last_request_time = {}  # domain -> timestamp
        self.domain_request_count = {}  # domain -> count
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        return urlparse(url).netloc
    
    def _smart_delay(self) -> None:
        """Realistic delay: base + jitter"""
        base = random.uniform(
            WebIntelligenceConfig.REQUEST_DELAY_MIN,
            WebIntelligenceConfig.REQUEST_DELAY_MAX
        )
        jitter = random.uniform(
            -base * WebIntelligenceConfig.JITTER_FACTOR,
            base * WebIntelligenceConfig.JITTER_FACTOR
        )
        delay = max(0.5, base + jitter)
        time.sleep(delay)
    
    def wait_for_domain(self, url: str) -> None:
        """Check rate limits and wait if needed"""
        domain = self._get_domain(url)
        
        # Check request count
        count = self.domain_request_count.get(domain, 0)
        if count >= WebIntelligenceConfig.MAX_DOMAIN_REQUESTS:
            logger.warning(f"[RATE_LIMIT] Domain {domain} hit request limit")
            raise Exception(f"Rate limit: Too many requests to {domain}")
        
        # Smart delay
        self._smart_delay()
        
        # Track
        self.domain_request_count[domain] = count + 1
        self.last_request_time[domain] = time.time()
        
        logger.debug(f"[RATE_LIMITED] Delayed before: {domain}")


# ============================================================================
# TASK UNDERSTANDING (LLM-POWERED, NO TEMPLATES)
# ============================================================================

class TaskIntelligence:
    """Understand user intent without rigid templates"""
    
    @staticmethod
    def understand_task(query: str) -> Tuple[TaskCategory, Dict[str, str]]:
        """
        Use LLM to understand what user wants (flexible, no templates)
        Returns: (category, extracted_params)
        """
        
        prompt = f"""
Analyze this user research request and determine:
1. What type of task is this?
2. What are the key entities/targets?
3. What information is being sought?
4. Any specific requirements or constraints?

User Request: "{query}"

Return JSON:
{{
    "category": "company_research|contact_extraction|product_research|comparison|location_search|pricing_research|custom",
    "target_entity": "primary thing being researched",
    "search_focus": "what to prioritize in search",
    "specific_fields": ["field1", "field2"],
    "quality_requirements": "high/medium/low",
    "reasoning": "why you classified it this way"
}}
"""
        
        try:
            response = llm_client.complete(prompt, response_format="json", max_tokens=300)
            result = json.loads(response)
            
            category_str = result.get('category', 'custom').upper().replace(' ', '_')
            category = TaskCategory[category_str] if category_str in TaskCategory.__members__ else TaskCategory.CUSTOM
        except Exception as e:
            logger.warning(f"[TASK_UNDERSTAND_ERROR] {e}")
            category = TaskCategory.CUSTOM
            result = {
                'target_entity': query,
                'search_focus': query,
                'specific_fields': [],
                'quality_requirements': 'medium'
            }
        
        logger.info(f"[TASK_UNDERSTOOD] Category: {category.value}, Entity: {result.get('target_entity')}")
        return category, result


# ============================================================================
# SEARCH & DISCOVERY (SerpAPI)
# ============================================================================

class WebDiscovery:
    """Find relevant information via intelligent multi-engine search"""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.search_engines = search_engines
    
    def select_engines_for_task(self, task_category: TaskCategory) -> List[str]:
        """Select which search engines to use based on task type"""
        
        engine_map = {
            TaskCategory.COMPANY_RESEARCH: ["google", "google_maps", "google_news"],
            TaskCategory.CONTACT_EXTRACTION: ["google", "linkedin", "google_maps"],
            TaskCategory.PRODUCT_RESEARCH: ["google", "google_shopping", "amazon"],
            TaskCategory.COMPARISON: ["google", "google_shopping", "google_news"],
            TaskCategory.LOCATION_SEARCH: ["google_maps", "google"],
            TaskCategory.PRICING_RESEARCH: ["google_shopping", "amazon", "google"],
            TaskCategory.CUSTOM: ["google", "google_maps"]
        }
        
        return engine_map.get(task_category, ["google"])
    
    def search_multi_engine(self, query: str, task_category: TaskCategory, num_results: int = 10) -> Dict[str, Any]:
        """Search using multiple engines for comprehensive results"""
        
        engines_to_use = self.select_engines_for_task(task_category)
        all_results = {
            "query": query,
            "task_category": task_category.value,
            "engines_used": engines_to_use,
            "results_by_engine": {}
        }
        
        for engine in engines_to_use:
            try:
                logger.info(f"[MULTI_SEARCH] Using engine: {engine}")
                
                if engine == "google":
                    results = self.search_engines.search_google(query, num=num_results)
                elif engine == "google_maps":
                    results = self.search_engines.search_google_maps(query, num=num_results)
                elif engine == "google_news":
                    results = self.search_engines.search_google_news(query, num=num_results)
                elif engine == "linkedin":
                    results = self.search_engines.search_linkedin(query, num=num_results)
                elif engine == "google_scholar":
                    results = self.search_engines.search_google_scholar(query, num=num_results)
                elif engine == "google_shopping":
                    results = self.search_engines.search_google_shopping(query, num=num_results)
                elif engine == "youtube":
                    results = self.search_engines.search_youtube(query, num=num_results)
                elif engine == "google_trends":
                    results = self.search_engines.search_google_trends(query)
                elif engine == "amazon":
                    results = self.search_engines.search_amazon(query, num=num_results)
                elif engine == "google_jobs":
                    results = self.search_engines.search_google_jobs(query, num=num_results)
                else:
                    results = {"error": f"Unknown engine: {engine}"}
                
                all_results["results_by_engine"][engine] = results
                
            except Exception as e:
                logger.warning(f"[MULTI_SEARCH_ERROR] Engine {engine} failed: {e}")
                all_results["results_by_engine"][engine] = {"error": str(e)}
        
        logger.info(f"[MULTI_SEARCH] Completed search with {len(engines_to_use)} engines")
        return all_results
    
    def extract_urls_from_results(self, multi_results: Dict[str, Any]) -> List[str]:
        """Extract all unique URLs from multi-engine search results"""
        
        urls = set()
        
        for engine, results in multi_results.get("results_by_engine", {}).items():
            if "error" in results:
                continue
            
            # Google search results
            if "results" in results:
                urls.update([r.get("url") for r in results["results"] if r.get("url")])
            
            # Google Maps business results
            if "businesses" in results:
                urls.update([b.get("url") for b in results["businesses"] if b.get("url")])
            
            # News articles
            if "articles" in results:
                urls.update([a.get("url") for a in results["articles"] if a.get("url")])
            
            # LinkedIn profiles/companies
            if "profiles" in results:
                urls.update([p.get("url") for p in results["profiles"] if p.get("url")])
            if "companies" in results:
                urls.update([c.get("url") for c in results["companies"] if c.get("url")])
            
            # Academic papers
            if "papers" in results:
                urls.update([p.get("url") for p in results["papers"] if p.get("url")])
            
            # Products
            if "products" in results:
                urls.update([p.get("url") for p in results["products"] if p.get("url")])
            
            # Videos
            if "videos" in results:
                urls.update([v.get("url") for v in results["videos"] if v.get("url")])
            
            # Jobs
            if "jobs" in results:
                urls.update([j.get("url") for j in results["jobs"] if j.get("url")])
        
        return list(urls)
    
    def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Legacy single-engine search (for compatibility)"""
        
        results = self.search_engines.search_google(query, num=num_results)
        return [
            SearchResult(
                title=r.get("title", ""),
                link=r.get("url", ""),
                snippet=r.get("snippet", ""),
                position=i + 1
            )
            for i, r in enumerate(results.get("results", []))
        ]
    
    def identify_official_domain(self, results: List[SearchResult], entity: str) -> Optional[str]:
        """Use LLM to identify official website from search results"""
        
        if not results:
            return None
        
        links_str = "\n".join([f"{r.position}. {r.title}\n   {r.link}\n   {r.snippet[:100]}..." 
                               for r in results[:5]])
        
        prompt = f"""
Which of these is the OFFICIAL website for: {entity}

Search Results:
{links_str}

Return JSON:
{{
    "official_url": "the most likely official url",
    "confidence": 0.0-1.0,
    "reasoning": "why you chose this one"
}}
"""
        
        try:
            response = llm_client.complete(prompt, response_format="json", max_tokens=200)
            result = json.loads(response)
            logger.info(f"[OFFICIAL_DOMAIN] {result['official_url']} (confidence: {result['confidence']})")
            return result['official_url']
        except Exception as e:
            logger.warning(f"[DOMAIN_IDENTIFY_ERROR] {e}")
            return results[0].link if results else None


# ============================================================================
# SITE MAPPING
# ============================================================================

class SiteMapper:
    """Map website structure and prioritize pages"""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
    
    def extract_internal_links(self, base_url: str) -> List[Tuple[str, str]]:
        """Extract internal links from homepage"""
        
        try:
            self.rate_limiter.wait_for_domain(base_url)
            
            response = requests.get(base_url, timeout=WebIntelligenceConfig.PAGE_LOAD_TIMEOUT)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                text = a.get_text(strip=True)
                
                # Make absolute URL
                absolute_url = urljoin(base_url, href)
                
                # Only internal links
                if urlparse(absolute_url).netloc == urlparse(base_url).netloc:
                    links.append((absolute_url, text))
            
            logger.info(f"[SITE_MAP] Extracted {len(links)} internal links from {base_url}")
            return links
            
        except Exception as e:
            logger.error(f"[SITE_MAP_ERROR] {e}")
            return []
    
    def prioritize_pages(self, links: List[Tuple[str, str]], task_category: TaskCategory) -> List[str]:
        """Use LLM to prioritize pages based on task"""
        
        if not links:
            return []
        
        links_str = "\n".join([f"{url}: {text}" for url, text in links[:20]])
        
        prompt = f"""
Task Category: {task_category.value}

These are pages from a website. Rank them by relevance for this task.
Return top 5-7 most relevant pages.

Pages:
{links_str}

Return JSON:
{{
    "prioritized_pages": ["url1", "url2", ...],
    "reasoning": "why these are most relevant"
}}
"""
        
        try:
            response = llm_client.complete(prompt, response_format="json", max_tokens=300)
            result = json.loads(response)
            urls = result['prioritized_pages']
            logger.info(f"[PRIORITIZED] {len(urls)} pages for {task_category.value}")
            return urls[:7]
        except Exception as e:
            logger.warning(f"[PRIORITIZE_ERROR] {e}")
            return [url for url, _ in links[:5]]


# ============================================================================
# CONTENT HARVESTING
# ============================================================================

class ContentHarvester:
    """Extract content from multiple pages"""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
    
    def harvest(self, urls: List[str], max_pages: int = 5) -> List[PageContent]:
        """Crawl multiple pages and extract content"""
        
        results = []
        
        for url in urls[:max_pages]:
            try:
                self.rate_limiter.wait_for_domain(url)
                
                logger.info(f"[HARVEST] Crawling: {url}")
                
                scraped = scrape_webpage(url, max_length=WebIntelligenceConfig.MAX_CONTENT_PER_PAGE)
                
                if scraped['success']:
                    page = PageContent(
                        url=url,
                        title=scraped.get('title', ''),
                        content=scraped['content'],
                        extracted_data={},
                        crawled_at=datetime.now().isoformat(),
                        word_count=len(scraped['content'].split())
                    )
                    results.append(page)
                    logger.info(f"[HARVEST] Extracted {page.word_count} words from {url}")
                
            except Exception as e:
                logger.warning(f"[HARVEST_ERROR] {url}: {e}")
        
        return results


# ============================================================================
# INTELLIGENT EXTRACTION (LLM-POWERED)
# ============================================================================

class IntelligenceExtractor:
    """Extract structured information using LLM"""
    
    @staticmethod
    def extract(pages: List[PageContent], query: str, task_category: TaskCategory) -> Dict[str, Any]:
        """Use LLM to extract relevant information from all pages"""
        
        # Combine content (respect token limits)
        combined = ""
        for page in pages:
            combined += f"\n\n--- {page.url} ---\n{page.content[:5000]}"
        
        combined = combined[:WebIntelligenceConfig.MAX_TOTAL_CONTENT]
        
        # Task-specific extraction prompts
        if task_category == TaskCategory.COMPANY_RESEARCH:
            return IntelligenceExtractor._extract_company(combined, query)
        elif task_category == TaskCategory.CONTACT_EXTRACTION:
            return IntelligenceExtractor._extract_contacts(combined)
        else:
            return IntelligenceExtractor._extract_generic(combined, query)
    
    @staticmethod
    def _extract_company(content: str, query: str) -> Dict:
        """Extract company information"""
        
        prompt = f"""
Extract structured company information from this website content.

Query: {query}

Content:
{content}

Return JSON:
{{
    "company_name": "...",
    "description": "2-3 sentence overview",
    "services": ["service1", "service2", ...],
    "industries": ["industry1", ...],
    "locations": [{{"city": "...", "state": "..."}}],
    "contact": {{
        "email": "...",
        "phone": "...",
        "address": "..."
    }},
    "website": "...",
    "key_facts": ["fact1", "fact2", ...],
    "social_media": {{"linkedin": "...", "twitter": "..."}},
    "confidence": 0.0-1.0
}}
"""
        
        try:
            response = llm_client.complete(prompt, response_format="json", max_tokens=800)
            return json.loads(response)
        except Exception as e:
            logger.warning(f"[EXTRACT_ERROR] {e}")
            return {"error": "Failed to extract company data"}
    
    @staticmethod
    def _extract_contacts(content: str) -> Dict:
        """Extract contact information for B2B research"""
        
        prompt = f"""
Extract ALL contact information from this content.

Content:
{content}

Return JSON with array of contacts:
{{
    "contacts": [
        {{
            "name": "...",
            "title": "...",
            "email": "...",
            "phone": "...",
            "department": "...",
            "linkedin": "..."
        }}
    ],
    "business_info": {{
        "company": "...",
        "address": "...",
        "phone": "..."
    }},
    "confidence": 0.0-1.0
}}
"""
        
        try:
            response = llm_client.complete(prompt, response_format="json", max_tokens=1000)
            return json.loads(response)
        except Exception as e:
            logger.warning(f"[EXTRACT_ERROR] {e}")
            return {"error": "Failed to extract contact data", "contacts": []}
    
    @staticmethod
    def _extract_generic(content: str, query: str) -> Dict:
        """Generic extraction for custom tasks"""
        
        prompt = f"""
Extract relevant information from this content based on the query.

Query: {query}

Content:
{content}

Return JSON:
{{
    "key_findings": ["finding1", "finding2", ...],
    "summary": "paragraph summarizing findings",
    "relevant_urls": ["url1", "url2", ...],
    "confidence": 0.0-1.0
}}
"""
        
        try:
            response = llm_client.complete(prompt, response_format="json", max_tokens=800)
            return json.loads(response)
        except Exception as e:
            logger.warning(f"[EXTRACT_ERROR] {e}")
            return {"error": "Failed to extract data"}


# ============================================================================
# WEBHOOK-BASED ASYNC APPROVAL
# ============================================================================

class ApprovalManager:
    """Manage async user approvals via webhook"""
    
    def __init__(self):
        self.pending_approvals = {}  # session_id -> approval_data
    
    def create_approval_request(self, session_id: str, message: str, context: Dict) -> str:
        """
        Create approval request and store for webhook callback.
        Returns webhook token for tracking.
        """
        
        token = f"approve_{uuid.uuid4().hex[:12]}"
        
        self.pending_approvals[token] = {
            'session_id': session_id,
            'message': message,
            'context': context,
            'created_at': datetime.now().isoformat(),
            'approved': None
        }
        
        logger.info(f"[APPROVAL_REQUEST] Token: {token}, Message: {message[:50]}...")
        return token
    
    def handle_approval_webhook(self, token: str, approved: bool) -> Dict:
        """
        Webhook handler for user approval decision.
        Called with: POST /webhook/research/approval?token=xxx&approved=true/false
        """
        
        if token not in self.pending_approvals:
            logger.warning(f"[APPROVAL_WEBHOOK] Unknown token: {token}")
            return {"error": "Invalid token"}
        
        approval = self.pending_approvals[token]
        approval['approved'] = approved
        approval['approved_at'] = datetime.now().isoformat()
        
        logger.info(f"[APPROVAL_WEBHOOK] Token: {token}, Approved: {approved}")
        
        return {
            "token": token,
            "approved": approved,
            "session_id": approval['session_id'],
            "message": f"Research {'deepened' if approved else 'stopped'}"
        }
    
    def check_approval(self, token: str) -> Optional[bool]:
        """Check if approval decision has been made"""
        
        if token not in self.pending_approvals:
            return None
        
        return self.pending_approvals[token].get('approved')


# ============================================================================
# MAIN ENGINE
# ============================================================================

class WebIntelligenceEngine:
    """
    Main intelligent web research engine.
    Flexible, no-template approach to web research.
    """
    
    def __init__(self):
        self.cache = FirebaseResearchCache()
        self.rate_limiter = RateLimiter()
        self.discovery = WebDiscovery(self.rate_limiter)
        self.mapper = SiteMapper(self.rate_limiter)
        self.harvester = ContentHarvester(self.rate_limiter)
        self.extractor = IntelligenceExtractor()
        self.approval_manager = ApprovalManager()
    
    def research(self, query: str, initial_depth: str = "standard", session_id: str = None) -> Dict[str, Any]:
        """
        Main entry point for web research.
        
        Args:
            query: What to research (free-form)
            initial_depth: "quick", "standard", or "comprehensive"
            session_id: Session ID for tracking
        
        Returns:
            Comprehensive research report
        """
        
        logger.info(f"[RESEARCH_START] Query: {query}, Depth: {initial_depth}")
        start_time = time.time()
        
        # Check cache first
        cached = self.cache.get(query)
        if cached:
            logger.info(f"[RESEARCH] Using cached result")
            return cached
        
        # Step 1: Understand task
        task_category, task_params = TaskIntelligence.understand_task(query)
        logger.info(f"[TASK] Category: {task_category.value}")
        
        # Step 2: Search
        search_results = self.discovery.search(task_params['target_entity'])
        if not search_results:
            return {"error": "No search results found"}
        
        # Step 3: Identify official domain
        official_url = self.discovery.identify_official_domain(search_results, task_params['target_entity'])
        if not official_url:
            official_url = search_results[0].link
        
        logger.info(f"[OFFICIAL_DOMAIN] {official_url}")
        
        # Step 4: Map site
        links = self.mapper.extract_internal_links(official_url)
        priority_pages = self.mapper.prioritize_pages(links, task_category)
        
        # Step 5: Harvest content (initial depth)
        depth_enum = ResearchDepth[initial_depth.upper()]
        max_pages, time_limit = WebIntelligenceConfig.CRAWL_LIMITS[depth_enum]
        
        pages_to_crawl = priority_pages[:max_pages]
        harvested_pages = self.harvester.harvest(pages_to_crawl, max_pages=max_pages)
        
        time_elapsed = time.time() - start_time
        
        # Step 6: Extract intelligence
        findings = self.extractor.extract(harvested_pages, query, task_category)
        
        # Step 7: Prepare result
        result = {
            "query": query,
            "task_category": task_category.value,
            "status": "complete",
            "findings": findings,
            "metadata": {
                "pages_crawled": len(harvested_pages),
                "time_seconds": round(time_elapsed, 1),
                "confidence": findings.get('confidence', 0.8),
                "official_domain": official_url,
                "depth": initial_depth,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Step 8: Cache result
        self.cache.set(query, result)
        
        # Step 9: Check if should ask for deeper dive
        can_go_deeper = (
            time_elapsed < 30 and 
            len(harvested_pages) < 10 and 
            initial_depth != "comprehensive"
        )
        
        if can_go_deeper and session_id:
            approval_token = self.approval_manager.create_approval_request(
                session_id,
                f"Found {len(harvested_pages)} pages. Go deeper? (+60s for comprehensive research)",
                result
            )
            result['approval_token'] = approval_token
            result['can_deepen'] = True
            result['webhook_url'] = f"/webhook/research/approval?token={approval_token}&approved={{true|false}}"
        
        logger.info(f"[RESEARCH_COMPLETE] {len(harvested_pages)} pages, {time_elapsed:.1f}s")
        return result
    
    def deepen_research(self, query: str, session_id: str) -> Dict[str, Any]:
        """Deepen research from standard to comprehensive"""
        logger.info(f"[DEEPEN_RESEARCH] Query: {query}")
        return self.research(query, "comprehensive", session_id)


# ============================================================================
# TOOL REGISTRATION
# ============================================================================

engine = WebIntelligenceEngine()

def web_research(query: str, depth: str = "standard", session_id: str = None) -> Dict[str, Any]:
    """
    Intelligent web research tool.
    
    Entry point for the web intelligence engine.
    Handles discovery, crawling, extraction, and synthesis.
    """
    return engine.research(query, depth, session_id)


# Register with tool registry
tool_registry.register(
    'web_research',
    web_research,
    description="Intelligent web research - discovers, crawls, extracts, and synthesizes information about any entity or topic. Includes Firebase caching and progressive depth with async approval."
)

logger.info("[ENGINE_READY] Web Intelligence Engine initialized with Firebase caching")

