"""
LLM Client: Unified interface for language models (OpenAI, Anthropic, local)
"""

import os
import logging
import json
from typing import Dict, List, Optional
from backend.config import Config


class LLMClient:
    """Universal LLM client with fallback to pattern-based heuristics"""
    
    def __init__(self):
        self.provider = os.getenv('LLM_PROVIDER', 'none').lower()
        self.enabled = self.provider != 'none'
        
        if self.provider == 'openai':
            self._init_openai()
        elif self.provider == 'anthropic':
            self._init_anthropic()
        
        logging.info(f"LLM Client initialized: provider={self.provider}, enabled={self.enabled}")
    
    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            import openai
            self.openai = openai
            self.openai.api_key = os.getenv('OPENAI_API_KEY')
            self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            logging.info(f"OpenAI initialized: model={self.model}")
        except ImportError:
            logging.error("OpenAI library not installed. Run: pip install openai")
            self.enabled = False
        except Exception as e:
            logging.error(f"OpenAI initialization failed: {e}")
            self.enabled = False
    
    def _init_anthropic(self):
        """Initialize Anthropic client"""
        try:
            import anthropic
            self.anthropic_client = anthropic.Anthropic(
                api_key=os.getenv('ANTHROPIC_API_KEY')
            )
            self.model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
            logging.info(f"Anthropic initialized: model={self.model}")
        except ImportError:
            logging.error("Anthropic library not installed. Run: pip install anthropic")
            self.enabled = False
        except Exception as e:
            logging.error(f"Anthropic initialization failed: {e}")
            self.enabled = False
    
    def complete(self, prompt: str, system_prompt: str = "", max_tokens: int = 500, temperature: float = 0.7) -> Optional[str]:
        """
        Get completion from LLM with fallback to None if unavailable.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            max_tokens: Max response length
            temperature: Creativity (0.0-1.0)
        
        Returns:
            LLM response text or None if unavailable
        """
        if not self.enabled:
            return None
        
        try:
            if self.provider == 'openai':
                return self._complete_openai(prompt, system_prompt, max_tokens, temperature)
            elif self.provider == 'anthropic':
                return self._complete_anthropic(prompt, system_prompt, max_tokens, temperature)
        except Exception as e:
            logging.error(f"LLM completion failed: {e}")
            return None
    
    def _complete_openai(self, prompt: str, system_prompt: str, max_tokens: int, temperature: float) -> str:
        """OpenAI completion - returns text content"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.openai.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Store last usage for tracking (can be retrieved separately)
        self.last_usage = {
            'input_tokens': response.usage.prompt_tokens,
            'output_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens,
            'model': self.model
        }
        
        return response.choices[0].message.content.strip()
    
    def get_last_usage(self) -> dict:
        """Get token usage from last API call"""
        return getattr(self, 'last_usage', {})
    
    def _complete_anthropic(self, prompt: str, system_prompt: str, max_tokens: int, temperature: float) -> str:
        """Anthropic completion"""
        response = self.anthropic_client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt if system_prompt else "You are a helpful AI assistant.",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    
    def select_tool(self, goal: str, available_tools: List[Dict]) -> Optional[Dict]:
        """
        Use LLM to intelligently select the best tool for a goal.
        
        Returns:
            {
                'tool': 'tool_name',
                'confidence': 0.95,
                'reasoning': 'explanation',
                'input': {...}
            }
        """
        if not self.enabled:
            return None
        
        tool_descriptions = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in available_tools
        ])
        
        system_prompt = """You are an intelligent tool selector. Given a user goal and available tools, select the BEST tool to accomplish the goal.

