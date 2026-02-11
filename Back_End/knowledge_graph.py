"""
Knowledge Graph Builder: Visualizes Buddy's learned knowledge with semantic relationships
"""

import logging
from typing import Dict, List, Set, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
from Back_End.memory_manager import memory_manager
from Back_End.tool_performance import tracker
from Back_End.tool_registry import tool_registry


class KnowledgeGraph:
    """Builds a robust knowledge graph with semantic relationships, skill tracking, and learning paths"""
    
    def __init__(self):
        self.concept_cache = {}
        self.relationship_cache = {}
        self.skill_levels = defaultdict(lambda: {'beginner': 0, 'intermediate': 0, 'advanced': 0})
    def extract_concepts(self, text: str) -> Set[str]:
        """Extract key concepts from text using simple NLP patterns"""
        if not text:
            return set()
        
        # Simple concept extraction: phrases in quotes or capitalized terms
        concepts = set()
        words = text.lower().split()
        
        # Find capitalized terms (likely concepts)
        for word in text.split():
            if word and word[0].isupper() and len(word) > 2:
                concepts.add(word.lower())
        
        # Simple noun phrase detection (word + "of" + word)
        for i in range(len(words) - 2):
            if words[i + 1] in ['of', 'in', 'about']:
                phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
                if len(phrase) > 5:
                    concepts.add(phrase)
        
        return concepts
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts (0-1)"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_skill_level(self, confidence: float, num_datapoints: int) -> str:
        """Determine skill level based on confidence and experience"""
        if confidence < 0.5 or num_datapoints < 2:
            return 'beginner'
        elif confidence < 0.75 or num_datapoints < 5:
            return 'intermediate'
        else:
            return 'advanced'
    
    def identify_related_concepts(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, List[str]]:
        """Identify which concepts are semantically related"""
        related = defaultdict(set)
        
        # Find concepts that share tools
        topic_nodes = [n for n in nodes if n['type'] == 'topic']
        
        for i, node1 in enumerate(topic_nodes):
            for node2 in topic_nodes[i+1:]:
                # Find shared tools/edges
                shared_tools = 0
                for edge in edges:
                    if (edge['source'] == node1['id'] or edge['source'] == node2['id']) and \
                       (edge['target'] == node1['id'] or edge['target'] == node2['id']):
                        shared_tools += 1
                
                # Calculate semantic similarity
                similarity = self.calculate_semantic_similarity(
                    node1['label'], 
                    node2['label']
                )
                
                # If similar or share tools, they're related
                if similarity > 0.3 or shared_tools > 0:
                    related[node1['id']].add(node2['id'])
                    related[node2['id']].add(node1['id'])
        
        return {k: list(v) for k, v in related.items()}
    
    def get_learning_path_recommendations(self, nodes: List[Dict], edges: List[Dict]) -> List[Dict]:
        """Generate recommended learning paths based on current knowledge"""
        recommendations = []
        
        # Find weak areas (low confidence topics)
        weak_topics = sorted(
            [n for n in nodes if n['type'] == 'topic'],
            key=lambda x: x.get('confidence', 0.5)
        )[:3]
        
        for topic in weak_topics:
            recommendations.append({
                'type': 'strengthen',
                'topic': topic['label'],
                'current_confidence': topic['confidence'],
                'priority': 'high'
            })
        
        # Find adjacent skills (topics connected to mastered areas)
        mastered = [n for n in nodes if n['type'] == 'topic' and n['confidence'] >= 0.8]
        
        for master_topic in mastered:
            related_edges = [e for e in edges if e['source'] == master_topic['id'] or e['target'] == master_topic['id']]
            if related_edges:
                recommendations.append({
                    'type': 'related',
                    'from_topic': master_topic['label'],
                    'num_related': len(related_edges),
                    'priority': 'medium'
                })
        
        return recommendations
    
    def get_graph_data(self, domain: str = "_global") -> Dict:
        """
        Build enhanced knowledge graph with semantic relationships and skill tracking
        
        Returns dict with:
        - nodes: list of {id, label, type, confidence, size, skill_level, concepts}
        - edges: list of {source, target, weight, type, strength}
        - related_concepts: dict mapping node IDs to related concept IDs
        - learning_paths: list of recommended next topics
        - stats: dict of overall stats including skill distribution
        - timeline: confidence progression over time
        """
        nodes = []
        edges = []
        
        # 1. Get all observations from memory
        observations = memory_manager.get_all_observations(domain=domain)
        
        # 2. Build topic nodes from observations with enriched data
        topic_freq = defaultdict(int)
        topic_confidence = defaultdict(list)
        topic_concepts = defaultdict(set)
        topic_timestamps = defaultdict(list)
        topic_tools = defaultdict(set)
        
        for obs in observations:
            obs_type = obs.get('type', 'unknown')
            topic = None
            
            # For learning observations, use 'topic' field
            if obs_type == 'learning':
                topic = obs.get('topic', '')
                confidence = obs.get('confidence', 0.5)
                # Extract key concepts from learning
                for concept in obs.get('key_concepts', [])[:3]:
                    if concept:
                        topic_concepts[topic if topic else "Learning"].add(str(concept))
            
            # For reflections, use tool feedback to infer topics
            elif obs_type == 'reflection':
                # Reflections don't have explicit topics, but we can infer from tool usage
                tool_feedback = obs.get('tool_feedback', {})
                if tool_feedback:
                    # Create a synthetic "Tool Mastery" topic
                    topic = "Tool Application & Effectiveness"
                    confidence = obs.get('effectiveness_score', 0.5)
                else:
                    continue
            
            # For observation errors, treat as learning opportunities
            elif obs_type == 'observation':
                error_msg = obs.get('error', '')
                if error_msg:
                    # Extract error type as a topic
                    if 'Invalid' in error_msg or 'invalid' in error_msg:
                        topic = "Input Validation & Sanitization"
                    elif 'timeout' in error_msg.lower():
                        topic = "Performance & Timeouts"
                    elif 'connection' in error_msg.lower():
                        topic = "Network & Connectivity"
                    else:
                        topic = "Error Handling & Debugging"
                    confidence = 0.6 + (obs.get('importance', 0.5) * 0.2)
            
            # For other observations, use generic topic
            else:
                topic = obs.get('topic') or obs.get('goal_pattern', '') or obs.get('goal', '') or obs.get('original_goal', '')
                confidence = obs.get('confidence', 0.5)
            
            # Clean up topic to a reasonable length
            if topic and len(topic.strip()) > 3:
                topic = topic.strip()[:60]  # Truncate very long topics
                topic_freq[topic] += 1
                
                # Ensure confidence is valid
                if isinstance(confidence, (int, float)):
                    confidence = float(min(1.0, max(0.0, confidence)))
                    topic_confidence[topic].append(confidence)
                else:
                    topic_confidence[topic].append(0.5)
                
                # Extract concepts from observation
                result = obs.get('result', '')
                description = obs.get('description', '')
                synthesis = obs.get('synthesis', '')
                summary = obs.get('summary', '')
                what_worked = obs.get('what_worked', '')
                what_not_worked = obs.get('what_did_not_work', '')
                combined_text = f"{result} {description} {synthesis} {summary} {what_worked} {what_not_worked}"
                
                if combined_text.strip():
                    concepts = self.extract_concepts(combined_text)
                    topic_concepts[topic].update(concepts)
                
                # Track timestamps for timeline
                timestamp = obs.get('timestamp', datetime.now().isoformat())
                if timestamp:
                    topic_timestamps[topic].append(timestamp)
                
                # Track tools used
                if obs_type == 'reflection':
                    for tool in obs.get('tool_feedback', {}).keys():
                        topic_tools[topic].add(tool)
        
        # Create nodes for topics with skill levels
        skill_distribution = defaultdict(int)
        for topic, freq in topic_freq.items():
            if freq > 0:
                avg_confidence = sum(topic_confidence[topic]) / len(topic_confidence[topic]) if topic_confidence[topic] else 0.5
                skill_level = self.calculate_skill_level(avg_confidence, freq)
                skill_distribution[skill_level] += 1
                
                node = {
                    'id': f"topic_{topic}",
                    'label': topic[:50],
                    'type': 'topic',
                    'confidence': avg_confidence,
                    'size': min(60, 10 + freq * 5),
                    'data_points': freq,
                    'skill_level': skill_level,
                    'concepts': list(topic_concepts[topic])[:5],
                    'last_updated': max(topic_timestamps[topic]) if topic_timestamps[topic] else None,
                    'confidence_trend': self.calculate_confidence_trend(topic_confidence[topic])
                }
                nodes.append(node)
        
        # 3. Build tool nodes with enhanced metrics
        for tool_name, tool_info in tool_registry.tools.items():
            stats = tracker.get_stats(tool_name, domain=domain)
            if stats and stats['total_calls'] > 0:
                success_rate = stats['successful_calls'] / stats['total_calls']
                usefulness = tracker.get_usefulness_score(tool_name, domain=domain)
                
                nodes.append({
                    'id': f"tool_{tool_name}",
                    'label': tool_name,
                    'type': 'tool',
                    'confidence': success_rate,
                    'size': min(50, 10 + stats['total_calls'] * 2),
                    'success_rate': success_rate,
                    'usefulness': usefulness,
                    'total_calls': stats['total_calls'],
                    'efficiency': stats.get('avg_time', 0),
                    'category': tool_info.get('category', 'general')
                })
        
        # 4. Build edges with better relationship types
        edge_map = defaultdict(lambda: {'count': 0, 'weights': []})
        
        for obs in observations:
            # Extract topic same as above
            topic = obs.get('topic') or obs.get('goal_pattern', '') or obs.get('goal', '') or obs.get('original_goal', '')
            topic = topic[:60] if topic and len(topic) > 60 else topic
            
            # Get tool name - may be stored differently
            tool_used = obs.get('tool_name') or obs.get('tool')
            
            if topic and len(topic) > 3 and tool_used:
                edge_key = (f"topic_{topic}", f"tool_{tool_used}")
                edge_map[edge_key]['count'] += 1
                
                # Track confidence for edge weight
                confidence = obs.get('confidence', 0.5)
                if isinstance(confidence, (int, float)):
                    edge_map[edge_key]['weights'].append(float(confidence))
        
        # Build final edges with calculated weights and relationship strength
        for (source, target), data in edge_map.items():
            avg_weight = sum(data['weights']) / len(data['weights']) if data['weights'] else 0.5
            strength = 'strong' if avg_weight > 0.75 else 'medium' if avg_weight > 0.5 else 'weak'
            
            edges.append({
                'source': source,
                'target': target,
                'weight': data['count'],
                'confidence': avg_weight,
                'strength': strength,
                'type': 'uses'
            })
        
        # 5. Identify related concepts
        related_concepts = self.identify_related_concepts(nodes, edges)
        
        # 6. Generate learning paths
        learning_paths = self.get_learning_path_recommendations(nodes, edges)
        
        # 7. Calculate confidence progression timeline
        timeline_data = self.calculate_confidence_timeline(observations, domain)
        
        # 8. Calculate overall stats
        stats = {
            'total_topics': len(topic_freq),
            'total_tools': sum(1 for n in nodes if n['type'] == 'tool'),
            'total_connections': len(edges),
            'avg_confidence': sum(n['confidence'] for n in nodes) / len(nodes) if nodes else 0,
            'most_used_tool': max(
                (n for n in nodes if n['type'] == 'tool'),
                key=lambda n: n.get('total_calls', 0),
                default=None
            ),
            'strongest_topic': max(
                (n for n in nodes if n['type'] == 'topic'),
                key=lambda n: n.get('data_points', 0),
                default=None
            ),
            'skill_distribution': dict(skill_distribution),
            'mastered_skills': sum(1 for n in nodes if n['type'] == 'topic' and n['confidence'] >= 0.8),
            'learning_efficiency': self.calculate_learning_efficiency(observations, nodes)
        }
        
        return {
            'nodes': nodes,
            'edges': edges,
            'related_concepts': related_concepts,
            'learning_paths': learning_paths,
            'timeline': timeline_data,
            'stats': stats,
            'domain': domain,
            'generated_at': datetime.now().isoformat()
        }
    
    def calculate_confidence_trend(self, confidence_values: List[float]) -> str:
        """Determine if confidence is improving, stable, or declining"""
        if len(confidence_values) < 2:
            return 'stable'
        
        recent = confidence_values[-3:] if len(confidence_values) >= 3 else confidence_values
        older = confidence_values[:-3] if len(confidence_values) >= 3 else []
        
        if not older:
            return 'new'
        
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        
        diff = recent_avg - older_avg
        if diff > 0.1:
            return 'improving'
        elif diff < -0.1:
            return 'declining'
        else:
            return 'stable'
    
    def calculate_confidence_timeline(self, observations: List[Dict], domain: str) -> List[Dict]:
        """Calculate how confidence has evolved over time"""
        timeline = []
        
        # Group by date
        by_date = defaultdict(list)
        for obs in observations:
            timestamp = obs.get('timestamp', '')
            if timestamp:
                date = timestamp[:10]
                confidence = obs.get('confidence', 0.5)
                by_date[date].append(confidence)
        
        # Calculate daily averages
        for date in sorted(by_date.keys()):
            confidences = by_date[date]
            timeline.append({
                'date': date,
                'avg_confidence': sum(confidences) / len(confidences),
                'num_learnings': len(confidences)
            })
        
        return timeline[-30:]
    
    def calculate_learning_efficiency(self, observations: List[Dict], nodes: List[Dict]) -> float:
        """Calculate how efficiently the system is learning"""
        if len(observations) < 2:
            return 0.5
        
        first_confidence = observations[0].get('confidence', 0.5)
        last_confidence = observations[-1].get('confidence', 0.5)
        
        growth = (last_confidence - first_confidence) / len(observations)
        return min(1.0, max(0.0, growth + 0.5))


# Singleton instance
knowledge_graph = KnowledgeGraph()

