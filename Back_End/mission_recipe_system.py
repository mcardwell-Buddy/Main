"""
Phase 10: Mission Recipe System

Pre-built mission templates (recipes) for common tasks.
Enables quick launch with preset parameters and best-practice configurations.

Recipe categories:
- Web extraction & search
- Data analysis & calculation
- Content generation
- Cross-domain workflows
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from enum import Enum
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class RecipeCategory(Enum):
    """Recipe categories."""
    WEB_EXTRACTION = "web_extraction"
    WEB_SEARCH = "web_search"
    DATA_ANALYSIS = "data_analysis"
    CONTENT_GENERATION = "content_generation"
    WORKFLOW = "workflow"


@dataclass
class RecipeStep:
    """A single step in a recipe workflow."""
    step_name: str
    tool: str                          # web_search, web_extract, calculate, etc.
    parameters: Dict[str, Any]         # Tool-specific parameters
    error_handling: str = "fail"       # fail, continue, skip
    timeout_seconds: int = 300


@dataclass
class MissionRecipe:
    """Pre-built mission template."""
    recipe_id: str
    name: str                          # User-friendly name
    description: str                   # What this recipe does
    category: str                      # web_extraction, web_search, etc.
    version: str = "1.0"
    created_at: str = None
    steps: List[RecipeStep] = field(default_factory=list)
    estimated_duration_minutes: int = 5
    estimated_cost: float = 0.05
    success_rate: float = 0.95         # Based on historical data
    tags: List[str] = field(default_factory=list)  # Searchable tags
    examples: List[Dict[str, Any]] = field(default_factory=list)  # Usage examples
    metadata: Dict[str, Any] = field(default_factory=dict)  # Custom metadata

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()


class MissionRecipeSystem:
    """Manages mission recipe templates."""
    
    def __init__(self, data_dir: str = "./outputs/mission_recipes"):
        """
        Initialize recipe system.
        
        Args:
            data_dir: Directory to persist recipes
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.recipes_file = self.data_dir / "recipes.jsonl"
        self.usage_log = self.data_dir / "usage_log.jsonl"
        
        # In-memory cache
        self._recipes: Dict[str, MissionRecipe] = {}
        self._load_recipes()
        self._create_default_recipes()
        
        logger.info(f"[RECIPES] Initialized with {len(self._recipes)} recipes")
    
    def _load_recipes(self) -> None:
        """Load recipes from persistent storage."""
        if not self.recipes_file.exists():
            return
        
        try:
            with open(self.recipes_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        # Convert step dicts to RecipeStep objects
                        if 'steps' in data and data['steps']:
                            data['steps'] = [RecipeStep(**step) if isinstance(step, dict) else step 
                                            for step in data['steps']]
                        recipe = MissionRecipe(**data)
                        self._recipes[recipe.recipe_id] = recipe
            logger.info(f"[RECIPES] Loaded {len(self._recipes)} recipes from disk")
        except Exception as e:
            logger.error(f"[RECIPES] Error loading recipes: {e}")
    
    def _persist_recipe(self, recipe: MissionRecipe) -> None:
        """Persist a recipe to disk."""
        try:
            recipe_dict = asdict(recipe)
            # Convert RecipeStep objects to dicts
            if recipe_dict['steps']:
                recipe_dict['steps'] = [asdict(step) if hasattr(step, '__dataclass_fields__') else step 
                                       for step in recipe_dict['steps']]
            with open(self.recipes_file, 'a') as f:
                f.write(json.dumps(recipe_dict, default=str) + '\n')
        except Exception as e:
            logger.error(f"[RECIPES] Error persisting recipe: {e}")
    
    def _create_default_recipes(self) -> None:
        """Create default system recipes if not already present."""
        default_recipes = [
            MissionRecipe(
                recipe_id="web_search_basic",
                name="Web Search - Basic",
                description="Simple web search for information",
                category=RecipeCategory.WEB_SEARCH.value,
                version="1.0",
                steps=[
                    RecipeStep(
                        step_name="search",
                        tool="web_search",
                        parameters={
                            "query": "{search_query}",
                            "num_results": 10,
                        }
                    )
                ],
                estimated_duration_minutes=1,
                estimated_cost=0.02,
                success_rate=0.98,
                tags=["search", "web", "quick"],
                examples=[
                    {"input": "search_query: 'best Python libraries 2026'", 
                     "output": "Top 10 relevant results"}
                ]
            ),
            MissionRecipe(
                recipe_id="web_extract_table",
                name="Web Extraction - Table Data",
                description="Extract structured data from a webpage table",
                category=RecipeCategory.WEB_EXTRACTION.value,
                version="1.0",
                steps=[
                    RecipeStep(
                        step_name="navigate",
                        tool="web_navigate",
                        parameters={"url": "{target_url}"}
                    ),
                    RecipeStep(
                        step_name="extract",
                        tool="web_extract",
                        parameters={
                            "selector": "{table_selector}",
                            "format": "table"
                        }
                    )
                ],
                estimated_duration_minutes=3,
                estimated_cost=0.05,
                success_rate=0.92,
                tags=["extraction", "table", "data"],
                examples=[
                    {"input": "target_url: 'example.com/prices', table_selector: 'tbody > tr'",
                     "output": "Structured table data as CSV"}
                ]
            ),
            MissionRecipe(
                recipe_id="calc_financial",
                name="Financial Calculation",
                description="Perform financial calculations and analysis",
                category=RecipeCategory.DATA_ANALYSIS.value,
                version="1.0",
                steps=[
                    RecipeStep(
                        step_name="calculate",
                        tool="calculate",
                        parameters={
                            "expression": "{formula}",
                            "format": "float"
                        }
                    )
                ],
                estimated_duration_minutes=1,
                estimated_cost=0.01,
                success_rate=0.99,
                tags=["calculation", "finance", "math"],
                examples=[
                    {"input": "formula: 'mortgage(500000, 0.065, 360)'",
                     "output": "Monthly payment calculation"}
                ]
            ),
            MissionRecipe(
                recipe_id="content_summarize",
                name="Content Summarization",
                description="Summarize long-form content",
                category=RecipeCategory.CONTENT_GENERATION.value,
                version="1.0",
                steps=[
                    RecipeStep(
                        step_name="extract",
                        tool="web_extract",
                        parameters={"url": "{source_url}"}
                    ),
                    RecipeStep(
                        step_name="summarize",
                        tool="llm_call",
                        parameters={
                            "prompt": "Summarize the following in 3-5 bullet points: {extracted_text}",
                            "model": "gpt-4"
                        }
                    )
                ],
                estimated_duration_minutes=5,
                estimated_cost=0.10,
                success_rate=0.85,
                tags=["summary", "content", "nlp"],
                examples=[
                    {"input": "source_url: 'long-article.com'",
                     "output": "5-point summary of article"}
                ]
            ),
        ]
        
        # Add default recipes if not already present
        for recipe in default_recipes:
            if recipe.recipe_id not in self._recipes:
                self._recipes[recipe.recipe_id] = recipe
                self._persist_recipe(recipe)
                logger.info(f"[RECIPES] Created default recipe: {recipe.recipe_id}")
    
    def create_recipe(
        self,
        name: str,
        description: str,
        category: str,
        steps: List[RecipeStep],
        estimated_duration_minutes: int = 5,
        estimated_cost: float = 0.05,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Create a new mission recipe.
        
        Args:
            name: Recipe name
            description: What it does
            category: Recipe category
            steps: List of recipe steps
            estimated_duration_minutes: Expected duration
            estimated_cost: Estimated cost
            tags: Searchable tags
            metadata: Custom metadata
        
        Returns:
            recipe_id if successful
        """
        try:
            recipe_id = f"recipe_{name.lower().replace(' ', '_')}_{int(datetime.now(timezone.utc).timestamp())}"
            
            recipe = MissionRecipe(
                recipe_id=recipe_id,
                name=name,
                description=description,
                category=category,
                steps=steps,
                estimated_duration_minutes=estimated_duration_minutes,
                estimated_cost=estimated_cost,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            self._recipes[recipe_id] = recipe
            self._persist_recipe(recipe)
            
            logger.info(f"[RECIPES] Created recipe: {recipe_id}")
            return recipe_id
        except Exception as e:
            logger.error(f"[RECIPES] Error creating recipe: {e}")
            return None
    
    def get_recipe(self, recipe_id: str) -> Optional[MissionRecipe]:
        """Get a recipe by ID."""
        return self._recipes.get(recipe_id)
    
    def list_recipes(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[MissionRecipe]:
        """
        List recipes with optional filtering.
        
        Args:
            category: Filter by category
            tag: Filter by tag
        
        Returns:
            List of recipes
        """
        recipes = list(self._recipes.values())
        
        if category:
            recipes = [r for r in recipes if r.category == category]
        
        if tag:
            recipes = [r for r in recipes if tag in r.tags]
        
        return recipes
    
    def search_recipes(self, query: str) -> List[MissionRecipe]:
        """
        Search recipes by name or description.
        
        Args:
            query: Search query
        
        Returns:
            Matching recipes
        """
        query_lower = query.lower()
        return [
            r for r in self._recipes.values()
            if query_lower in r.name.lower() or query_lower in r.description.lower()
        ]
    
    def instantiate_recipe(
        self,
        recipe_id: str,
        parameters: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Instantiate a recipe into a concrete mission.
        
        Replaces {parameter} placeholders with actual values.
        Creates a real mission in mission_store that can be approved and executed.
        
        Args:
            recipe_id: Recipe to instantiate
            parameters: Parameter substitutions
        
        Returns:
            Mission obj with mission_id if successful
        """
        try:
            recipe = self.get_recipe(recipe_id)
            if not recipe:
                logger.error(f"[RECIPES] Recipe {recipe_id} not found")
                return None
            
            # Instantiate steps with parameter substitution
            instantiated_steps = []
            for step in recipe.steps:
                step_dict = asdict(step)
                
                # Replace parameters in step parameters
                params_str = json.dumps(step_dict['parameters'])
                for key, value in parameters.items():
                    params_str = params_str.replace(f"{{{key}}}", str(value))
                step_dict['parameters'] = json.loads(params_str)
                
                instantiated_steps.append(step_dict)
            
            # Replace parameters in objective/description
            instantiated_objective = recipe.description
            for key, value in parameters.items():
                instantiated_objective = instantiated_objective.replace(f"{{{key}}}", str(value))
            
            # CRITICAL FIX: Create mission draft and save to mission_store
            from Back_End.mission_control.mission_draft_builder import MissionDraft
            from Back_End.mission_control.mission_proposal_emitter import emit_mission_proposal
            
            mission_id = f"recipe_{recipe_id}_{int(datetime.now().timestamp())}"
            
            # Create draft from recipe
            draft = MissionDraft(
                mission_id=mission_id,
                source="recipe",
                status="proposed",
                objective_description=instantiated_objective,
                objective_type=recipe.category.lower() if hasattr(recipe.category, 'lower') else str(recipe.category).lower(),
                target_count=None,
                allowed_domains=[],
                max_pages=100,
                max_duration_seconds=recipe.estimated_duration_minutes * 60,
                created_at=datetime.now().isoformat(),
                raw_chat_message=f"Recipe instantiation: {recipe.name}",
                intent_keywords=[recipe_id, str(recipe.category)],
            )
            
            # Emit to mission store (saves to Firebase)
            emission_result = emit_mission_proposal(draft)
            
            # Log usage
            self._log_recipe_usage(recipe_id)
            
            logger.info(f"[RECIPES] Instantiated recipe {recipe_id} → mission {mission_id}")
            
            return {
                "mission_id": mission_id,
                "recipe_id": recipe_id,
                "recipe_name": recipe.name,
                "status": "proposed",
                "objective": instantiated_objective,
                "steps": instantiated_steps,
                "estimated_duration_minutes": recipe.estimated_duration_minutes,
                "estimated_cost": recipe.estimated_cost,
                "emission_result": emission_result,
                "message": f"Mission {mission_id} created from recipe '{recipe.name}'. Approve to execute.",
            }
        except Exception as e:
            logger.error(f"[RECIPES] Error instantiating recipe: {e}", exc_info=True)
            return None
    
    def _log_recipe_usage(self, recipe_id: str) -> bool:
        """Log that a recipe was used."""
        try:
            usage = {
                "recipe_id": recipe_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            with open(self.usage_log, 'a') as f:
                f.write(json.dumps(usage) + '\n')
            return True
        except Exception as e:
            logger.error(f"[RECIPES] Error logging usage: {e}")
            return False


# Global recipe system instance
_recipe_system: Optional[MissionRecipeSystem] = None


def get_recipe_system() -> MissionRecipeSystem:
    """Get or create the mission recipe system."""
    global _recipe_system
    if _recipe_system is None:
        _recipe_system = MissionRecipeSystem()
    return _recipe_system


logger.info("[RECIPES] Module loaded")