CRITICAL DISTINCTIONS:
- "what do YOU know about X?" → learning_query (introspection - check agent's memory)
- "learn about X" / "study X" → store_knowledge (active learning - research AND save)
- "what is X?" / "explain X" → web_search (research only - no saving)

Respond ONLY with valid JSON in this format:
{
  "tool": "tool_name",
  "confidence": 0.95,
  "reasoning": "why this tool is best",
  "input": {"key": "value"}
}

If no tool matches, use "tool": "none" and confidence 0.0."""

        prompt = f"""Goal: {goal}

Available Tools:
{tool_descriptions}

Select the best tool for this goal. Consider:
1. Tool purpose and description
2. Input requirements
3. Expected output

JSON response:"""

        try:
            response = self.complete(prompt, system_prompt, max_tokens=300, temperature=0.3)
            if not response:
                return None
            
            # Strip JavaScript-style comments from JSON response
            import re
            cleaned_response = re.sub(r'//[^\n]*', '', response)
            
            # Parse JSON response
            result = json.loads(cleaned_response)
            return result
        except json.JSONDecodeError:
            logging.error(f"Failed to parse LLM tool selection: {response}")
            return None
        except Exception as e:
            logging.error(f"LLM tool selection failed: {e}")
            return None
    
    def decompose_goal(self, goal: str) -> Optional[Dict]:
        """
        Use LLM to intelligently decompose complex goals into subgoals.
        
        Returns:
            {
                'is_composite': True/False,
                'subgoals': ['subgoal1', 'subgoal2', ...],
                'reasoning': 'explanation'
            }
        """
        if not self.enabled:
            return None
        
        system_prompt = """You are an intelligent goal decomposer. Determine if a goal is composite (needs multiple steps) or atomic (single step).

CRITICAL: These are ALWAYS atomic (single step):

Introspection queries:
- "what do you know about X?" → ATOMIC (query agent's memory, NOT research)
- "tell me what you know/learned" → ATOMIC (self-reflection)
- "show me your understanding" → ATOMIC (introspection)
- "how much do you know about" → ATOMIC (knowledge check)

Learning instructions:
- "learn about X" → ATOMIC (active learning task)
- "study X" → ATOMIC (research and store)
- "research and remember X" → ATOMIC (learn and save)
- "teach yourself X" → ATOMIC (active learning)

For composite goals, break them into 2-4 clear, sequential subgoals.

Respond ONLY with valid JSON:
{
  "is_composite": true/false,
  "subgoals": ["subgoal1", "subgoal2"],
  "reasoning": "why composite or atomic"
}"""

        prompt = f"""Goal: {goal}

Is this goal composite (needs multiple steps) or atomic (single step)?
If composite, break it into 2-4 subgoals.

JSON response:"""

        try:
            response = self.complete(prompt, system_prompt, max_tokens=400, temperature=0.3)
            if not response:
                return None
            
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            logging.error(f"Failed to parse LLM goal decomposition: {response}")
            return None
        except Exception as e:
            logging.error(f"LLM goal decomposition failed: {e}")
            return None
    
    def synthesize_answer(self, goal: str, observations: List[Dict]) -> Optional[str]:
        """
        Use LLM to synthesize observations into a natural, helpful answer.
        
        Returns:
            Natural language answer or None
        """
        if not self.enabled:
            return None
        
        system_prompt = """You are a helpful AI assistant. Given a user's goal and the observations from tools, synthesize a clear, concise, natural answer.

Keep answers:
- Direct and informative
- Well-formatted with proper spacing
- Include sources if relevant
- Maximum 3-4 sentences unless more detail is needed"""

        # Format observations
        obs_text = "\n\n".join([
            f"Tool: {obs.get('tool', 'unknown')}\nResult: {json.dumps(obs.get('observation', {}), indent=2)}"
            for obs in observations[-3:]  # Last 3 observations
        ])
        
        prompt = f"""User Goal: {goal}

Tool Observations:
{obs_text}

Synthesize a natural, helpful answer:"""

        try:
            response = self.complete(prompt, system_prompt, max_tokens=500, temperature=0.7)
            return response
        except Exception as e:
            logging.error(f"LLM answer synthesis failed: {e}")
            return None


# Singleton instance
llm_client = LLMClient()
