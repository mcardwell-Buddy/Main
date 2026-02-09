import re
import logging
from typing import List, Dict, Tuple, Optional
from backend.tool_registry import tool_registry
from backend.tool_performance import tracker
from backend.memory_manager import memory_manager
from backend.feedback_manager import feedback_manager
from backend.llm_client import llm_client

class ToolSelector:
    """Intelligent tool selection based on goal analysis and learned patterns"""
    
    def __init__(self):
        # Keywords/patterns that indicate which tool to use
        # ORDER MATTERS: Check more specific patterns first
        # INTROSPECTION/LEARNING QUERIES MUST BE FIRST (before web_search)
        self.tool_patterns = {
            'learning_query': [
                r'\b(what do you know about|tell me what you know|what have you learned about)\b',
                r'\b(how much do you know|what\'s your understanding of|explain your knowledge of)\b',
                r'\b(what can you tell me about your.*knowledge|show me what you learned)\b',
                r'\byour knowledge (about|of)\b',
                r'\bshow me what you (know|learned)\b',
            ],
            'store_knowledge': [
                r'\b(learn about|study|research and remember)\b',
                r'\b(teach yourself|find out about and remember|memorize)\b',
                r'\b(actively learn|build knowledge about|gain expertise in)\b',
                r'\b(learn everything about|become expert in)\b',
            ],
            'understanding_metrics': [
                r'\b(show.*metrics|learning progress|understanding level|confidence score)\b',
                r'\b(how confident are you|what\'s your expertise|mastery level)\b',
                r'\b(what topics.*learned|show growth|learning trajectory)\b',
                r'\bshow (me )?your (learning|progress|metrics|confidence)\b',
            ],
            'get_time': [
                r'\b(what time|current time|what\'s the time|time is it|time now)\b',
                r'\b(what date|current date|what\'s the date|today\'s date|what date is it)\b',
                r'\b(show.*time|get.*time|tell.*time|show.*date|get.*date)\b',
                r'\b(what is.*time)\b',  # Catch "what is the current time"
                r'\b(what is.*today)\b',  # Catch "what is today"
            ],
            'calculate': [
                r'\b(calculate|compute|solve|evaluate)\b',  # Explicit math words
                r'\b(what is|how much).*\d+[\s]*[-+*/xX][\s]*\d+',  # "What is 100+50" style
                r'^\d+[\s]*[-+*/xX][\s]*\d+',  # Math expressions at start: "100 + 50"
                r'\b(sum|product|divide|multiply|add|subtract|minus|times|math|arithmetic)\b',
            ],
            'read_file': [
                r'\b(read|show|display|open|view|examine|check)\b.*\b(file|document|code)\b',
                r'\.(txt|py|js|json|md|csv)',
            ],
            'list_directory': [
                r'\b(list|show|display)\b.*\b(directory|folder|files|contents)\b',
                r'\b(what files|what\'s in|contents of)\b',
            ],
            'mployer_login': [
                r'\b(mployer|m?ployer).*\b(login|log in|sign in|authenticate)\b',
                r'\b(login|log in|sign in).*\b(mployer|m?ployer)\b',
            ],
            'mployer_search_employers': [
                r'\b(search|find|look.*for).*\b(employers?|companies|contacts?|businesses)\b.*\b(mployer|maryland|employees?|size|industry)\b',
                r'\bmployer.*\b(search|find|employers?|contacts?)\b',
                r'\b(employers?|contacts?).*\b(maryland|[A-Z]{2}).*\b(employees?|size|between)',
            ],
            'web_search': [
                r'\b(search|find|look up|research|investigate|discover)\b',
                r'\b(latest|recent|news|information about)\b',
                r'\b(best practices|how to|tutorial|guide|examples)\b',
                r'\b(who is|when did|where is|what company|what organization|what is [A-Z])\b',
            ],
            'web_navigate': [
                r'\b(navigate|go to|visit|browse|open|visit)\b.*\b(site|page|website|url|link)\b',
                r'\b(navigate|go to|visit|open)\b.*\bhttps?://',
            ],
            'web_extract': [
                r'\b(extract|pull|get|grab|fetch|scrape|retrieve)\b.*\b(data|content|text|info|information|details|element|value)\b',
                r'\b(extract|parse|get)\b.*\b(from|off|off of)\b',
                r'\b(scrape|extract|pull)\b',
                r'\b(data.*extract|extract.*data)\b',
            ],
            'reflect': [
                r'\b(reflect|evaluate|assess|review|analyze my)\b',
            ],
            'repo_index': [
                r'\b(repository|repo|structure|architecture|organization)\b',
                r'\b(what files|what modules|project layout)\b',
            ],
            'file_summary': [
                r'\b(summarize|understand|what does|analyze)\b.*\b(file|module)\b',
                r'\.(py|js|ts|jsx|tsx)\b',
            ],
            'dependency_map': [
                r'\b(dependencies|imports|relationships|how do.*relate)\b',
                r'\b(circular|orphaned|core modules)\b',
            ],
            'web_research': [
                r'\b(tell me (all )?about|comprehensive|deep dive|research|investigate thoroughly|find out everything about)\b',
                r'\b(what do you know|full information|complete profile|overview of)\b',
                r'\b(marketing contacts|email|phone number|business address|contact information)\b.*\b(companies?|businesses?)\b',
                r'\b(find.*contacts?.*for|contact info for|reach out to)\b',
                r'\b(find (all )?phone numbers?|find (all )?email(s)?|find (all )?employees?|find team)\b',
                r'\b(business intelligence|market research|competitor research|industry analysis)\b',
                r'\b(extract.*contact|gather.*information|collect.*data)\b.*\b(companies?|businesses?)\b',
            ]
        }
    
    def is_proper_noun_query(self, goal: str) -> bool:
        """
        Detect if query is asking about a specific entity/organization/person.
        Returns True if it looks like: "What is [Proper Noun]?" or "Who is [Proper Noun]?"
        Examples: "What is Cardwell Associates?", "Who is Elon Musk?"
        """
        # Common English words that start sentences (not proper nouns)
        sentence_starters = {'what', 'who', 'when', 'where', 'why', 'how', 'is', 'are', 'do', 'does', 'did', 'can', 'could', 'will', 'would', 'should', 'have', 'has', 'had', 'may', 'might', 'must', 'shall', 'the', 'a', 'an'}
        
        # Pattern: Capital letter followed by lowercase, possibly multiple words
        # But exclude sentence starters
        potential_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', goal)
        
        # Filter out sentence starters
        proper_nouns = [n for n in potential_nouns if n.lower() not in sentence_starters]
        
        # If we found actual proper nouns (not just "What" or "I"), it's likely an entity question
        if not proper_nouns:
            return False
        
        # Confirm it's a knowledge question pattern
        is_entity_question = bool(re.search(
            r'\b(what is|who is|what company|what organization|what are)\b',
            goal, re.IGNORECASE
        ))
        
        # If it has proper nouns AND is phrased as an entity question, it's a proper noun query
        # But NOT if it contains math operators
        if is_entity_question and proper_nouns:
            if not re.search(r'\d+[\s]*[-+*/xX][\s]*\d+', goal):
                return True
        
        return False
    
    def is_math_query(self, goal: str) -> bool:
        """Detect if query is mathematical"""
        # Explicit math operators with numbers
        if re.search(r'\d+[\s]*[-+*/xX][\s]*\d+', goal):
            return True
        
        # Math-specific keywords
        if re.search(r'\b(calculate|compute|solve|evaluate|sum|product|divide|multiply|add|subtract)\b', goal, re.IGNORECASE):
            return True
        
        return False
    
    def is_time_query(self, goal: str) -> bool:
        """Detect if query is about time/date"""
        time_patterns = r'\b(time|date|today|now|current|what hour|what minute|when is it)\b'
        return bool(re.search(time_patterns, goal, re.IGNORECASE))
    
    def is_extraction_query(self, goal: str) -> bool:
        """Detect if query is about extracting/scraping/pulling data"""
        extraction_patterns = r'\b(extract|pull|get|grab|fetch|scrape|retrieve|parse)\b.*\b(data|content|text|info|information|details)\b'
        return bool(re.search(extraction_patterns, goal, re.IGNORECASE))
    
    def analyze_goal(self, goal: str) -> Dict[str, float]:
        """
        Analyze a goal and return confidence scores for each tool.
        Returns: {tool_name: confidence_score (0.0 to 1.0)}
        """
        goal_lower = goal.lower()
        scores = {}
        
        # Context checks (these have priority)
        is_math = self.is_math_query(goal)
        is_time = self.is_time_query(goal)
        is_proper_noun = self.is_proper_noun_query(goal)
        is_extraction = self.is_extraction_query(goal)
        
        logging.debug(f"Query analysis - math:{is_math}, time:{is_time}, proper_noun:{is_proper_noun}, extraction:{is_extraction}")
        
        for tool_name, patterns in self.tool_patterns.items():
            score = 0.0
            for pattern in patterns:
                if re.search(pattern, goal_lower, re.IGNORECASE):
                    score += 0.3
            
            # CONTEXT PRIORITY OVERRIDES
            # If it's clearly an extraction query, boost web extraction tools
            if is_extraction and tool_name in ['web_extract', 'web_navigate', 'web_search']:
                score = min(1.0, score + 0.5)
            elif is_extraction and tool_name == 'calculate':
                score = max(0.0, score - 0.6)  # Heavy penalty - don't use calculate for extraction!
            
            # If it's clearly a math question, strongly boost calculate
            if is_math and tool_name == 'calculate':
                score = min(1.0, score + 0.5)  # Strong boost
            elif is_math and tool_name in ['web_search', 'get_time', 'web_extract']:
                score = max(0.0, score - 0.3)  # Penalize non-math tools
            
            # If it's clearly a time question, strongly boost get_time
            if is_time and tool_name == 'get_time':
                score = min(1.0, score + 0.5)
            elif is_time and tool_name in ['calculate', 'web_search', 'web_extract']:
                score = max(0.0, score - 0.2)
            
            # If it's a proper noun (entity/company/person), strongly boost web_search
            if is_proper_noun and tool_name == 'web_search':
                score = min(1.0, score + 0.6)  # Strongest boost
            elif is_proper_noun and tool_name in ['calculate', 'get_time', 'web_extract']:
                score = max(0.0, score - 0.4)  # Heavy penalty
            
            # If it's a research/comprehensive query, boost web_research
            is_research_query = bool(re.search(
                r'\b(tell me.*about|comprehensive|deep dive|research|investigate|marketing contacts|find.*contacts?)\b',
                goal, re.IGNORECASE
            ))
            if is_research_query and tool_name == 'web_research':
                score = min(1.0, score + 0.7)  # Very strong boost for research queries
            
            # Cap at 1.0
            scores[tool_name] = min(1.0, score)
        
        return scores
    
    def _select_tool_with_llm(self, goal: str, domain: str) -> Optional[Dict]:
        """Use LLM to select tool intelligently"""
        # Prepare tool list for LLM
        available_tools = []
        for tool_name, tool_info in tool_registry.tools.items():
            available_tools.append({
                'name': tool_name,
                'description': tool_info.get('description', ''),
                'domain': domain
            })
        
        # Get LLM selection
        result = llm_client.select_tool(goal, available_tools)
        
        # Validate result
        if result and result.get('tool') != 'none' and result['tool'] in tool_registry.tools:
            return {
                'tool': result['tool'],
                'confidence': result.get('confidence', 0.8),
                'reasoning': result.get('reasoning', '')
            }
        
        return None
    
    def get_tool_usefulness(self, tool_name: str) -> float:
        """Get historical usefulness score from performance tracker"""
        return tracker.get_usefulness_score(tool_name)
    
    def select_tool(self, goal: str, context: Dict = None) -> Tuple[str, str, float]:
        """
        Select the best tool for a goal.
        Prioritizes high-confidence deterministic pattern matches.
        Uses LLM only when pattern confidence is ambiguous/low.
        Returns: (tool_name, input_for_tool, confidence)
        """
        context = context or {}
        domain = context.get('domain', '_global')
        
        # DETERMINISTIC PRIORITY: Check pattern-based selection first
        # If we have a high-confidence pattern match, use it immediately without LLM override
        pattern_scores = self.analyze_goal(goal)
        
        # Find the best pattern match
        if pattern_scores:
            max_pattern_score = max(pattern_scores.values(), default=0.0)
            # If pattern score is high enough (>=0.8), use it deterministically
            if max_pattern_score >= 0.8:
                best_pattern_tool = max(pattern_scores.items(), key=lambda x: x[1])[0]
                logging.info(f"High-confidence pattern match: {best_pattern_tool} (score: {max_pattern_score:.2f}) - using deterministically")
                # Skip LLM and use pattern result directly
                tool_input = self.prepare_input(best_pattern_tool, goal, context)
                return best_pattern_tool, tool_input, max_pattern_score
        
        # PROBABILISTIC FALLBACK: Try LLM-based selection when pattern confidence is low
        if llm_client.enabled:
            llm_result = self._select_tool_with_llm(goal, domain)
            if llm_result:
                logging.info(f"LLM selected {llm_result['tool']} (confidence: {llm_result['confidence']:.2f})")
                return llm_result['tool'], self.prepare_input(goal, llm_result['tool']), llm_result['confidence']
            else:
                logging.info("LLM selection failed, falling back to patterns")
        
        # Fallback to full pattern-based selection with performance scores
        
        # Get domain-specific performance
        performance_scores = {}
        for tool_name in tool_registry.tools.keys():
            performance_scores[tool_name] = tracker.get_usefulness_score(tool_name, domain)
        
        # Combine pattern matching + historical performance
        final_scores = {}
        for tool_name in tool_registry.tools.keys():
            pattern_conf = pattern_scores.get(tool_name, 0.0)
            perf_conf = performance_scores.get(tool_name, 0.5)
            
            # Weighted combination: 80% pattern matching, 20% historical
            final_scores[tool_name] = (pattern_conf * 0.8) + (perf_conf * 0.2)
        
        logging.debug(f"Initial final_scores: {final_scores}")
        
        # Check memory for domain-specific learned penalties
        learnings = memory_manager.summarize_learnings(goal, domain=domain)
        tools_to_avoid = learnings.get('tools_to_avoid', [])
        
        # Penalize tools that have failed before in this domain
        for tool_name in tools_to_avoid:
            if tool_name in final_scores:
                final_scores[tool_name] *= 0.3  # Heavy penalty
                logging.info(f"Penalizing {tool_name} in domain '{domain}' - learned it fails for this goal type")

        # Apply human feedback adjustments (highest priority)
        for tool_name in list(final_scores.keys()):
            multiplier, hard_constraint, matched = feedback_manager.get_tool_adjustment(goal, tool_name, domain)
            if hard_constraint:
                final_scores[tool_name] = 0.0
                logging.info(f"Tool {tool_name} constrained by feedback: {hard_constraint}")
                continue
            if matched:
                final_scores[tool_name] *= multiplier
                logging.info(f"Tool {tool_name} adjusted by human feedback (x{multiplier:.2f})")
        
        logging.debug(f"Final scores after adjustments: {final_scores}")
        
        # Find best tool
        if not final_scores:
            logging.debug("No tools available")
            return None, None, 0.0
        
        max_score = max(final_scores.values())
        if max_score < 0.15:
            logging.debug(f"All tool scores too low (max: {max_score:.2f})")
            return None, None, max_score
        
        best_tool = max(final_scores.items(), key=lambda x: x[1])
        tool_name = best_tool[0]
        confidence = best_tool[1]
        
        # Prepare input for the tool
        tool_input = self.prepare_input(tool_name, goal, context)
        
        logging.info(f"Selected tool: {tool_name} in domain '{domain}' (confidence: {confidence:.2f})")
        logging.debug(f"All scores: {final_scores}")
        
        return tool_name, tool_input, confidence
    
    def prepare_input(self, tool_name: str, goal: str, context: Dict = None) -> str:
        """Prepare the input parameter for a specific tool using LLM-based extraction"""
        context = context or {}
        
        # Tools that need no input
        if tool_name in ['get_time', 'repo_index', 'dependency_map', 'understanding_metrics']:
            return ''
        
        # Use LLM to extract the appropriate input from the goal
        try:
            prompt = self._build_input_extraction_prompt(tool_name, goal)
            response = llm_client.complete(prompt, max_tokens=200, temperature=0.3)
            extracted_input = response.strip()
            
            # Remove surrounding quotes if present (LLM sometimes adds them)
            if extracted_input:
                if (extracted_input.startswith('"') and extracted_input.endswith('"')) or \
                   (extracted_input.startswith("'") and extracted_input.endswith("'")):
                    extracted_input = extracted_input[1:-1]
            
            if extracted_input and extracted_input.lower() not in ['none', 'n/a', 'not found', 'unable']:
                logging.info(f"[INPUT_EXTRACTION] {tool_name}: {extracted_input[:100]}")
                return extracted_input
        except Exception as e:
            logging.warning(f"[INPUT_EXTRACTION_ERROR] Failed to extract input for {tool_name}: {e}")
        
        # Fallback: return the whole goal if LLM fails
        return goal
    
    def _build_input_extraction_prompt(self, tool_name: str, goal: str) -> str:
        """Build an LLM prompt for extracting tool-specific input from goal"""
        
        prompts = {
            'web_search': f"""Extract the search query from this request. Return ONLY the search query, nothing else.
Request: {goal}
Search query:""",
            
            'calculate': f"""Extract the mathematical expression to calculate. Return ONLY the expression (e.g., "100 + 50", "25 * 4").
Request: {goal}
Expression:""",
            
            'learning_query': f"""Extract the topic being asked about. Return ONLY the topic name.
Request: {goal}
Topic:""",
            
            'read_file': f"""Extract the file path or filename. Return ONLY the file path.
Request: {goal}
File path:""",
            
            'list_directory': f"""Extract the directory path. Return ONLY the directory path.
Request: {goal}
Directory path:""",
            
            'file_summary': f"""Extract the file path to summarize. Return ONLY the file path.
Request: {goal}
File path:""",
            
            'web_navigate': f"""Extract the URL or website to navigate to. Return ONLY the URL (starting with http:// or https://).
Request: {goal}
URL:""",
            
            'web_extract': f"""Extract what content the user wants to extract from the webpage. Return ONLY the content type/description.
Examples: "services section", "contact information", "product list", "pricing table", "company overview"
Request: {goal}
What to extract:""",
            
            'web_research': f"""Extract the research query/entity being asked about. 
For company research: Return the company name or entity to research
For contact extraction: Return what type of contacts and for which company/industry
Return ONLY the research target, nothing else.
Request: {goal}
Research target:""",
        }
        
        return prompts.get(tool_name, f"Extract the input needed for {tool_name}. Request: {goal}\nInput:")
    
    def explain_selection(self, goal: str) -> str:
        """Explain why a particular tool was selected (for debugging)"""
        scores = self.analyze_goal(goal)
        explanation = ["Tool selection reasoning:"]
        
        for tool, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            if score > 0:
                explanation.append(f"  - {tool}: {score:.2f} confidence")
        
        return "\n".join(explanation)

tool_selector = ToolSelector()
