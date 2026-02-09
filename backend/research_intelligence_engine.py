"""
RESEARCH INTELLIGENCE ENGINE
=============================

Complete multi-step research system that orchestrates intelligent
web research across multiple SerpAPI engines with:
- Task decomposition & planning
- Persistent research sessions
- Multi-source deduplication
- Confidence scoring & validation
- Adaptive completeness detection
- Structured output generation
- Full audit trails

This is Buddy's perception layer - the foundation for all
intelligent decision-making.
"""

import logging
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime, timedelta
from uuid import uuid4
from collections import defaultdict

from backend.config import Config
from backend.llm_client import llm_client
from backend.search_engines_registry import search_engines

logger = logging.getLogger(__name__)

# Will import after class definitions to avoid circular imports
research_feedback_loop = None


# ============================================================================
# ENUMS & DATA MODELS
# ============================================================================

class ResearchTaskType(Enum):
    """High-level research task categories"""
    COMPANY_RESEARCH = "company"
    CONTACT_EXTRACTION = "contacts"
    COMPETITOR_ANALYSIS = "competitor"
    PRICING_RESEARCH = "pricing"
    MARKET_RESEARCH = "market"
    EMPLOYMENT_RESEARCH = "employment"
    ACADEMIC_RESEARCH = "academic"
    PRODUCT_RESEARCH = "product"
    SOCIAL_INTELLIGENCE = "social"
    NEWS_MONITORING = "news"
    CUSTOM = "custom"


@dataclass
class DataPoint:
    """A single extracted data point"""
    value: str
    data_type: str  # "phone", "email", "name", "company", etc.
    source: str  # engine name
    confidence: float  # 0.0-1.0
    extracted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    url: Optional[str] = None
    raw_context: Optional[str] = None


@dataclass
class DeduplicatedEntity:
    """Merged result from multiple sources"""
    canonical_value: str
    data_type: str
    sources: List[Tuple[str, float]] = field(default_factory=list)  # (source, confidence)
    confidence: float = 0.0  # Average of sources
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_source(self, source: str, confidence: float):
        """Add a source and recalculate confidence"""
        self.sources.append((source, confidence))
        # Weighted average
        total_confidence = sum(c for _, c in self.sources)
        self.confidence = total_confidence / len(self.sources)


@dataclass
class ResearchTask:
    """Single research sub-task"""
    task_id: str
    description: str
    task_type: 'ResearchTaskType'
    required_engines: List[str]
    fallback_engines: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, in_progress, complete, failed
    results: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class ResearchSession:
    """Active research session"""
    session_id: str
    original_query: str
    task_type: 'ResearchTaskType'
    tasks: Dict[str, ResearchTask] = field(default_factory=dict)
    findings: Dict[str, List[DataPoint]] = field(default_factory=lambda: defaultdict(list))
    deduped_findings: Dict[str, List[DeduplicatedEntity]] = field(default_factory=lambda: defaultdict(list))
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    is_complete: bool = False
    completeness_score: float = 0.0
    suggested_follow_ups: List[str] = field(default_factory=list)


# ============================================================================
# INTENT CLASSIFIER
# ============================================================================

