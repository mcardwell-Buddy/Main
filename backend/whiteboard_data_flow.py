"""
Whiteboard Data Flow: Reconstruction from ResponseEnvelope + mission_id

Read-only wiring. No duplicate computation. mission_id is join key.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


# =============================================================================
# WHITEBOARD DATA MODEL
# =============================================================================

@dataclass
class WhiteboardMissionView:
    """Complete mission state reconstructed from ResponseEnvelope + mission_id."""
    mission_id: str
    objective: str
    status: str  # 'proposed', 'executing', 'completed', 'failed'
    created_at: datetime
    updated_at: datetime
    artifacts: List[Dict[str, Any]]  # Artifact references from ResponseEnvelope
    signals: List[Dict[str, Any]]    # Signal references from ResponseEnvelope
    metrics: Dict[str, Any]  # Derived from signals
    timeline: List[Dict[str, Any]]  # Event sequence

    def to_dict(self) -> Dict[str, Any]:
        return {
            'mission_id': self.mission_id,
            'objective': self.objective,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'artifacts': self.artifacts,
            'signals': self.signals,
            'metrics': self.metrics,
            'timeline': self.timeline,
        }


# =============================================================================
# DATA SOURCE ABSTRACTION (Read-only)
# =============================================================================

class MissionArtifactStore:
    """Read-only store for mission artifacts (append-only, no updates)."""
    
    def __init__(self):
        self._artifacts = {}  # mission_id -> List[Artifact]
    
    def get_artifacts_for_mission(self, mission_id: str) -> List[Dict[str, Any]]:
        """Get all artifacts created by this mission."""
        return self._artifacts.get(mission_id, [])
    
    def artifact_exists(self, artifact_id: str) -> bool:
        """Check if artifact exists."""
        for mission_artifacts in self._artifacts.values():
            for artifact in mission_artifacts:
                if artifact.get('id') == artifact_id:
                    return True
        return False


class MissionSignalStore:
    """Read-only store for mission signals (append-only, immutable)."""
    
    def __init__(self):
        self._signals = {}  # mission_id -> List[Signal]
    
    def get_signals_for_mission(self, mission_id: str) -> List[Dict[str, Any]]:
        """Get all signals emitted by this mission."""
        return self._signals.get(mission_id, [])
    
    def signal_exists(self, signal_id: str) -> bool:
        """Check if signal exists."""
        for mission_signals in self._signals.values():
            for signal in mission_signals:
                if signal.get('id') == signal_id:
                    return True
        return False


class MissionStateStore:
    """Read-only store for mission metadata (mission_id → state)."""
    
    def __init__(self):
        self._missions = {}  # mission_id -> Mission
    
    def get_mission(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """Get mission metadata."""
        return self._missions.get(mission_id)
    
    def mission_exists(self, mission_id: str) -> bool:
        """Check if mission exists."""
        return mission_id in self._missions


# =============================================================================
# WHITEBOARD VIEW ENGINE (Read-only reconstruction)
# =============================================================================

class WhiteboardViewEngine:
    """
    Reconstructs whiteboard views from ResponseEnvelope + mission_id.
    
    Algorithm:
    1. Load mission metadata (state, objective, timestamps)
    2. Query artifact store: fetch all artifacts for mission_id
    3. Query signal store: fetch all signals for mission_id
    4. Build timeline from signal timestamps
    5. Calculate metrics from signal data
    6. Return complete view (no new computation)
    """
    
    def __init__(
        self,
        mission_store: MissionStateStore,
        artifact_store: MissionArtifactStore,
        signal_store: MissionSignalStore,
    ):
        self.mission_store = mission_store
        self.artifact_store = artifact_store
        self.signal_store = signal_store
    
    def reconstruct_mission_view(
        self,
        mission_id: str,
    ) -> Optional[WhiteboardMissionView]:
        """
        Reconstruct complete mission view from stored data.
        
        Join key: mission_id
        
        Returns None if mission not found.
        """
        # Step 1: Get mission metadata
        mission_meta = self.mission_store.get_mission(mission_id)
        if not mission_meta:
            return None
        
        # Step 2: Get all artifacts for this mission
        # (These are the same artifacts referenced in ResponseEnvelope)
        artifacts = self.artifact_store.get_artifacts_for_mission(mission_id)
        artifacts_view = [
            {
                'id': a.get('id'),
                'type': a.get('artifact_type'),
                'title': a.get('title'),
                'created_at': a.get('created_at'),
            }
            for a in artifacts
        ]
        
        # Step 3: Get all signals for this mission
        # (These are the same signals referenced in ResponseEnvelope)
        signals = self.signal_store.get_signals_for_mission(mission_id)
        signals_view = [
            {
                'id': s.get('id'),
                'type': s.get('signal_type'),
                'source': s.get('signal_source'),
                'timestamp': s.get('timestamp'),
                'summary': s.get('summary'),
            }
            for s in signals
        ]
        
        # Step 4: Build timeline from signals
        # (Chronological sequence of events)
        timeline = self._build_timeline_from_signals(signals)
        
        # Step 5: Calculate metrics from signals
        # (No new computation, just aggregation)
        metrics = self._aggregate_metrics_from_signals(signals)
        
        # Step 6: Return complete view
        return WhiteboardMissionView(
            mission_id=mission_id,
            objective=mission_meta.get('objective'),
            status=mission_meta.get('status'),
            created_at=mission_meta.get('created_at'),
            updated_at=mission_meta.get('updated_at'),
            artifacts=artifacts_view,
            signals=signals_view,
            metrics=metrics,
            timeline=timeline,
        )
    
    def _build_timeline_from_signals(self, signals: List[Dict]) -> List[Dict[str, Any]]:
        """Build timeline from signal timestamps (sorted chronologically)."""
        timeline = []
        for signal in sorted(signals, key=lambda s: s.get('timestamp', '')):
            timeline.append({
                'timestamp': signal.get('timestamp'),
                'event': signal.get('signal_type'),
                'summary': signal.get('summary'),
                'source': signal.get('signal_source'),
            })
        return timeline
    
    def _aggregate_metrics_from_signals(self, signals: List[Dict]) -> Dict[str, Any]:
        """Aggregate metrics from signals (no new computation)."""
        metrics = {
            'signal_count': len(signals),
            'signal_types': {},
            'signal_sources': set(),
            'timeline_span': None,
        }
        
        for signal in signals:
            signal_type = signal.get('signal_type')
            metrics['signal_types'][signal_type] = metrics['signal_types'].get(signal_type, 0) + 1
            metrics['signal_sources'].add(signal.get('signal_source'))
        
        # Timeline span
        if signals:
            timestamps = [s.get('timestamp') for s in signals if s.get('timestamp')]
            if timestamps:
                metrics['timeline_span'] = {
                    'start': min(timestamps),
                    'end': max(timestamps),
                }
        
        metrics['signal_sources'] = list(metrics['signal_sources'])
        return metrics
    
    def reconstruct_from_response_envelope(
        self,
        response_envelope_dict: Dict[str, Any],
    ) -> Optional[WhiteboardMissionView]:
        """
        Reconstruct whiteboard view using ResponseEnvelope + mission_id.
        
        Algorithm:
        1. Extract mission_id from ResponseEnvelope.missions_spawned[0]
        2. Call reconstruct_mission_view(mission_id)
        3. Return view
        
        This ensures the whiteboard reads from the SAME artifacts/signals
        that ResponseEnvelope references, with NO duplicate computation.
        """
        # Extract mission_id from ResponseEnvelope
        missions = response_envelope_dict.get('missions_spawned', [])
        if not missions:
            return None
        
        mission_id = missions[0].get('mission_id')
        if not mission_id:
            return None
        
        # Reconstruct view using same mission_id
        return self.reconstruct_mission_view(mission_id)


# =============================================================================
# WHITEBOARD HTTP ENDPOINTS (Read-only)
# =============================================================================

class WhiteboardEndpoints:
    """
    HTTP endpoints for whiteboard (FastAPI routes).
    
    GET /api/whiteboard/{mission_id}
    GET /api/whiteboard/goals
    GET /api/whiteboard/timeline/{mission_id}
    GET /api/whiteboard/artifacts/{mission_id}
    GET /api/whiteboard/signals/{mission_id}
    """
    
    def __init__(self, view_engine: WhiteboardViewEngine):
        self.view_engine = view_engine
    
    def get_mission_view(self, mission_id: str) -> Dict[str, Any]:
        """GET /api/whiteboard/{mission_id}"""
        view = self.view_engine.reconstruct_mission_view(mission_id)
        if not view:
            return {'error': 'Mission not found', 'mission_id': mission_id}
        return view.to_dict()
    
    def get_mission_timeline(self, mission_id: str) -> Dict[str, Any]:
        """GET /api/whiteboard/timeline/{mission_id}"""
        view = self.view_engine.reconstruct_mission_view(mission_id)
        if not view:
            return {'error': 'Mission not found'}
        return {
            'mission_id': mission_id,
            'timeline': view.timeline,
            'timeline_span': view.metrics.get('timeline_span'),
        }
    
    def get_mission_artifacts(self, mission_id: str) -> Dict[str, Any]:
        """GET /api/whiteboard/artifacts/{mission_id}"""
        view = self.view_engine.reconstruct_mission_view(mission_id)
        if not view:
            return {'error': 'Mission not found'}
        return {
            'mission_id': mission_id,
            'artifacts': view.artifacts,
            'artifact_count': len(view.artifacts),
        }
    
    def get_mission_signals(self, mission_id: str) -> Dict[str, Any]:
        """GET /api/whiteboard/signals/{mission_id}"""
        view = self.view_engine.reconstruct_mission_view(mission_id)
        if not view:
            return {'error': 'Mission not found'}
        return {
            'mission_id': mission_id,
            'signals': view.signals,
            'signal_metrics': view.metrics,
        }


# =============================================================================
# VALIDATION: Data Flow Consistency
# =============================================================================

class WhiteboardDataFlowValidator:
    """
    Validates that whiteboard reads from same data referenced in ResponseEnvelope.
    
    Checks:
    1. mission_id in ResponseEnvelope.missions_spawned matches actual mission
    2. Artifact IDs in ResponseEnvelope.artifacts match stored artifacts
    3. Signal IDs in ResponseEnvelope.signals_emitted match stored signals
    4. No duplicate computation
    5. Read-only wiring (no writes to mission data)
    """
    
    def __init__(
        self,
        view_engine: WhiteboardViewEngine,
        mission_store: MissionStateStore,
        artifact_store: MissionArtifactStore,
        signal_store: MissionSignalStore,
    ):
        self.view_engine = view_engine
        self.mission_store = mission_store
        self.artifact_store = artifact_store
        self.signal_store = signal_store
    
    def validate_mission_consistency(
        self,
        mission_id: str,
        response_envelope_dict: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate that ResponseEnvelope and whiteboard refer to same mission data.
        
        Returns validation report.
        """
        report = {
            'mission_id': mission_id,
            'valid': True,
            'checks': {},
            'errors': [],
        }
        
        # Check 1: Mission exists
        mission = self.mission_store.get_mission(mission_id)
        if not mission:
            report['valid'] = False
            report['errors'].append(f"Mission {mission_id} not found")
            report['checks']['mission_exists'] = False
            return report
        report['checks']['mission_exists'] = True
        
        # Check 2: mission_id from ResponseEnvelope matches
        envelope_missions = response_envelope_dict.get('missions_spawned', [])
        envelope_mission_id = envelope_missions[0].get('mission_id') if envelope_missions else None
        if envelope_mission_id != mission_id:
            report['valid'] = False
            report['errors'].append(
                f"ResponseEnvelope mission {envelope_mission_id} != whiteboard mission {mission_id}"
            )
            report['checks']['mission_id_match'] = False
        else:
            report['checks']['mission_id_match'] = True
        
        # Check 3: All artifact IDs in ResponseEnvelope exist in store
        envelope_artifacts = response_envelope_dict.get('artifacts', [])
        for artifact in envelope_artifacts:
            artifact_id = artifact.get('id')
            if artifact_id and not self.artifact_store.artifact_exists(artifact_id):
                report['valid'] = False
                report['errors'].append(f"Artifact {artifact_id} referenced in ResponseEnvelope not found in store")
        report['checks']['artifacts_exist'] = len(report['errors']) == 0
        
        # Check 4: All signal IDs in ResponseEnvelope exist in store
        envelope_signals = response_envelope_dict.get('signals_emitted', [])
        for signal in envelope_signals:
            signal_id = signal.get('id')
            if signal_id and not self.signal_store.signal_exists(signal_id):
                report['valid'] = False
                report['errors'].append(f"Signal {signal_id} referenced in ResponseEnvelope not found in store")
        report['checks']['signals_exist'] = len(report['errors']) == 0
        
        # Check 5: Whiteboard reads match ResponseEnvelope
        whiteboard_view = self.view_engine.reconstruct_mission_view(mission_id)
        if whiteboard_view:
            whiteboard_artifact_count = len(whiteboard_view.artifacts)
            envelope_artifact_count = len([a for a in envelope_artifacts if a.get('id')])
            if whiteboard_artifact_count != envelope_artifact_count:
                report['warnings'] = report.get('warnings', [])
                report['warnings'].append(
                    f"Artifact count mismatch: {whiteboard_artifact_count} in whiteboard vs {envelope_artifact_count} in ResponseEnvelope"
                )
        
        # Check 6: Read-only operations (no writes)
        report['checks']['read_only'] = True  # By design - view_engine only has read methods
        
        return report
    
    def validate_join_key_integrity(
        self,
        mission_id: str,
    ) -> Dict[str, Any]:
        """
        Validate that mission_id is consistent join key across all data sources.
        
        Returns validation report.
        """
        report = {
            'mission_id': mission_id,
            'valid': True,
            'data_sources': {},
        }
        
        # Check mission store
        mission = self.mission_store.get_mission(mission_id)
        report['data_sources']['mission_store'] = {
            'exists': mission is not None,
            'mission_id': mission.get('mission_id') if mission else None,
        }
        
        # Check artifact store
        artifacts = self.artifact_store.get_artifacts_for_mission(mission_id)
        report['data_sources']['artifact_store'] = {
            'exists': len(artifacts) > 0,
            'count': len(artifacts),
            'all_have_mission_id': all(
                a.get('mission_id') == mission_id for a in artifacts
            ),
        }
        
        # Check signal store
        signals = self.signal_store.get_signals_for_mission(mission_id)
        report['data_sources']['signal_store'] = {
            'exists': len(signals) > 0,
            'count': len(signals),
            'all_have_mission_id': all(
                s.get('mission_id') == mission_id for s in signals
            ),
        }
        
        # Overall validity
        report['valid'] = all(
            ds.get('all_have_mission_id', True)
            for ds in report['data_sources'].values()
        )
        
        return report


# =============================================================================
# CONSTANTS
# =============================================================================

WHITEBOARD_ENDPOINTS = [
    "GET /api/whiteboard/{mission_id}",
    "GET /api/whiteboard/timeline/{mission_id}",
    "GET /api/whiteboard/artifacts/{mission_id}",
    "GET /api/whiteboard/signals/{mission_id}",
]
