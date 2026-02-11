"""
Learning-focused tools for Buddy's introspection and knowledge management.
These tools enable Buddy to understand what it knows, track learning progress, and improve.
"""

import logging
import re
from typing import Dict, List, Any
from Back_End.memory_manager import memory_manager
from Back_End.tool_performance import tracker
from Back_End.tool_registry import tool_registry
from Back_End.config import Config
from Back_End.llm_client import llm_client


def learning_query(topic: str) -> Dict[str, Any]:
    """
    Query what Buddy knows about a specific topic.
    Returns confidence scores, past interactions, knowledge gaps, and learning suggestions.
    
    Args:
        topic: The subject/topic to query (e.g., "marketing", "Python", "AI")
    
    Returns:
        Dict with knowledge_summary, confidence, past_queries, gaps, suggestions
    """
    try:
        # Search memory for related interactions
        learnings = memory_manager.summarize_learnings(topic, domain="_global")
        
        # Get tool usage stats related to this topic
        relevant_tools = []
        for tool_name in tool_registry.tools.keys():
            stats = tracker.get_stats(tool_name, domain="_global")
            if stats and stats.get('total_calls', 0) > 0:
                relevant_tools.append({
                    'tool': tool_name,
                    'uses': stats['total_calls'],
                    'success_rate': stats['successful_calls'] / stats['total_calls'],
                    'usefulness': tracker.get_usefulness_score(tool_name, "_global")
                })
        
        # Sort by usage
        relevant_tools.sort(key=lambda x: x['uses'], reverse=True)
        
        # Calculate confidence score based on data available
        confidence = 0.0
        data_points = 0
        
        if learnings.get('past_observations'):
            data_points += len(learnings['past_observations'])
            confidence += min(0.4, len(learnings['past_observations']) * 0.05)
        
        if relevant_tools:
            confidence += min(0.3, len(relevant_tools) * 0.03)
            data_points += len(relevant_tools)
        
        if learnings.get('tools_to_avoid'):
            confidence += 0.1  # Having learned what NOT to do is valuable
            data_points += len(learnings['tools_to_avoid'])
        
        confidence = min(1.0, confidence)
        
        # Identify knowledge gaps
        gaps = []
        if confidence < 0.3:
            gaps.append(f"Limited experience with '{topic}' - only {data_points} data points")
        if not learnings.get('past_observations'):
            gaps.append(f"No recorded interactions about '{topic}'")
        if not relevant_tools:
            gaps.append("No tool usage history for this topic")
        
        # Generate learning suggestions
        suggestions = []
        if confidence < 0.5:
            suggestions.append(f"Ask more questions about '{topic}' to build expertise")
        if learnings.get('tools_to_avoid'):
            suggestions.append(f"Continue avoiding these tools for '{topic}': {', '.join(learnings['tools_to_avoid'])}")
        if data_points > 0:
            suggestions.append(f"Current knowledge based on {data_points} data points - continue learning!")
        
        return {
            'topic': topic,
            'confidence': round(confidence, 2),
            'expertise_level': _get_expertise_level(confidence),
            'knowledge_summary': {
                'past_observations': learnings.get('past_observations', [])[:5],  # Top 5
                'total_observations': len(learnings.get('past_observations', [])),
                'tools_to_avoid': learnings.get('tools_to_avoid', []),
                'relevant_tools': relevant_tools[:5],  # Top 5 tools
            },
            'knowledge_gaps': gaps,
            'learning_suggestions': suggestions,
            'data_points': data_points
        }
    
    except Exception as e:
        logging.error(f"learning_query failed: {e}")
        return {'error': str(e)}