class IntentClassifier:
    """Classifies user requests into research task types"""
    
    @staticmethod
    def classify(query: str) -> Tuple[ResearchTaskType, Dict[str, Any]]:
        """Classify query intent and extract parameters"""
        query_lower = query.lower()
        
        # Company research patterns
        if any(p in query_lower for p in ["tell me about", "company overview", "about company", "profile of"]):
            return ResearchTaskType.COMPANY_RESEARCH, {"entity": query}
        
        # Contact extraction
        if any(p in query_lower for p in ["find contacts", "email", "phone", "team members", "employees"]):
            return ResearchTaskType.CONTACT_EXTRACTION, {"entity": query}
        
        # Competitor analysis
        if any(p in query_lower for p in ["competitors", "competitive", "vs", "versus", "compare"]):
            return ResearchTaskType.COMPETITOR_ANALYSIS, {"entity": query}
        
        # Pricing research
        if any(p in query_lower for p in ["pricing", "price", "cost", "rates", "fees", "charges"]):
            return ResearchTaskType.PRICING_RESEARCH, {"entity": query}
        
        # Market research
        if any(p in query_lower for p in ["market research", "market analysis", "industry trends", "market size"]):
            return ResearchTaskType.MARKET_RESEARCH, {"entity": query}
        
        # Job/employment
        if any(p in query_lower for p in ["jobs", "careers", "hiring", "openings", "employment"]):
            return ResearchTaskType.EMPLOYMENT_RESEARCH, {"entity": query}
        
        # Academic
        if any(p in query_lower for p in ["research paper", "academic", "study", "thesis", "citation"]):
            return ResearchTaskType.ACADEMIC_RESEARCH, {"entity": query}
        
        # Product research
        if any(p in query_lower for p in ["product", "features", "specifications", "reviews"]):
            return ResearchTaskType.PRODUCT_RESEARCH, {"entity": query}
        
        # Social/news
        if any(p in query_lower for p in ["news", "social", "trending", "mentioned", "posted"]):
            return ResearchTaskType.NEWS_MONITORING, {"entity": query}
        
        # Default
        return ResearchTaskType.CUSTOM, {"entity": query}


# ============================================================================
# TASK DECOMPOSER
# ============================================================================

