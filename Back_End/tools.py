import requests
import logging
from Back_End.config import Config
from Back_End.codebase_analyzer import CodebaseAnalyzer
from Back_End.research_intelligence_engine import research_intelligence_engine

def web_search(query: str) -> dict:
    if not Config.API_KEYS['SERPAPI'] and not Config.MOCK_MODE:
        return {'error': 'SERPAPI_KEY missing'}
    if Config.MOCK_MODE:
        return {
            'results': [f"Mock result for '{query}'"],
            'usage': {'serpapi_searches': 1}  # Track usage even in mock mode
        }
    try:
        resp = requests.get(
            'https://serpapi.com/search',
            params={'q': query, 'api_key': Config.API_KEYS['SERPAPI'], 'engine': 'google'},
            timeout=Config.TIMEOUT
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            'results': data.get('organic_results', []),
            'usage': {'serpapi_searches': 1}  # Each API call = 1 search credit
        }
    except Exception as e:
        logging.error(f"web_search failed: {e}")
        return {'error': str(e)}

def web_research(query: str) -> dict:
    """Execute intelligent multi-step research across multiple engines"""
    try:
        result = research_intelligence_engine.research(query)
        return result
    except Exception as e:
        logging.error(f"web_research failed: {e}")
        return {'error': str(e)}

def register_foundational_tools(tool_registry):
    tool_registry.register('web_search', web_search, mock_func=lambda q: {'results': [f"Mock result for '{q}'"]}, description='Search the web.')
    tool_registry.register(
        'web_research',
        web_research,
        mock_func=lambda q: {'results': [f"Mock research for '{q}'"], 'status': 'mock'},
        description='Execute intelligent multi-step research across multiple search engines with deduplication and confidence scoring.'
    )
    tool_registry.register(
        'reflect',
        reflect,
        mock_func=lambda *args, **kwargs: {
            'effectiveness_score': 0.5,
            'what_worked': 'Mock reflection: tools returned some data',
            'what_did_not_work': 'Mock reflection: refine queries',
            'strategy_adjustment': 'Mock: try targeted searches next',
            'tool_feedback': {t: {'usefulness': 0.5, 'notes': 'mock'} for t in (kwargs.get('tools_used') or [])},
            'confidence_adjustment': 0.0
        },
        description='Reflect on recent steps and suggest improvements.'
    )

def register_code_awareness_tools(tool_registry):
    """Register read-only codebase analysis tools"""
    analyzer = CodebaseAnalyzer(root_path=".")

    def repo_index_impl(_input: str = ""):
        return analyzer.get_repo_index()

    def file_summary_impl(input_str: str):
        if not input_str:
            return {'error': 'file_summary requires a filepath parameter'}
        return analyzer.get_file_summary(input_str)

    def dependency_map_impl(_input: str = ""):
        return analyzer.get_dependency_map()

    tool_registry.register(
        'repo_index',
        repo_index_impl,
        mock_func=repo_index_impl,
        description='Analyze repository structure (read-only)'
    )

    tool_registry.register(
        'file_summary',
        file_summary_impl,
        mock_func=file_summary_impl,
        description='Summarize a Python/JS/TS file (read-only)'
    )

    tool_registry.register(
        'dependency_map',
        dependency_map_impl,
        mock_func=dependency_map_impl,
        description='Show module dependencies (read-only)'
    )

def reflect(steps: list, tools_used: list, goal: str, confidence: float, memory_excerpt: dict = None) -> dict:
    try:
        # Deterministic, fast heuristic evaluation
        if Config.MOCK_MODE:
            return {
                'effectiveness_score': 0.5,
                'what_worked': 'Used web_search to gather initial information.',
                'what_did_not_work': 'Search results were limited; refine query.',
                'strategy_adjustment': 'Broaden search terms and follow with targeted queries.',
                'tool_feedback': {t: {'usefulness': 0.5, 'notes': 'Mock evaluation.'} for t in tools_used},
                'confidence_adjustment': 0.0
            }

        # Simple heuristic: count successful observations (no 'error' key and not a simple note)
        total = 0
        successes = 0
        for s in steps:
            total += 1
            if isinstance(s, dict):
                if 'error' in s:
                    continue
                note = s.get('note')
                if note and 'No tool used' in note:
                    continue
                # otherwise treat as success
                successes += 1
        effectiveness = 0.0 if total == 0 else successes / total

        # Tool feedback: score each tool by counting observations tied to it (heuristic)
        tool_feedback = {}
        for t in tools_used:
            # deterministic mapping: usefulness based on presence
            found = False
            for s in steps:
                if not isinstance(s, dict):
                    continue
                if s.get('tool') == t:
                    found = True
                    break
                dec = s.get('decision')
                if isinstance(dec, dict) and dec.get('tool') == t:
                    found = True
                    break
            usefulness = 1.0 if found else 0.5
            tool_feedback[t] = {'usefulness': float(usefulness), 'notes': 'Heuristic usefulness score.'}

        # Confidence adjustment in range [-0.2, 0.2]
        confidence_adj = max(-0.2, min(0.2, (effectiveness - 0.5) * 0.4))

        what_worked = 'Some tools returned usable observations.' if successes > 0 else 'No effective observations.'
        what_did_not_work = 'Several steps produced errors or no-op notes.' if successes < total else 'Minor issues only.'
        strategy_adjustment = (
            'If search returns few hits, broaden queries and run additional targeted searches.'
            if effectiveness < 0.6 else 'Proceed with current strategy; prioritize high-confidence sources.'
        )

        return {
            'effectiveness_score': float(round(effectiveness, 3)),
            'what_worked': what_worked,
            'what_did_not_work': what_did_not_work,
            'strategy_adjustment': strategy_adjustment,
            'tool_feedback': tool_feedback,
            'confidence_adjustment': float(round(confidence_adj, 3))
        }
    except Exception as e:
        # Never raise; always return valid structured JSON
        return {
            'effectiveness_score': 0.0,
            'what_worked': '',
            'what_did_not_work': f'Exception during reflection: {str(e)}',
            'strategy_adjustment': '',
            'tool_feedback': {},
            'confidence_adjustment': 0.0
        }

# Auto-register on import
from Back_End.tool_registry import tool_registry
register_foundational_tools(tool_registry)
register_code_awareness_tools(tool_registry)