def understanding_metrics(goal: str = "") -> Dict[str, Any]:
    """
    Get overall understanding metrics across all topics.
    Shows Buddy's learning trajectory, confidence distribution, and growth areas.
    
    Args:
        goal: Unused parameter (for compatibility with tool signature)
    
    Returns:
        Dict with overall_confidence, topics_learned, tool_mastery, growth_indicators
    """
    try:
        # Get all tool stats
        all_tools_stats = {}
        total_calls = 0
        successful_calls = 0
        
        for tool_name in tool_registry.tools.keys():
            stats = tracker.get_stats(tool_name, domain="_global")
            if stats:
                all_tools_stats[tool_name] = {
                    'total_calls': stats['total_calls'],
                    'success_rate': stats['successful_calls'] / stats['total_calls'] if stats['total_calls'] > 0 else 0,
                    'avg_latency_ms': stats['avg_latency_ms'],
                    'usefulness': tracker.get_usefulness_score(tool_name, "_global")
                }
                total_calls += stats['total_calls']
                successful_calls += stats['successful_calls']
        
        # Calculate overall success rate
        overall_success_rate = successful_calls / total_calls if total_calls > 0 else 0
        
        # Categorize tools by mastery level
        expert_tools = []  # >80% success, >0.7 usefulness
        learning_tools = []  # 50-80% success
        novice_tools = []  # <50% success
        
        for tool_name, stats in all_tools_stats.items():
            success_rate = stats['success_rate']
            usefulness = stats['usefulness']
            
            if success_rate >= 0.8 and usefulness >= 0.7:
                expert_tools.append(tool_name)
            elif success_rate >= 0.5:
                learning_tools.append(tool_name)
            else:
                novice_tools.append(tool_name)
        
        # Calculate overall confidence
        confidence = 0.0
        if total_calls > 0:
            confidence += min(0.4, total_calls * 0.001)  # Experience factor
        confidence += overall_success_rate * 0.4  # Success factor
        confidence += len(expert_tools) * 0.05  # Mastery factor
        confidence = min(1.0, confidence)
        
        # Identify growth indicators
        growth_indicators = []
        if total_calls > 50:
            growth_indicators.append(f"Active learning: {total_calls} total tool calls")
        if overall_success_rate > 0.7:
            growth_indicators.append(f"High success rate: {overall_success_rate:.0%}")
        if len(expert_tools) > 0:
            growth_indicators.append(f"Mastered {len(expert_tools)} tools")
        if len(novice_tools) > 0:
            growth_indicators.append(f"Improving on {len(novice_tools)} tools")
        
        return {
            'overall_confidence': round(confidence, 2),
            'confidence_level': _get_expertise_level(confidence),
            'total_tool_calls': total_calls,
            'overall_success_rate': round(overall_success_rate, 2),
            'tool_mastery': {
                'expert': expert_tools,
                'learning': learning_tools,
                'novice': novice_tools
            },
            'tool_stats': all_tools_stats,
            'growth_indicators': growth_indicators,
            'areas_for_improvement': novice_tools[:3] if novice_tools else ['Keep learning!']
        }
    
    except Exception as e:
        logging.error(f"understanding_metrics failed: {e}")
        return {'error': str(e)}


def _get_expertise_level(confidence: float) -> str:
    """Convert confidence score to human-readable expertise level"""
    if confidence >= 0.9:
        return "Expert"
    elif confidence >= 0.7:
        return "Proficient"
    elif confidence >= 0.5:
        return "Learning"
    elif confidence >= 0.3:
        return "Novice"
    else:
        return "Beginner"


