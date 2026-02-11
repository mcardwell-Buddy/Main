"""
Curiosity Engine - generates follow-up questions and explores related topics.
Makes the agent autonomously explore beyond the user's original question.
"""
import logging
from typing import Dict, List, Optional
from Back_End.llm_client import llm_client
from Back_End.memory_manager import memory_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CuriosityEngine:
    """
    Generates curiosity-driven follow-up questions and exploration paths.
    """
    
    def __init__(self):
        self.min_confidence_for_exploration = 0.75  # Only explore after good understanding
        self.max_exploration_depth = 3  # How deep to go on tangents
        self.min_confidence_for_tangents = 0.85  # Higher bar for tangent exploration
        
    def should_explore_further(self, topic: str, confidence: float, 
                               depth: int, learned_concepts: List[str]) -> bool:
        """
        Decide if agent should continue exploring beyond user's question.
        
        Args:
            topic: Main topic being researched
            confidence: Current confidence in understanding (0-1)
            depth: Current exploration depth
            learned_concepts: Key concepts already learned
            
        Returns:
            bool - whether to continue exploring
        """
        # Don't explore if confidence too low (still learning basics)
        if confidence < self.min_confidence_for_exploration:
            logger.info(f"Confidence {confidence:.2f} < {self.min_confidence_for_exploration}, not exploring yet")
            return False
        
        # Don't go too deep
        if depth >= self.max_exploration_depth:
            logger.info(f"Reached max exploration depth {self.max_exploration_depth}")
            return False
        
        # Check if there are interesting concepts to explore
        if not learned_concepts or len(learned_concepts) < 2:
            logger.info("Not enough concepts learned to generate curiosity")
            return False
        
        logger.info(f"Curiosity triggered! Confidence {confidence:.2f}, depth {depth}, {len(learned_concepts)} concepts")
        return True
    
    def generate_curiosity_questions(self, topic: str, 
                                    learned_content: Dict,
                                    max_questions: int = 5) -> List[Dict]:
        """
        Generate exploratory questions beyond the original goal.
        
        Args:
            topic: Main topic
            learned_content: What's been learned (concepts, facts, etc.)
            max_questions: Maximum questions to generate
            
        Returns:
            List of curiosity questions with metadata
        """
        key_concepts = learned_content.get('key_concepts', [])
        facts = learned_content.get('facts', [])
        
        if not llm_client.enabled:
            # Fallback: template-based questions
            return self._generate_template_questions(topic, key_concepts)
        
        try:
            prompt = f"""Based on this learning about "{topic}", generate {max_questions} curiosity-driven follow-up questions that would deepen understanding.

**Key Concepts Learned**:
{format_list(key_concepts[:5])}

**Key Facts**:
{format_list(facts[:5])}

Generate diverse questions covering:
1. Comparisons (how does this compare to alternatives?)
2. Limitations (what are the constraints or drawbacks?)
3. Applications (real-world use cases or examples?)
4. Connections (how does this relate to other topics?)
5. Evolution (historical context or future directions?)

Return JSON array:
[
  {{
    "question": "<curious question>",
    "type": "comparison|limitation|application|connection|evolution",
    "priority": <1-5>,
    "rationale": "<why this is interesting>"
  }},
  ...
]"""

            response = llm_client.complete(prompt, max_tokens=600, temperature=0.7)
            
            import json
            questions = json.loads(response)
            
            if not isinstance(questions, list):
                questions = [questions]
            
            # Sort by priority
            questions.sort(key=lambda q: q.get('priority', 3), reverse=True)
            
            return questions[:max_questions]
            
        except Exception as e:
            logger.error(f"LLM curiosity generation failed: {e}")
            return self._generate_template_questions(topic, key_concepts)
    
    def _generate_template_questions(self, topic: str, concepts: List[str]) -> List[Dict]:
        """
        Fallback: generate template-based curiosity questions.
        """
        questions = []
        
        # Comparison questions
        questions.append({
            'question': f"What is {topic} similar to, and how do they differ?",
            'type': 'comparison',
            'priority': 4,
            'rationale': 'Understanding analogies deepens comprehension'
        })
        
        # Limitation questions
        questions.append({
            'question': f"What are the limitations or drawbacks of {topic}?",
            'type': 'limitation',
            'priority': 5,
            'rationale': 'Critical thinking about constraints'
        })
        
        # Application questions
        questions.append({
            'question': f"What are real-world examples or use cases of {topic}?",
            'type': 'application',
            'priority': 4,
            'rationale': 'Concrete examples aid understanding'
        })
        
        # If we have concepts, ask about connections
        if concepts:
            questions.append({
                'question': f"How does {concepts[0] if concepts else topic} relate to broader concepts?",
                'type': 'connection',
                'priority': 3,
                'rationale': 'Building knowledge web'
            })
        
        # Evolution question
        questions.append({
            'question': f"How has {topic} evolved, and where is it heading?",
            'type': 'evolution',
            'priority': 3,
            'rationale': 'Historical and future context'
        })
        
        return questions[:5]
    
    def explore_tangent(self, main_topic: str, tangent_concept: str, 
                       confidence: float, depth: int = 1) -> Optional[Dict]:
        """
        Explore a tangential topic discovered during main research.
        
        Args:
            main_topic: Original topic
            tangent_concept: Related concept to explore
            confidence: Confidence in main topic understanding
            depth: Current depth (stops at max_depth)
            
        Returns:
            Exploration results or None if shouldn't explore
        """
        # Check if we should explore this tangent
        if confidence < self.min_confidence_for_tangents:
            logger.info(f"Confidence {confidence:.2f} too low for tangent exploration")
            return None
        
        if depth >= self.max_exploration_depth:
            logger.info(f"Already at max depth {self.max_exploration_depth}")
            return None
        
        logger.info(f"🔍 Curiosity: Exploring tangent '{tangent_concept}' from '{main_topic}'")
        
        # Do mini-research on tangent (using existing tools)
        from Back_End.learning_tools import store_knowledge
        
        try:
            tangent_result = store_knowledge(
                topic=tangent_concept,
                domain=f"curiosity_from_{main_topic[:30]}"
            )
            
            # Link back to main topic in memory
            self._create_knowledge_link(main_topic, tangent_concept, "related_to")
            
            return {
                'main_topic': main_topic,
                'tangent': tangent_concept,
                'depth': depth,
                'confidence': tangent_result.get('confidence', 0.0),
                'key_concepts': tangent_result.get('key_concepts', []),
                'summary': tangent_result.get('synthesis', {}).get('summary', '')
            }
            
        except Exception as e:
            logger.error(f"Tangent exploration failed: {e}")
            return None
    
    def _create_knowledge_link(self, topic_a: str, topic_b: str, relationship: str):
        """
        Create a link between two topics in knowledge memory.
        """
        try:
            link_data = {
                'from': topic_a,
                'to': topic_b,
                'relationship': relationship,
                'bidirectional': True
            }
            
            memory_manager.save_if_important(
                key=f"link_{topic_a}_{topic_b}",
                item_type='knowledge_link',
                data=link_data,
                importance=0.7,
                domain='knowledge_graph'
            )
            
            logger.info(f"Created knowledge link: {topic_a} --[{relationship}]--> {topic_b}")
        except Exception as e:
            logger.error(f"Failed to create knowledge link: {e}")
    
    def is_tangent_worthy(self, concept: str, main_topic: str) -> bool:
        """
        Decide if a concept is interesting enough to explore as tangent.
        
        Simple heuristic for now - could be made more sophisticated.
        """
        # Don't explore if concept is too similar to main topic
        if concept.lower() in main_topic.lower() or main_topic.lower() in concept.lower():
            return False
        
        # Don't explore very short concepts (likely not substantial)
        if len(concept.split()) < 2:
            return False
        
        # Could add more sophisticated filtering here
        return True


