"""
Result Presenter: Smart visualization routing for mission results

Maps tool outcomes → optimal visualization strategies.

Philosophy:
- Right visualization for right data type
- Preserve full data (no summarization)
- Multiple views when valuable (table + chart)
- Allow raw data export

NO execution. Pure routing/recommendation. Deterministic only.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class VisualizationType(Enum):
    """Visualization strategy for different data types."""
    TABLE = "table"  # Structured tabular data
    CHART = "chart"  # Numeric data (bar, line, pie)
    DOCUMENT = "document"  # Text content (markdown, HTML)
    TIMELINE = "timeline"  # Time-series or sequential events
    MAP = "map"  # Geographic data
    GALLERY = "gallery"  # Images, media
    CODE = "code"  # Code snippets
    JSON = "json"  # Raw JSON viewer
    MIXED = "mixed"  # Multiple visualization types


@dataclass
class VisualizationStrategy:
    """Recommended visualization for artifact/result."""
    primary_type: VisualizationType
    secondary_types: List[VisualizationType] = field(default_factory=list)
    
    # Configuration for visualization
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Data transformations recommended
    transformations: List[str] = field(default_factory=list)
    
    # Export options
    export_formats: List[str] = field(default_factory=list)
    
    # UI hints
    suggested_height: Optional[str] = None  # e.g., "400px", "auto"
    collapsible: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            'primary_type': self.primary_type.value,
            'secondary_types': [t.value for t in self.secondary_types],
            'config': self.config,
            'transformations': self.transformations,
            'export_formats': self.export_formats,
            'suggested_height': self.suggested_height,
            'collapsible': self.collapsible
        }


@dataclass
class PresentedResult:
    """Mission result with visualization strategy."""
    mission_id: str
    tool_used: str
    result_data: Any  # Original data (preserved)
    visualization_strategy: VisualizationStrategy
    summary: Optional[str] = None  # Brief text summary (if applicable)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            'mission_id': self.mission_id,
            'tool_used': self.tool_used,
            'result_data': self.result_data,
            'visualization_strategy': self.visualization_strategy.to_dict(),
            'summary': self.summary
        }


class ResultPresenter:
    """
    Maps tool results to optimal visualization strategies.
    
    Analyzes:
    - Tool type (web_search, llm_call, database_query, etc.)
    - Data shape (array, object, string, etc.)
    - Data content (numbers, text, dates, etc.)
    
    Recommends:
    - Primary visualization type
    - Secondary views (if valuable)
    - Configuration options
    - Export formats
    """
    
    # Tool → default visualization mapping
    TOOL_VISUALIZATION_MAP = {
        'web_search': VisualizationType.TABLE,
        'serp_search': VisualizationType.TABLE,
        'google_search': VisualizationType.TABLE,
        'llm_call': VisualizationType.DOCUMENT,
        'database_query': VisualizationType.TABLE,
        'calendar_query': VisualizationType.TIMELINE,
        'image_search': VisualizationType.GALLERY,
        'code_generation': VisualizationType.CODE,
        'api_call': VisualizationType.JSON
    }
    
    def __init__(self):
        logger.info("ResultPresenter initialized")
    
    def present_result(
        self,
        mission_id: str,
        tool_used: str,
        result_data: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> PresentedResult:
        """
        Analyze result and determine visualization strategy.
        
        Args:
            mission_id: Mission identifier
            tool_used: Tool that produced the result
            result_data: Actual result data
            context: Optional context (data schema, user preferences, etc.)
            
        Returns:
            PresentedResult: Result with visualization strategy
        """
        logger.info(f"Presenting result for mission {mission_id} (tool: {tool_used})")
        
        # Determine visualization strategy
        strategy = self._determine_strategy(tool_used, result_data, context)
        
        # Generate summary if applicable
        summary = self._generate_summary(tool_used, result_data, strategy)
        
        return PresentedResult(
            mission_id=mission_id,
            tool_used=tool_used,
            result_data=result_data,
            visualization_strategy=strategy,
            summary=summary
        )
    
    def _determine_strategy(
        self,
        tool_used: str,
        result_data: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> VisualizationStrategy:
        """Determine optimal visualization strategy."""
        
        # Start with tool-based default
        primary_type = self.TOOL_VISUALIZATION_MAP.get(
            tool_used.lower(),
            VisualizationType.JSON  # Fallback
        )
        
        # Analyze data shape to refine strategy
        data_analysis = self._analyze_data_shape(result_data)
        
        # Override primary type based on data analysis
        if data_analysis['is_array'] and data_analysis['has_numeric']:
            # Array with numbers → consider chart
            primary_type = VisualizationType.CHART
            secondary_types = [VisualizationType.TABLE]
        elif data_analysis['is_array'] and data_analysis['has_objects']:
            # Array of objects → table
            primary_type = VisualizationType.TABLE
            secondary_types = []
        elif data_analysis['is_text'] and data_analysis['length'] > 500:
            # Long text → document
            primary_type = VisualizationType.DOCUMENT
            secondary_types = []
        elif data_analysis['has_time_series']:
            # Time series data → timeline
            primary_type = VisualizationType.TIMELINE
            secondary_types = [VisualizationType.CHART]
        else:
            # Keep tool-based default
            secondary_types = []
        
        # Build configuration
        config = self._build_config(primary_type, data_analysis)
        
        # Determine export formats
        export_formats = self._determine_export_formats(primary_type, data_analysis)
        
        # Determine transformations
        transformations = self._determine_transformations(data_analysis)
        
        # UI hints
        suggested_height = self._suggest_height(primary_type, data_analysis)
        collapsible = data_analysis.get('length', 0) > 1000
        
        return VisualizationStrategy(
            primary_type=primary_type,
            secondary_types=secondary_types,
            config=config,
            transformations=transformations,
            export_formats=export_formats,
            suggested_height=suggested_height,
            collapsible=collapsible
        )
    
    def _analyze_data_shape(self, data: Any) -> Dict[str, Any]:
        """Analyze data structure and content."""
        analysis = {
            'is_array': False,
            'is_object': False,
            'is_text': False,
            'has_numeric': False,
            'has_objects': False,
            'has_time_series': False,
            'length': 0,
            'complexity': 'simple'
        }
        
        if isinstance(data, list):
            analysis['is_array'] = True
            analysis['length'] = len(data)
            
            if data:
                first_item = data[0]
                if isinstance(first_item, dict):
                    analysis['has_objects'] = True
                    analysis['complexity'] = 'structured'
                    
                    # Check for numeric fields
                    if any(isinstance(v, (int, float)) for v in first_item.values()):
                        analysis['has_numeric'] = True
                    
                    # Check for time fields
                    if any(k.lower() in ['date', 'time', 'timestamp', 'created_at'] for k in first_item.keys()):
                        analysis['has_time_series'] = True
                
                elif isinstance(first_item, (int, float)):
                    analysis['has_numeric'] = True
        
        elif isinstance(data, dict):
            analysis['is_object'] = True
            analysis['length'] = len(data)
            analysis['complexity'] = 'structured'
            
            # Check for numeric values
            if any(isinstance(v, (int, float)) for v in data.values()):
                analysis['has_numeric'] = True
        
        elif isinstance(data, str):
            analysis['is_text'] = True
            analysis['length'] = len(data)
            analysis['complexity'] = 'simple' if len(data) < 500 else 'complex'
        
        return analysis
    
    def _build_config(
        self,
        viz_type: VisualizationType,
        data_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build visualization-specific configuration."""
        config = {}
        
        if viz_type == VisualizationType.TABLE:
            config['sortable'] = True
            config['filterable'] = data_analysis['length'] > 10
            config['paginated'] = data_analysis['length'] > 50
            config['page_size'] = 25
        
        elif viz_type == VisualizationType.CHART:
            if data_analysis['has_numeric']:
                config['chart_type'] = 'bar'  # Default
                config['allow_type_switch'] = True
                config['chart_types'] = ['bar', 'line', 'pie']
            config['responsive'] = True
        
        elif viz_type == VisualizationType.DOCUMENT:
            config['format'] = 'markdown'
            config['syntax_highlight'] = True
            config['line_numbers'] = data_analysis['length'] > 100
        
        elif viz_type == VisualizationType.TIMELINE:
            config['groupable'] = True
            config['zoomable'] = data_analysis['length'] > 20
        
        elif viz_type == VisualizationType.CODE:
            config['language'] = 'python'  # Default
            config['theme'] = 'vs-dark'
            config['line_numbers'] = True
            config['copy_button'] = True
        
        elif viz_type == VisualizationType.JSON:
            config['collapsible_nodes'] = True
            config['syntax_highlight'] = True
            config['copy_button'] = True
        
        return config
    
    def _determine_export_formats(
        self,
        viz_type: VisualizationType,
        data_analysis: Dict[str, Any]
    ) -> List[str]:
        """Determine available export formats."""
        formats = ['JSON']  # Always offer JSON
        
        if viz_type == VisualizationType.TABLE:
            formats.extend(['CSV', 'Excel'])
        
        elif viz_type == VisualizationType.CHART:
            formats.extend(['PNG', 'SVG', 'PDF'])
        
        elif viz_type == VisualizationType.DOCUMENT:
            formats.extend(['Markdown', 'HTML', 'PDF'])
        
        elif viz_type == VisualizationType.CODE:
            formats.append('Text')
        
        return formats
    
    def _determine_transformations(self, data_analysis: Dict[str, Any]) -> List[str]:
        """Determine recommended data transformations."""
        transformations = []
        
        if data_analysis['is_array'] and data_analysis['has_numeric']:
            transformations.extend(['sort', 'filter', 'aggregate'])
        
        if data_analysis['has_time_series']:
            transformations.extend(['group_by_date', 'date_range_filter'])
        
        if data_analysis['is_text'] and data_analysis['length'] > 500:
            transformations.append('truncate')
        
        return transformations
    
    def _suggest_height(
        self,
        viz_type: VisualizationType,
        data_analysis: Dict[str, Any]
    ) -> str:
        """Suggest visualization height."""
        if viz_type == VisualizationType.TABLE:
            if data_analysis['length'] > 20:
                return "500px"
            else:
                return "auto"
        
        elif viz_type == VisualizationType.CHART:
            return "400px"
        
        elif viz_type == VisualizationType.DOCUMENT:
            if data_analysis['length'] > 1000:
                return "600px"
            else:
                return "auto"
        
        elif viz_type == VisualizationType.TIMELINE:
            return "500px"
        
        else:
            return "auto"
    
    def _generate_summary(
        self,
        tool_used: str,
        result_data: Any,
        strategy: VisualizationStrategy
    ) -> Optional[str]:
        """Generate brief text summary of result."""
        if isinstance(result_data, list):
            count = len(result_data)
            return f"{tool_used} returned {count} result{'s' if count != 1 else ''}"
        
        elif isinstance(result_data, dict):
            keys = len(result_data)
            return f"{tool_used} returned data with {keys} field{'s' if keys != 1 else ''}"
        
        elif isinstance(result_data, str):
            length = len(result_data)
            words = len(result_data.split())
            return f"{tool_used} returned text ({words} words, {length} characters)"
        
        else:
            return f"{tool_used} completed successfully"

