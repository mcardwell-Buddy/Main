# Phase 8 Architecture: Workflow Authoring & Safe Modification Layer

Generated: 2026-02-05

## Purpose
Phase 8 introduces a read-only execution authoring environment that enables users to design, simulate, and version workflows without touching Phase 1–7 execution logic. All operations are in-memory and dry-run only.

## Boundaries (Hard Constraints)
- No changes to Phase 1–7 execution code
- No tool dispatch, scheduler controls, or live execution
- No new backend APIs that mutate state
- Authoring operates on immutable snapshots and local JSON only

## UI Components (Phase 8)
- **Phase8Authoring**: Container + layout
- **AuthoringCanvas**: DAG node layout with drag positioning (UI-only)
- **TaskPropertiesPanel**: Edit metadata, risk, retries, confidence
- **SimulationTimeline**: Dry-run simulation playback
- **WorkflowSnapshotPanel**: Versioned snapshots + import/export

## Logic Components
- **SafeWorkflowExecutor**: Deterministic dry-run simulation (no tool calls)
- **ValidationEngine**: Detect circular deps, invalid branches, missing nodes
- **ConfidenceOverlay**: Visual confidence + risk annotations

## Data Contracts

### Workflow Model (UI-only)
```
{
  id: string,
  name: string,
  version: string,
  nodes: [
    {
      id: string,
      title: string,
      tool: string,
      priority: 'CRITICAL'|'HIGH'|'MEDIUM'|'LOW'|'BACKGROUND',
      risk: 'LOW'|'MEDIUM'|'HIGH',
      retries: number,
      confidence: number,
      dependencies: string[],
      branches: [{ condition: 'on_success'|'on_failure', nextTaskId: string }],
      position: { x, y }
    }
  ]
}
```

### Snapshot Store
- File: [frontend/public/workflow_snapshots.json](frontend/public/workflow_snapshots.json)
- Local copies in browser localStorage

## Safety Principles
- Simulation uses pure in-memory logic
- No calls to Phase 5 tools or Phase 6 scheduler
- High-risk tasks flagged with warnings
- UI explicitly labeled as dry-run only

## Phase 9–12 Hooks
- Authoring canvas can be extended with AI-suggestions
- DAG serialization enables collaboration
- ValidationEngine supports policy checks
- Snapshot system supports branching versions

## Integration Notes
- Phase 8 embeds Phase 7 read-only panels for continuity
- Authoring tab added to App with no impact on chat or observatory