class TaskDecomposer:
    """Breaks complex requests into sub-tasks"""
    
    @staticmethod
    def decompose(original_query: str, task_type: ResearchTaskType) -> List[ResearchTask]:
        """Decompose a research request into concrete sub-tasks"""
        tasks = []
        
        if task_type == ResearchTaskType.COMPANY_RESEARCH:
            tasks.extend([
                ResearchTask(
                    task_id="t1_company_search",
                    description="Find company basic information",
                    task_type=task_type,
                    required_engines=["google"],
                    fallback_engines=["google_maps"],
                    dependencies=[]
                ),
                ResearchTask(
                    task_id="t2_company_local",
                    description="Find local business info (address, phone)",
                    task_type=task_type,
                    required_engines=["google_maps"],
                    fallback_engines=["google"],
                    dependencies=["t1_company_search"]
                ),
                ResearchTask(
                    task_id="t3_company_news",
                    description="Find recent news about company",
                    task_type=task_type,
                    required_engines=["google_news"],
                    fallback_engines=[],
                    dependencies=["t1_company_search"]
                ),
            ])
        
        elif task_type == ResearchTaskType.CONTACT_EXTRACTION:
            tasks.extend([
                ResearchTask(
                    task_id="t1_web_contacts",
                    description="Search for contacts on web",
                    task_type=task_type,
                    required_engines=["google"],
                    fallback_engines=[],
                    dependencies=[]
                ),
                ResearchTask(
                    task_id="t2_linkedin_contacts",
                    description="Find profiles on LinkedIn",
                    task_type=task_type,
                    required_engines=["linkedin"],
                    fallback_engines=[],
                    dependencies=["t1_web_contacts"]
                ),
                ResearchTask(
                    task_id="t3_business_contacts",
                    description="Extract official business contact info",
                    task_type=task_type,
                    required_engines=["google_maps"],
                    fallback_engines=[],
                    dependencies=["t1_web_contacts"]
                ),
            ])
        
        elif task_type == ResearchTaskType.COMPETITOR_ANALYSIS:
            tasks.extend([
                ResearchTask(
                    task_id="t1_competitor_search",
                    description="Find competitor companies",
                    task_type=task_type,
                    required_engines=["google"],
                    fallback_engines=[],
                    dependencies=[]
                ),
                ResearchTask(
                    task_id="t2_competitor_news",
                    description="Find competitor news and activity",
                    task_type=task_type,
                    required_engines=["google_news"],
                    fallback_engines=[],
                    dependencies=["t1_competitor_search"]
                ),
                ResearchTask(
                    task_id="t3_competitor_pricing",
                    description="Find competitor pricing/products",
                    task_type=task_type,
                    required_engines=["google_shopping"],
                    fallback_engines=["amazon"],
                    dependencies=["t1_competitor_search"]
                ),
                ResearchTask(
                    task_id="t4_market_trends",
                    description="Analyze market trends",
                    task_type=task_type,
                    required_engines=["google_trends"],
                    fallback_engines=[],
                    dependencies=["t1_competitor_search"]
                ),
            ])
        
        elif task_type == ResearchTaskType.PRICING_RESEARCH:
            tasks.extend([
                ResearchTask(
                    task_id="t1_google_shopping",
                    description="Find pricing on Google Shopping",
                    task_type=task_type,
                    required_engines=["google_shopping"],
                    fallback_engines=[],
                    dependencies=[]
                ),
                ResearchTask(
                    task_id="t2_amazon_pricing",
                    description="Find pricing on Amazon",
                    task_type=task_type,
                    required_engines=["amazon"],
                    fallback_engines=[],
                    dependencies=[]
                ),
                ResearchTask(
                    task_id="t3_reviews",
                    description="Find reviews and ratings",
                    task_type=task_type,
                    required_engines=["google"],
                    fallback_engines=[],
                    dependencies=["t1_google_shopping", "t2_amazon_pricing"]
                ),
            ])
        
        elif task_type == ResearchTaskType.EMPLOYMENT_RESEARCH:
            tasks.extend([
                ResearchTask(
                    task_id="t1_job_search",
                    description="Find job listings",
                    task_type=task_type,
                    required_engines=["google_jobs"],
                    fallback_engines=["google"],
                    dependencies=[]
                ),
                ResearchTask(
                    task_id="t2_linkedin_jobs",
                    description="Find LinkedIn job postings",
                    task_type=task_type,
                    required_engines=["linkedin"],
                    fallback_engines=[],
                    dependencies=["t1_job_search"]
                ),
            ])
        
        elif task_type == ResearchTaskType.ACADEMIC_RESEARCH:
            tasks.extend([
                ResearchTask(
                    task_id="t1_scholar",
                    description="Find academic papers",
                    task_type=task_type,
                    required_engines=["google_scholar"],
                    fallback_engines=[],
                    dependencies=[]
                ),
                ResearchTask(
                    task_id="t2_news",
                    description="Find related news/discussion",
                    task_type=task_type,
                    required_engines=["google_news"],
                    fallback_engines=[],
                    dependencies=["t1_scholar"]
                ),
            ])
        
        else:
            tasks.append(ResearchTask(
                task_id="t1_generic_search",
                description="Search for information",
                task_type=task_type,
                required_engines=["google"],
                fallback_engines=["google_maps"],
                dependencies=[]
            ))
        
        return tasks


# ============================================================================
# RESULT DEDUPLICATOR
# ============================================================================

