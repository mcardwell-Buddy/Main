"""
SEARCH ENGINES REGISTRY
=======================

Unified wrapper for SerpAPI engines. Each engine is a composable capability
that can be used independently or combined into higher-level tools.

Supported Engines:
- google_search: General web search
- google_maps: Local business data, addresses, phone, hours
- google_news: News articles, sentiment, trending topics
- linkedin_search: People, companies, professionals
- google_scholar: Academic papers, citations, research
- google_shopping: Product listings, prices, reviews
- youtube_search: Videos, channels, transcripts
- google_trends: Trend analysis, popularity over time
- amazon_search: Product data, reviews, ratings
- google_jobs: Job listings, requirements, companies

Philosophy: Each engine returns normalized results. Tools compose engines.
"""

import logging
import requests
from typing import Dict, List, Optional, Any
from backend.config import Config

logger = logging.getLogger(__name__)


class SearchEnginesRegistry:
    """Unified interface to SerpAPI engines"""
    
    def __init__(self):
        self.api_key = Config.API_KEYS.get('SERPAPI')
        self.base_url = "https://serpapi.com/search"
        
        if not self.api_key:
            logger.warning("[SEARCH_ENGINES] SerpAPI key not configured")
    
    def search_google(self, query: str, num: int = 10, safe: str = "on") -> Dict[str, Any]:
        """
        General Google search - broadest coverage
        Returns: organic results, knowledge graph, related searches
        """
        try:
            params = {
                "api_key": self.api_key,
                "engine": "google",
                "q": query,
                "num": num,
                "safe": safe
            }
            
            response = requests.get(self.base_url, params=params, timeout=15)
            data = response.json()
            
            results = {
                "engine": "google",
                "query": query,
                "results": [],
                "knowledge_graph": None,
                "related_searches": []
            }
            
            # Organic results
            if "organic_results" in data:
                results["results"] = [
                    {
                        "title": r.get("title"),
                        "url": r.get("link"),
                        "snippet": r.get("snippet"),
                        "position": r.get("position")
                    }
                    for r in data["organic_results"][:num]
                ]
            
            # Knowledge graph
            if "knowledge_graph" in data:
                results["knowledge_graph"] = data["knowledge_graph"]
            
            # Related searches
            if "related_searches" in data:
                results["related_searches"] = [
                    r.get("query") for r in data["related_searches"]
                ]
            
            logger.info(f"[GOOGLE_SEARCH] Found {len(results['results'])} results for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"[GOOGLE_SEARCH_ERROR] {e}")
            return {"error": str(e), "engine": "google"}
    
    def search_google_maps(self, query: str, location: Optional[str] = None, num: int = 10) -> Dict[str, Any]:
        """
        Google Maps / Local search - business info, addresses, phones, hours
        Returns: business listings with contact info
        """
        try:
            params = {
                "api_key": self.api_key,
                "engine": "google_maps",
                "q": query,
                "num": num
            }
            if location:
                params["location"] = location
            
            response = requests.get(self.base_url, params=params, timeout=15)
            data = response.json()
            
            results = {
                "engine": "google_maps",
                "query": query,
                "location": location,
                "businesses": []
            }
            
            # Extract place results
            if "place_results" in data:
                results["businesses"] = [
                    {
                        "name": p.get("title"),
                        "address": p.get("address"),
                        "phone": p.get("phone"),
                        "website": p.get("website"),
                        "rating": p.get("rating"),
                        "review_count": p.get("review_count"),
                        "hours": p.get("hours"),
                        "type": p.get("type"),
                        "url": p.get("link")
                    }
                    for p in data["place_results"][:num]
                ]
            
            logger.info(f"[GOOGLE_MAPS] Found {len(results['businesses'])} businesses for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"[GOOGLE_MAPS_ERROR] {e}")
            return {"error": str(e), "engine": "google_maps"}
    
    def search_google_news(self, query: str, num: int = 10) -> Dict[str, Any]:
        """
        Google News - news articles, sentiment, trending
        Returns: news articles with dates and sources
        """
        try:
            params = {
                "api_key": self.api_key,
                "engine": "google_news",
                "q": query,
                "num": num
            }
            
            response = requests.get(self.base_url, params=params, timeout=15)
            data = response.json()
            
            results = {
                "engine": "google_news",
                "query": query,
                "articles": [],
                "top_story": None
            }
            
            # News results
            if "news_results" in data:
                results["articles"] = [
                    {
                        "title": r.get("title"),
                        "source": r.get("source"),
                        "date": r.get("date"),
                        "snippet": r.get("snippet"),
                        "url": r.get("link")
                    }
                    for r in data["news_results"][:num]
                ]
            
            # Top story
            if "top_story" in data:
                results["top_story"] = data["top_story"]
            
            logger.info(f"[GOOGLE_NEWS] Found {len(results['articles'])} articles for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"[GOOGLE_NEWS_ERROR] {e}")
            return {"error": str(e), "engine": "google_news"}
    
    def search_linkedin(self, query: str, search_type: str = "all", num: int = 10) -> Dict[str, Any]:
        """
        LinkedIn Search - people, companies, posts
        Returns: profiles and companies with details
        """
        try:
            params = {
                "api_key": self.api_key,
                "engine": "linkedin",
                "q": query,
                "num": num
            }
            
            response = requests.get(self.base_url, params=params, timeout=15)
            data = response.json()
            
            results = {
                "engine": "linkedin",
                "query": query,
                "search_type": search_type,
                "profiles": [],
                "companies": [],
                "posts": []
            }
            
            # Profile results (people)
            if "profiles" in data:
                results["profiles"] = [
                    {
                        "name": p.get("name"),
                        "title": p.get("title"),
                        "company": p.get("company"),
                        "location": p.get("location"),
                        "url": p.get("link"),
                        "summary": p.get("summary")
                    }
                    for p in data["profiles"][:num]
                ]
            
            # Company results
            if "companies" in data:
                results["companies"] = [
                    {
                        "name": c.get("name"),
                        "industry": c.get("industry"),
                        "website": c.get("website"),
                        "location": c.get("location"),
                        "employees": c.get("employee_count"),
                        "url": c.get("link")
                    }
                    for c in data["companies"][:num]
                ]
            
            logger.info(f"[LINKEDIN_SEARCH] Found {len(results['profiles'])} profiles, {len(results['companies'])} companies")
            return results
            
        except Exception as e:
            logger.error(f"[LINKEDIN_SEARCH_ERROR] {e}")
            return {"error": str(e), "engine": "linkedin"}
    
    def search_google_scholar(self, query: str, num: int = 10) -> Dict[str, Any]:
        """
        Google Scholar - academic papers, citations, research
        Returns: papers with author, citation count, abstract
        """
        try:
            params = {
                "api_key": self.api_key,
                "engine": "google_scholar",
                "q": query,
                "num": num
            }
            
            response = requests.get(self.base_url, params=params, timeout=15)
            data = response.json()
            
            results = {
                "engine": "google_scholar",
                "query": query,
                "papers": []
            }
            
            # Organic results (papers)
            if "organic_results" in data:
                results["papers"] = [
                    {
                        "title": r.get("title"),
                        "authors": r.get("publication_info", {}).get("authors"),
                        "publication": r.get("publication_info", {}).get("publication"),
                        "year": r.get("publication_info", {}).get("year"),
                        "citations": r.get("inline_links", {}).get("cited_by", {}).get("total"),
                        "abstract": r.get("snippet"),
                        "url": r.get("link")
                    }
                    for r in data["organic_results"][:num]
                ]
            
            logger.info(f"[GOOGLE_SCHOLAR] Found {len(results['papers'])} papers for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"[GOOGLE_SCHOLAR_ERROR] {e}")
            return {"error": str(e), "engine": "google_scholar"}
    
    def search_google_shopping(self, query: str, num: int = 10) -> Dict[str, Any]:
        """
        Google Shopping - products, prices, reviews
        Returns: product listings with pricing
        """
        try:
            params = {
                "api_key": self.api_key,
                "engine": "google_shopping",
                "q": query,
                "num": num
            }
            
            response = requests.get(self.base_url, params=params, timeout=15)
            data = response.json()
            
            results = {
                "engine": "google_shopping",
                "query": query,
                "products": []
            }
            
            # Shopping results
            if "shopping_results" in data:
                results["products"] = [
                    {
                        "title": p.get("title"),
                        "price": p.get("price"),
                        "original_price": p.get("original_price"),
                        "rating": p.get("rating"),
                        "review_count": p.get("reviews"),
                        "source": p.get("source"),
                        "url": p.get("link")
                    }
                    for p in data["shopping_results"][:num]
                ]
            
            logger.info(f"[GOOGLE_SHOPPING] Found {len(results['products'])} products for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"[GOOGLE_SHOPPING_ERROR] {e}")
            return {"error": str(e), "engine": "google_shopping"}
    
    def search_youtube(self, query: str, num: int = 10) -> Dict[str, Any]:
        """
        YouTube Search - videos, channels
        Returns: video results with view counts
        """
        try:
            params = {
                "api_key": self.api_key,
                "engine": "youtube",
                "search_query": query,
                "num": num
            }
            
            response = requests.get(self.base_url, params=params, timeout=15)
            data = response.json()
            
            results = {
                "engine": "youtube",
                "query": query,
                "videos": []
            }
            
            # Video results
            if "video_results" in data:
                results["videos"] = [
                    {
                        "title": v.get("title"),
                        "channel": v.get("channel"),
                        "views": v.get("views"),
                        "duration": v.get("duration"),
                        "upload_date": v.get("upload_date"),
                        "url": v.get("link")
                    }
                    for v in data["video_results"][:num]
                ]
            
            logger.info(f"[YOUTUBE_SEARCH] Found {len(results['videos'])} videos for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"[YOUTUBE_SEARCH_ERROR] {e}")
            return {"error": str(e), "engine": "youtube"}
    
    def search_google_trends(self, query: str) -> Dict[str, Any]:
        """
        Google Trends - trend analysis, popularity over time
        Returns: trend data and related queries
        """
        try:
            params = {
                "api_key": self.api_key,
                "engine": "google_trends",
                "q": query
            }
            
            response = requests.get(self.base_url, params=params, timeout=15)
            data = response.json()
            
            results = {
                "engine": "google_trends",
                "query": query,
                "interest": None,
                "related": []
            }
            
            # Interest data
            if "interest_by_time" in data:
                results["interest"] = data["interest_by_time"]
            
            # Related queries
            if "related_queries" in data:
                results["related"] = data["related_queries"]
            
            logger.info(f"[GOOGLE_TRENDS] Retrieved trend data for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"[GOOGLE_TRENDS_ERROR] {e}")
            return {"error": str(e), "engine": "google_trends"}
    
    def search_amazon(self, query: str, num: int = 10) -> Dict[str, Any]:
        """
        Amazon Search - products, prices, reviews
        Returns: product listings from Amazon
        """
        try:
            params = {
                "api_key": self.api_key,
                "engine": "amazon",
                "q": query,
                "num": num
            }
            
            response = requests.get(self.base_url, params=params, timeout=15)
            data = response.json()
            
            results = {
                "engine": "amazon",
                "query": query,
                "products": []
            }
            
            # Product results
            if "organic_results" in data:
                results["products"] = [
                    {
                        "title": p.get("title"),
                        "asin": p.get("asin"),
                        "price": p.get("price"),
                        "rating": p.get("rating"),
                        "review_count": p.get("review_count"),
                        "prime": p.get("prime", False),
                        "url": p.get("link")
                    }
                    for p in data["organic_results"][:num]
                ]
            
            logger.info(f"[AMAZON_SEARCH] Found {len(results['products'])} products for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"[AMAZON_SEARCH_ERROR] {e}")
            return {"error": str(e), "engine": "amazon"}
    
    def search_google_jobs(self, query: str, location: Optional[str] = None, num: int = 10) -> Dict[str, Any]:
        """
        Google Jobs - job listings, requirements, companies
        Returns: job postings with details
        """
        try:
            params = {
                "api_key": self.api_key,
                "engine": "google_jobs",
                "q": query,
                "num": num
            }
            if location:
                params["location"] = location
            
            response = requests.get(self.base_url, params=params, timeout=15)
            data = response.json()
            
            results = {
                "engine": "google_jobs",
                "query": query,
                "location": location,
                "jobs": []
            }
            
            # Job results
            if "jobs_results" in data:
                results["jobs"] = [
                    {
                        "title": j.get("title"),
                        "company": j.get("company_name"),
                        "location": j.get("location"),
                        "salary": j.get("salary"),
                        "description": j.get("description"),
                        "job_type": j.get("job_type"),
                        "url": j.get("link")
                    }
                    for j in data["jobs_results"][:num]
                ]
            
            logger.info(f"[GOOGLE_JOBS] Found {len(results['jobs'])} jobs for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"[GOOGLE_JOBS_ERROR] {e}")
            return {"error": str(e), "engine": "google_jobs"}


# Global instance
search_engines = SearchEnginesRegistry()
