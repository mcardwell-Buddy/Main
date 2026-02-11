import logging
from datetime import datetime
from Back_End.memory import memory
from Back_End.config import Config

class MemoryManager:
    """Intelligent memory management - decides what to save and what's important"""
    
    def __init__(self):
        self.importance_threshold = 0.6  # Only save if importance >= this
    
    def calculate_importance(self, item_type: str, data: dict, context: dict = None) -> float:
        """
        Calculate importance score (0.0 to 1.0) for a piece of information.
        Higher score = more important to remember.
        """
        score = 0.5  # neutral baseline
        
        if item_type == 'reflection':
            # High effectiveness = more important
            eff = data.get('effectiveness_score', 0.5)
            score += (eff - 0.5) * 0.3
            
            # Large confidence adjustment = important learning moment
            conf_adj = abs(data.get('confidence_adjustment', 0.0))
            score += conf_adj * 0.5
            
            # Specific strategy advice = worth remembering
            strategy = data.get('strategy_adjustment', '')
            if strategy and len(strategy) > 20:
                score += 0.2
            
            # Tool feedback with low usefulness = important (don't use again)
            tool_feedback = data.get('tool_feedback', {})
            for tool, feedback in tool_feedback.items():
                usefulness = feedback.get('usefulness', 0.5)
                if usefulness < 0.3:
                    score += 0.3  # Remember failures
        
        elif item_type == 'observation':
            # Errors are important to remember
            if 'error' in data:
                score += 0.4
            
            # Large result sets might be important
            if 'results' in data and isinstance(data['results'], list):
                if len(data['results']) > 0:
                    score += 0.2
        
        elif item_type == 'goal_completion':
            # Completed goals are always important
            score = 1.0
        
        elif item_type == 'tool_failure':
            # Tool failures are critical to remember
            score = 0.9
        
        elif item_type == 'learning':
            # Active learning is ALWAYS important - this is knowledge building
            score = 0.95  # Very high importance
            
            # Boost for comprehensive learning (multiple searches)
            if context and context.get('searches', 0) > 1:
                score = 1.0  # Maximum importance for deep learning
            
            # Boost for high confidence
            confidence = data.get('confidence', 0.5)
            if confidence >= 0.8:
                score = min(1.0, score + 0.05)
        
        return max(0.0, min(1.0, score))
    
    def should_save(self, item_type: str, data: dict, context: dict = None) -> bool:
        """Decide if this item is worth saving to persistent memory"""
        importance = self.calculate_importance(item_type, data, context)
        
        # Always save high-importance items
        if importance >= self.importance_threshold:
            return True
        
        # In debug mode, save everything for learning
        if Config.DEBUG:
            return True
        
        return False
    
    def save_if_important(self, key: str, item_type: str, data: dict, context: dict = None, domain: str = "_global") -> bool:
        """Save data to memory only if it meets importance threshold"""
        if not self.should_save(item_type, data, context):
            logging.debug(f"Skipping save for {key} (importance too low)")
            return False
        
        importance = self.calculate_importance(item_type, data, context)
        
        # Enrich data with metadata (now including domain)
        enriched = {
            'data': data,
            'metadata': {
                'importance': importance,
                'type': item_type,
                'timestamp': datetime.utcnow().isoformat(),
                'domain': domain,
                'context': context or {}
            }
        }
        
        result = memory.safe_call('set', key, enriched)
        if result:
            logging.info(f"Saved {item_type} to memory in domain '{domain}' with importance {importance:.2f}")
        return result
    
    def get_important_memories(self, goal: str, limit: int = 5, domain: str = "_global") -> list:
        """Retrieve the most important memories related to a goal in a domain"""
        # This is simplified - in production, you'd query by importance score and domain
        key = f"last_reflection:{goal}:{domain}"
        data = memory.safe_call('get', key)
        if data:
            return [data]
        # Fallback to global if no domain-specific memory
        if domain != "_global":
            key_global = f"last_reflection:{goal}:_global"
            data = memory.safe_call('get', key_global)
            if data:
                return [data]
        return []
    
    def summarize_learnings(self, goal: str, domain: str = "_global") -> dict:
        """Summarize what the agent has learned about this type of goal in a domain"""
        memories = self.get_important_memories(goal, domain=domain)
        
        if not memories:
            return {'summary': 'No prior learnings', 'confidence': 0.0, 'domain': domain}
        
        # Extract key insights
        strategies = []
        tools_to_avoid = []
        avg_effectiveness = 0.0
        
        for mem in memories:
            data = mem.get('data', {}) if isinstance(mem, dict) else mem
            mem_domain = mem.get('metadata', {}).get('domain', '_global') if isinstance(mem, dict) else '_global'
            
            # Only extract if memory's domain matches or is global
            if mem_domain != '_global' and mem_domain != domain:
                continue
            
            if 'strategy_adjustment' in data:
                strategies.append(data['strategy_adjustment'])
            
            if 'tool_feedback' in data:
                for tool, feedback in data['tool_feedback'].items():
                    if feedback.get('usefulness', 0.5) < 0.3:
                        tools_to_avoid.append(tool)
            
            if 'effectiveness_score' in data:
                avg_effectiveness += data['effectiveness_score']
        
        if len(memories) > 0:
            avg_effectiveness /= len(memories)
        
        return {
            'domain': domain,
            'summary': f"Learned from {len(memories)} similar goals in domain '{domain}'",
            'strategies': strategies,
            'tools_to_avoid': list(set(tools_to_avoid)),
            'avg_effectiveness': avg_effectiveness,
            'confidence': min(1.0, len(memories) / 5.0)
        }
    
    def get_all_observations(self, domain: str = "_global") -> list:
        """Get all stored observations for knowledge graph building"""
        # Get all memory keys and extract observations
        observations = []
        
        # Try to retrieve all stored memories from Firebase
        try:
            # Get all memories (this returns a dict-like structure with memory items)
            all_memories = memory.safe_call('get_all') or {}
            
            # Filter and extract observations from all stored items
            for key, value in all_memories.items():
                if not isinstance(value, dict):
                    continue
                
                # Extract data from enriched format if present
                data = value.get('data', value)
                metadata = value.get('metadata', {})
                mem_domain = metadata.get('domain', '_global')
                
                # Include if domain matches or if looking for global
                if domain == "_global" or mem_domain == domain:
                    # Enrich the observation with metadata
                    obs = dict(data) if isinstance(data, dict) else {}
                    obs['timestamp'] = metadata.get('timestamp', '')
                    obs['domain'] = mem_domain
                    obs['importance'] = metadata.get('importance', 0.5)
                    obs['type'] = metadata.get('type', 'unknown')
                    observations.append(obs)
        except Exception as e:
            logging.warning(f"Failed to retrieve all observations: {e}")
            # Fallback: try the old method
            try:
                agent_memory = memory.safe_call('get', 'agent_memory') or []
                for mem in agent_memory:
                    if isinstance(mem, dict):
                        mem_domain = mem.get('domain', '_global')
                        if domain == "_global" or mem_domain == domain:
                            observations.append(mem)
            except:
                pass
        
        return observations
    
    def retrieve_observations(self, goal_pattern: str, domain: str = "_global", top_k: int = 5) -> list:
        """Retrieve observations matching a goal pattern"""
        all_obs = self.get_all_observations(domain)
        
        # Filter by goal pattern (simple substring match)
        matching = []
        for obs in all_obs:
            goal = obs.get('goal', obs.get('original_goal', ''))
            if goal and goal_pattern.lower() in goal.lower():
                matching.append(obs)
        
        # Return top_k most recent
        matching.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return matching[:top_k]

memory_manager = MemoryManager()