class ResultDeduplicator:
    """Merges duplicate results from multiple sources"""
    
    @staticmethod
    def normalize_email(email: str) -> str:
        """Normalize email for comparison"""
        return email.lower().strip()
    
    @staticmethod
    def normalize_phone(phone: str) -> str:
        """Normalize phone for comparison"""
        normalized = ''.join(c for c in phone if c.isdigit() or c == '+')
        return normalized
    
    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize person name for comparison"""
        return ' '.join(name.lower().split())
    
    @staticmethod
    def dedupe_data_points(data_points: List[DataPoint]) -> List[DeduplicatedEntity]:
        """Merge duplicate data points from multiple sources"""
        by_type = defaultdict(list)
        
        # Group by data type
        for point in data_points:
            by_type[point.data_type].append(point)
        
        deduplicated = []
        
        for data_type, points in by_type.items():
            if not points:
                continue
            
            # Normalize and group
            groups = defaultdict(list)
            
            for point in points:
                if data_type == "email":
                    key = ResultDeduplicator.normalize_email(point.value)
                elif data_type == "phone":
                    key = ResultDeduplicator.normalize_phone(point.value)
                elif data_type == "name":
                    key = ResultDeduplicator.normalize_name(point.value)
                else:
                    key = point.value.lower().strip()
                
                groups[key].append(point)
            
            # Create deduplicated entities
            for canonical, group in groups.items():
                entity = DeduplicatedEntity(
                    canonical_value=group[0].value,
                    data_type=data_type
                )
                
                for point in group:
                    entity.add_source(point.source, point.confidence)
                
                deduplicated.append(entity)
        
        return deduplicated


# ============================================================================
# COMPLETENESS ANALYZER
# ============================================================================

class CompletenessAnalyzer:
    """Analyzes if research findings are complete"""
    
    @staticmethod
    def analyze(session: ResearchSession) -> Tuple[float, List[str]]:
        """Analyze completeness of research findings"""
        score = 0.0
        follow_ups = []
        
        # Check data coverage
        total_fields = len(session.deduped_findings)
        if total_fields == 0:
            return 0.0, ["Need to gather more information"]
        
        # Check confidence
        confidences = []
        for entities in session.deduped_findings.values():
            if entities:
                confidences.append(max(e.confidence for e in entities))
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        score = min(1.0, avg_confidence)
        
        # Suggest follow-ups if incomplete
        if score < 0.8:
            if session.task_type == ResearchTaskType.COMPANY_RESEARCH:
                follow_ups.append("Want me to find news about this company?")
                follow_ups.append("Should I look up their competitors?")
            elif session.task_type == ResearchTaskType.CONTACT_EXTRACTION:
                follow_ups.append("Want me to search for more team members?")
                follow_ups.append("Should I find LinkedIn profiles?")
        
        return score, follow_ups


# ============================================================================
# STRUCTURED OUTPUT GENERATOR
# ============================================================================

class StructuredOutputGenerator:
    """Generates structured output from findings"""
    
    @staticmethod
    def generate(session: ResearchSession) -> Dict[str, Any]:
        """Generate structured output from research findings"""
        output = {
            "session_id": session.session_id,
            "original_query": session.original_query,
            "task_type": session.task_type.value,
            "generated_at": datetime.utcnow().isoformat(),
            "completeness_score": round(session.completeness_score, 2),
            "findings": {},
            "audit_trail": []
        }
        
        # Organize findings by type
        for field_name, entities in session.deduped_findings.items():
            output["findings"][field_name] = [
                {
                    "value": e.canonical_value,
                    "confidence": round(e.confidence, 2),
                    "sources": [{"engine": s[0], "confidence": round(s[1], 2)} for s in e.sources],
                    "metadata": e.metadata
                }
                for e in entities
            ]
        
        # Add audit trail
        for task_id, task in session.tasks.items():
            output["audit_trail"].append({
                "task": task.description,
                "engines_used": task.required_engines,
                "status": task.status,
                "error": task.error
            })
        
        # Add suggested follow-ups
        if session.suggested_follow_ups:
            output["suggested_follow_ups"] = session.suggested_follow_ups
        
        return output


# ============================================================================
# RESEARCH INTELLIGENCE ENGINE (Main Orchestrator)
# ============================================================================

class ResearchIntelligenceEngine:
    """Main orchestrator for multi-step intelligent research"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.task_decomposer = TaskDecomposer()
        self.deduplicator = ResultDeduplicator()
        self.completeness_analyzer = CompletenessAnalyzer()
        self.output_generator = StructuredOutputGenerator()
        self.active_sessions: Dict[str, ResearchSession] = {}
    
    def research(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute complete research workflow"""
        
        # Step 1: Create or get session
        if not session_id:
            session_id = f"research_{uuid4().hex[:8]}"
        
        # Step 2: Classify intent
        task_type, params = self.intent_classifier.classify(query)
        logger.info(f"[RESEARCH] Task type: {task_type.value}")
        
        # Step 3: Create session
        session = ResearchSession(
            session_id=session_id,
            original_query=query,
            task_type=task_type,
            context=params
        )
        self.active_sessions[session_id] = session
        
        # Step 4: Decompose into sub-tasks
        tasks = self.task_decomposer.decompose(query, task_type)
        for task in tasks:
            session.tasks[task.task_id] = task
        
        logger.info(f"[RESEARCH] Decomposed into {len(tasks)} tasks")
        
        # Step 5: Execute tasks in dependency order
        executed = set()
        
        while len(executed) < len(tasks):
            # Find executable tasks (dependencies met)
            executable = [
                t for t_id, t in session.tasks.items()
                if t_id not in executed and 
                   all(dep in executed for dep in t.dependencies)
            ]
            
            if not executable:
                break
            
            # Execute tasks
            for task in executable:
                self._execute_task(task, session)
                executed.add(task.task_id)
        
        # Step 6: Deduplicate findings
        all_points = []
        for data_points in session.findings.values():
            all_points.extend(data_points)
        
        deduped = self.deduplicator.dedupe_data_points(all_points)
        
        # Reorganize by type
        for entity in deduped:
            if entity.data_type not in session.deduped_findings:
                session.deduped_findings[entity.data_type] = []
            session.deduped_findings[entity.data_type].append(entity)
        
        # Step 7: Analyze completeness
        completeness_score, follow_ups = self.completeness_analyzer.analyze(session)
        session.completeness_score = completeness_score
        session.suggested_follow_ups = follow_ups
        session.is_complete = completeness_score > 0.7
        session.last_updated = datetime.utcnow().isoformat()
        
        # Step 8: Generate structured output
        output = self.output_generator.generate(session)
        
        logger.info(f"[RESEARCH] Complete. Score: {completeness_score:.2f}")
        
        # Step 9: Emit learning signals via feedback loop
        try:
            from backend.research_feedback_loop import research_feedback_loop
            feedback_result = research_feedback_loop.process_research_session(output)
            logger.info(f"[RESEARCH_LEARNING] Feedback processed: {feedback_result['signals_generated']} signals generated")
        except Exception as e:
            logger.warning(f"[RESEARCH_LEARNING] Feedback loop failed (non-blocking): {e}")
        
        return output
    
    def _execute_task(self, task: ResearchTask, session: ResearchSession) -> None:
        """Execute a single research task"""
        task.status = "in_progress"
        
        try:
            # Select engines
            engines = task.required_engines + task.fallback_engines
            
            # Execute each engine
            for engine in engines:
                try:
                    results = self._search_with_engine(
                        engine, 
                        session.context.get("entity", session.original_query)
                    )
                    
                    # Extract data points
                    data_points = self._extract_data_points(results, engine)
                    
                    # Store findings
                    for point in data_points:
                        if point.data_type not in session.findings:
                            session.findings[point.data_type] = []
                        session.findings[point.data_type].append(point)
                    
                    if data_points:
                        task.results[engine] = len(data_points)
                        break  # Success, move to next task
                
                except Exception as e:
                    logger.warning(f"[TASK] Engine {engine} failed: {e}")
                    continue
            
            task.status = "complete"
            
        except Exception as e:
            logger.error(f"[TASK] Failed: {e}")
            task.status = "failed"
            task.error = str(e)
    
    def _search_with_engine(self, engine: str, query: str) -> Dict[str, Any]:
        """Execute search with a specific engine"""
        
        if engine == "google":
            return search_engines.search_google(query)
        elif engine == "google_maps":
            return search_engines.search_google_maps(query)
        elif engine == "google_news":
            return search_engines.search_google_news(query)
        elif engine == "linkedin":
            return search_engines.search_linkedin(query)
        elif engine == "google_scholar":
            return search_engines.search_google_scholar(query)
        elif engine == "google_shopping":
            return search_engines.search_google_shopping(query)
        elif engine == "youtube":
            return search_engines.search_youtube(query)
        elif engine == "google_trends":
            return search_engines.search_google_trends(query)
        elif engine == "amazon":
            return search_engines.search_amazon(query)
        elif engine == "google_jobs":
            return search_engines.search_google_jobs(query)
        else:
            raise ValueError(f"Unknown engine: {engine}")
    
    def _extract_data_points(self, results: Dict[str, Any], engine: str) -> List[DataPoint]:
        """Extract structured data points from engine results"""
        points = []
        
        if "error" in results:
            return []
        
        try:
            if engine == "google":
                if "results" in results:
                    for r in results["results"][:5]:
                        if r.get("title"):
                            points.append(DataPoint(
                                value=r.get("title", ""),
                                data_type="reference",
                                source=engine,
                                confidence=0.7,
                                url=r.get("url")
                            ))
            
            elif engine == "google_maps":
                if "businesses" in results:
                    for b in results["businesses"][:5]:
                        if b.get("phone"):
                            points.append(DataPoint(
                                value=b.get("phone"),
                                data_type="phone",
                                source=engine,
                                confidence=0.95,
                                url=b.get("url")
                            ))
                        if b.get("website"):
                            points.append(DataPoint(
                                value=b.get("website"),
                                data_type="website",
                                source=engine,
                                confidence=0.95,
                                url=b.get("url")
                            ))
                        if b.get("name"):
                            points.append(DataPoint(
                                value=b.get("name"),
                                data_type="company_name",
                                source=engine,
                                confidence=0.9,
                                url=b.get("url")
                            ))
            
            elif engine == "linkedin":
                if "profiles" in results:
                    for p in results["profiles"][:5]:
                        if p.get("name"):
                            points.append(DataPoint(
                                value=p.get("name"),
                                data_type="name",
                                source=engine,
                                confidence=0.85,
                                url=p.get("url")
                            ))
                        if p.get("title"):
                            points.append(DataPoint(
                                value=p.get("title"),
                                data_type="job_title",
                                source=engine,
                                confidence=0.85,
                                url=p.get("url")
                            ))
            
            elif engine == "google_news":
                if "articles" in results:
                    for a in results["articles"][:3]:
                        if a.get("title"):
                            points.append(DataPoint(
                                value=a.get("title", ""),
                                data_type="news_article",
                                source=engine,
                                confidence=0.8,
                                url=a.get("url"),
                                raw_context=a.get("snippet")
                            ))
            
            elif engine == "google_shopping":
                if "products" in results:
                    for p in results["products"][:5]:
                        if p.get("price"):
                            points.append(DataPoint(
                                value=str(p.get("price")),
                                data_type="price",
                                source=engine,
                                confidence=0.9,
                                url=p.get("url"),
                                raw_context=p.get("title")
                            ))
            
            elif engine == "amazon":
                if "products" in results:
                    for p in results["products"][:5]:
                        if p.get("price"):
                            points.append(DataPoint(
                                value=str(p.get("price")),
                                data_type="price",
                                source=engine,
                                confidence=0.9,
                                url=p.get("url"),
                                raw_context=p.get("title")
                            ))
            
            elif engine == "google_jobs":
                if "jobs" in results:
                    for j in results["jobs"][:5]:
                        if j.get("title"):
                            points.append(DataPoint(
                                value=j.get("title"),
                                data_type="job_title",
                                source=engine,
                                confidence=0.8,
                                url=j.get("url")
                            ))
        
        except Exception as e:
            logger.warning(f"[EXTRACT] Error extracting data: {e}")
        
        return points


# Global instance
research_intelligence_engine = ResearchIntelligenceEngine()