def format_list(items: List[str]) -> str:
    """Format list for LLM prompt"""
    if not items:
        return "None"
    return "\n".join(f"- {item}" for item in items)


# Global instance
curiosity_engine = CuriosityEngine()


def generate_curiosity_followups(topic: str, learned_content: Dict, 
                                 confidence: float, depth: int = 0) -> Dict:
    """
    Tool function: Generate curiosity-driven follow-up questions.
    
    Args:
        topic: Main topic being researched
        learned_content: What's been learned (dict with key_concepts, facts, etc.)
        confidence: Current confidence in understanding (0-1)
        depth: Current exploration depth
        
    Returns:
        dict with 'should_explore', 'questions', 'tangents'
    """
    key_concepts = learned_content.get('key_concepts', [])
    
    should_explore = curiosity_engine.should_explore_further(
        topic, confidence, depth, key_concepts
    )
    
    if not should_explore:
        return {
            'should_explore': False,
            'reason': 'Confidence too low or depth limit reached',
            'questions': [],
            'tangents': []
        }
    
    # Generate curiosity questions
    questions = curiosity_engine.generate_curiosity_questions(topic, learned_content)
    
    # Identify interesting tangents to explore
    tangents = []
    for concept in key_concepts[:3]:  # Top 3 concepts
        if curiosity_engine.is_tangent_worthy(concept, topic):
            tangents.append({
                'concept': concept,
                'priority': 3,  # Could be made dynamic
                'reason': f'Related to {topic}'
            })
    
    return {
        'should_explore': True,
        'questions': questions,
        'tangents': tangents[:2],  # Top 2 tangents
        'exploration_depth': depth
    }


def register_curiosity_tools(tool_registry):
    """Register curiosity engine tools"""
    tool_registry.register(
        name='generate_curiosity_followups',
        func=generate_curiosity_followups,
        description='Generate curiosity-driven follow-up questions and exploration paths after learning about a topic. Parameters: topic, learned_content, confidence, depth (optional)',
        mock_func=lambda topic, **kwargs: {
            'should_explore': True,
            'questions': [
                {
                    'question': f'[MOCK] What are the limitations of {topic}?',
                    'type': 'limitation',
                    'priority': 5
                },
                {
                    'question': f'[MOCK] How does {topic} compare to alternatives?',
                    'type': 'comparison',
                    'priority': 4
                }
            ],
            'tangents': [
                {'concept': '[MOCK] Related Concept 1', 'priority': 3},
                {'concept': '[MOCK] Related Concept 2', 'priority': 2}
            ]
        }
    )
    
    logger.info("Registered curiosity engine tools")

