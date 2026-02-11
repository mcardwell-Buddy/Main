#!/usr/bin/env python
"""Quick test to verify Phase 7 analytics engine works."""

import sys
import tempfile
import shutil
from pathlib import Path

# Test imports
try:
    from analytics_engine import (
        AnalyticsEngine, ExecutionMetrics, ConfidenceLevel,
        MetricsCollector, StorageManager, ToolRegistry
    )
    print("✅ All Phase 7 modules imported successfully!")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test basic functionality
try:
    temp_dir = tempfile.mkdtemp()
    
    # Create engine
    engine = AnalyticsEngine()
    engine.metrics_collector.db_path = str(Path(temp_dir) / "test.db")
    engine.storage_manager.db_path = str(Path(temp_dir) / "test.db")
    print("✅ AnalyticsEngine initialized!")
    
    # Record some executions
    for i in range(5):
        engine.record_execution(
            task_id=f"task_{i}",
            agent_id=f"agent_{i % 2}",
            tool_name=["web_search", "api_call", "browser"][i % 3],
            duration_seconds=2.0 + i,
            success=i % 3 != 0
        )
    print("✅ Recorded 5 executions!")
    
    # Test all 6 API endpoints
    apis = [
        ("get_agents_status", engine.get_agents_status()),
        ("get_predictive_capacity", engine.get_predictive_capacity()),
        ("get_task_pipeline", engine.get_task_pipeline()),
        ("get_api_usage_and_costing", engine.get_api_usage_and_costing()),
        ("get_system_learning", engine.get_system_learning()),
        ("get_risk_patterns", engine.get_risk_patterns()),
    ]
    
    for name, result in apis:
        assert isinstance(result, dict), f"{name} should return dict"
        assert "timestamp" in result, f"{name} missing timestamp"
        print(f"✅ API endpoint {name}() works!")
    
    print(f"\n✅ All {len(apis)} API endpoints working!")
    
    # Cleanup
    shutil.rmtree(temp_dir)
    print("✅ Cleanup complete!")
    
    print("\n" + "="*50)
    print("🚀 PHASE 7: ADVANCED ANALYTICS READY!")
    print("="*50)
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