def store_knowledge(topic: str, domain: str = "_global") -> Dict[str, Any]:
    """
    Actively learn and store knowledge about a topic through DEEP RESEARCH.
    Used when user instructs: "learn about X", "study X", "research X"
    
    This is NOT just a single web search - it's a comprehensive learning process:
    1. Multiple targeted searches (3-5 queries)
    2. Extract key concepts and facts
    3. Synthesize information into structured knowledge
    4. Store with high importance
    
    Args:
        topic: What to learn about (e.g., "Python decorators", "quantum computing")
        domain: Memory domain to store in
    
    Returns:
        Dict with learning summary, key concepts, confidence, and what was stored
    """
    try:
        logging.info(f"🎓 ACTIVE LEARNING: Starting deep research on '{topic}'")
        
        # Import tools here to avoid circular dependency
        from Back_End.tools import web_search
        
        # Step 1: Generate multiple targeted search queries
        search_queries = _generate_learning_queries(topic)
        logging.info(f"Generated {len(search_queries)} search queries")
        
        # Step 2: Execute searches and collect information
        all_results = []
        for idx, query in enumerate(search_queries[:5], 1):  # Max 5 searches
            logging.info(f"Search {idx}/{min(len(search_queries), 5)}: {query}")
            results = web_search(query)
            
            if isinstance(results, dict) and 'results' in results:
                all_results.extend(results['results'][:3])  # Top 3 from each search
        
        if not all_results:
            return {
                'topic': topic,
                'status': 'failed',
                'error': 'No search results found',
                'confidence': 0.0
            }
        
        # Step 3: Extract and synthesize knowledge
        logging.info(f"Synthesizing knowledge from {len(all_results)} search results")
        synthesized = _synthesize_knowledge(topic, all_results)
        
        # Step 4: Store structured knowledge in memory
        learning_data = {
            'topic': topic,
            'key_concepts': synthesized['key_concepts'],
            'summary': synthesized['summary'],
            'facts': synthesized['facts'],
            'sources': synthesized['sources'],
            'search_queries': search_queries[:5],
            'total_results': len(all_results),
            'confidence': synthesized['confidence'],
            'type': 'active_learning',
            'depth': 'comprehensive'  # Indicates multi-search learning
        }
        
        # Save with VERY HIGH importance (active learning is critical)
        key = f"knowledge:{topic}"
        saved = memory_manager.save_if_important(
            key=key,
            item_type='learning',  # Special type for active learning
            data=learning_data,
            context={'source': 'active_learning', 'searches': len(search_queries)},
            domain=domain
        )
        
        logging.info(f"✅ Learned about '{topic}' - Stored: {saved}, Confidence: {synthesized['confidence']:.2f}")
        
        return {
            'topic': topic,
            'status': 'learned',
            'confidence': synthesized['confidence'],
            'key_concepts': synthesized['key_concepts'],
            'summary': synthesized['summary'],
            'facts_learned': len(synthesized['facts']),
            'searches_performed': len(search_queries[:5]),
            'results_analyzed': len(all_results),
            'stored': saved,
            'message': f"Successfully learned about '{topic}' through {len(search_queries[:5])} searches"
        }
    
    except Exception as e:
        logging.error(f"store_knowledge failed: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e), 'topic': topic, 'status': 'failed'}


def _generate_learning_queries(topic: str) -> List[str]:
    """
    Generate multiple targeted search queries for comprehensive learning.
    
    Returns 3-5 queries covering different aspects:
    - Overview/definition
    - How it works
    - Use cases/applications
    - Advantages/limitations
    - Examples
    """
    queries = [
        f"what is {topic}",  # Overview
        f"how does {topic} work",  # Mechanism
        f"{topic} examples and use cases",  # Applications
        f"{topic} advantages and disadvantages",  # Critical analysis
    ]
    
    # Use LLM to generate even better queries if available
    if llm_client.enabled:
        try:
            prompt = f"""Generate 4 search queries to deeply learn about "{topic}".
Queries should cover: definition, mechanism, applications, pros/cons.
Return ONLY the queries, one per line."""
            
            llm_queries = llm_client.complete(prompt, max_tokens=150, temperature=0.3)
            if llm_queries:
                generated = [q.strip() for q in llm_queries.strip().split('\n') if q.strip()]
                if len(generated) >= 3:
                    return generated[:5]  # Use LLM queries if good
        except Exception as e:
            logging.warning(f"LLM query generation failed: {e}")
    
    return queries


def _synthesize_knowledge(topic: str, search_results: List[Dict]) -> Dict:
    """
    Synthesize search results into structured knowledge.
    
    Extracts:
    - Key concepts (important terms/ideas)
    - Summary (what is it, how it works)
    - Facts (discrete learnings)
    - Sources (where information came from)
    - Confidence (how complete is understanding)
    """
    # Extract text from search results
    all_text = []
    sources = []
    
    for result in search_results:
        title = result.get('title', '')
        snippet = result.get('snippet', '')
        link = result.get('link', '')
        
        if title and snippet:
            all_text.append(f"{title}: {snippet}")
            if link and link not in sources:
                sources.append(link)
    
    combined_text = ' '.join(all_text)
    
    # Try LLM synthesis for high-quality summary
    if llm_client.enabled and combined_text:
        try:
            synthesis_prompt = f"""Based on these search results about "{topic}":

{combined_text[:2000]}

Provide a structured learning summary:
1. Definition (2 sentences)
2. Key concepts (3-5 bullet points)
3. How it works (2-3 sentences)
4. Main applications (2-3 examples)

Be factual and concise."""

            llm_summary = llm_client.complete(synthesis_prompt, max_tokens=400, temperature=0.2)
            
            if llm_summary:
                # Parse LLM response into structured format
                key_concepts = _extract_bullet_points(llm_summary)
                
                return {
                    'summary': llm_summary[:500],  # Truncate if too long
                    'key_concepts': key_concepts[:7],  # Max 7 concepts
                    'facts': _extract_facts(llm_summary, topic),
                    'sources': sources[:10],  # Max 10 sources
                    'confidence': min(0.9, 0.5 + (len(search_results) * 0.05))  # More results = higher confidence
                }
        except Exception as e:
            logging.warning(f"LLM synthesis failed: {e}")
    
    # Fallback: Pattern-based synthesis
    key_concepts = _extract_key_terms(combined_text, topic)
    
    return {
        'summary': f"Learned about {topic} from {len(search_results)} sources. " + combined_text[:300],
        'key_concepts': key_concepts[:5],
        'facts': [snippet[:150] for result in search_results[:5] if (snippet := result.get('snippet'))],
        'sources': sources[:10],
        'confidence': min(0.7, 0.4 + (len(search_results) * 0.04))
    }


def _extract_bullet_points(text: str) -> List[str]:
    """Extract bullet points or numbered items from text"""
    lines = text.split('\n')
    bullets = []
    
    for line in lines:
        line = line.strip()
        # Match bullet points (-, *, •) or numbers (1., 2.)
        if re.match(r'^[-*•]\s+', line) or re.match(r'^\d+\.\s+', line):
            clean = re.sub(r'^[-*•\d.]\s+', '', line).strip()
            if clean:
                bullets.append(clean)
    
    return bullets if bullets else [text[:100]]  # Fallback


def _extract_key_terms(text: str, topic: str) -> List[str]:
    """Extract important terms/concepts from text"""
    # Simple term extraction: capitalized words that aren't common words
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    
    words = re.findall(r'\b[A-Z][a-z]+\b', text)
    terms = [w for w in set(words) if w.lower() not in common_words and len(w) > 3]
    
    # Add the topic itself
    if topic not in terms:
        terms.insert(0, topic)
    
    return terms[:7]


def _extract_facts(text: str, topic: str) -> List[str]:
    """Extract discrete facts/learnings from text"""
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    
    facts = []
    for sent in sentences:
        sent = sent.strip()
        # Facts are substantial sentences mentioning the topic
        if len(sent) > 30 and len(sent) < 200:
            facts.append(sent)
    
    return facts[:8]  # Max 8 facts


def register_learning_tools(tool_registry):
    """Register all learning-focused tools"""
    tool_registry.register(
        'learning_query',
        learning_query,
        mock_func=lambda topic: {
            'topic': topic,
            'confidence': 0.65,
            'expertise_level': 'Learning',
            'knowledge_summary': {'past_observations': [], 'tools_to_avoid': []},
            'knowledge_gaps': [f"Mock data for '{topic}'"],
            'learning_suggestions': ['Continue asking questions'],
            'data_points': 10,
            'mock': True
        },
        description='Check what Buddy ALREADY knows (introspection/self-reflection). Use ONLY for "what do YOU know" queries, NOT for learning new information.'
    )
    
    tool_registry.register(
        'understanding_metrics',
        understanding_metrics,
        mock_func=lambda: {
            'overall_confidence': 0.72,
            'confidence_level': 'Proficient',
            'total_tool_calls': 100,
            'overall_success_rate': 0.85,
            'tool_mastery': {'expert': ['calculate'], 'learning': ['web_search'], 'novice': []},
            'growth_indicators': ['Mock metrics'],
            'mock': True
        },
        description='Get overall understanding and learning metrics'
    )
    
    tool_registry.register(
        'store_knowledge',
        store_knowledge,
        mock_func=lambda topic, domain='_global': {
            'topic': topic,
            'status': 'learned',
            'confidence': 0.85,
            'key_concepts': ['Mock Concept 1', 'Mock Concept 2'],
            'summary': f"Mock: Comprehensive learning about '{topic}' through multi-search research",
            'facts_learned': 12,
            'searches_performed': 4,
            'results_analyzed': 15,
            'stored': True,
            'message': f"Mock: Successfully learned about '{topic}' through 4 searches",
            'mock': True
        },
        description='Actively LEARN and STORE knowledge (when user says "learn about X", "study X", "teach yourself X"). Performs 3-5 web searches, synthesizes information, and stores structured knowledge in memory.'
    )


# Auto-register on import
register_learning_tools(tool_registry)

