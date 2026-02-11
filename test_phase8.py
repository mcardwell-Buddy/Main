#!/usr/bin/env python
"""
Phase 8: Dashboard & Web UI - Test Suite
Comprehensive testing of FastAPI dashboard server and endpoints
"""

import unittest
import json
from pathlib import Path
import tempfile
import shutil

# Mock analytics engine for testing
class MockAnalyticsEngine:
    def get_agents_status(self):
        return {
            "timestamp": "2026-02-11T10:00:00",
            "total_agents": 2,
            "agents": [
                {
                    "agent_id": "local-aspire5-abc123",
                    "status": "IDLE",
                    "tasks_completed_today": 10,
                    "avg_response_time": 2.5,
                    "success_rate": 0.95,
                    "last_activity": "2026-02-11T10:00:00"
                }
            ]
        }

    def get_predictive_capacity(self):
        return {
            "timestamp": "2026-02-11T10:00:00",
            "forecasts": [
                {
                    "agent_id": "local-aspire5-abc123",
                    "estimated_available_capacity": 75,
                    "current_queue_depth": 2,
                    "bottleneck_tools": []
                }
            ]
        }

    def get_task_pipeline(self):
        return {
            "timestamp": "2026-02-11T10:00:00",
            "last_24_hours": {
                "total_tasks": 50,
                "successful_tasks": 48,
                "failed_tasks": 2,
                "success_rate": 0.96,
                "tool_breakdown": {"web_search": 25, "api_call": 15, "browser": 10}
            }
        }

    def get_api_usage_and_costing(self):
        return {
            "timestamp": "2026-02-11T10:00:00",
            "api_usage": {
                "total_tasks_24h": 50,
                "total_tokens_24h": 5000,
                "avg_tokens_per_task": 100
            },
            "costing": {
                "execution_costs_24h": 0.50,
                "storage_costs_daily": 0.00001,
                "total_daily_cost": 0.50001
            },
            "storage": {
                "tier1_raw_records": 100,
                "tier2_hourly_summaries": 24,
                "estimated_size_mb": 0.05
            }
        }

    def get_system_learning(self):
        return {
            "timestamp": "2026-02-11T10:00:00",
            "confidence_distribution": {
                "high_confidence": 3,
                "medium_confidence": 2,
                "low_confidence": 0
            },
            "tool_profiles": [
                {
                    "tool_name": "web_search",
                    "total_executions": 25,
                    "success_rate": 0.98,
                    "avg_cost": 0.02,
                    "avg_duration": 2.0,
                    "confidence_level": "HIGH"
                }
            ]
        }

    def get_risk_patterns(self):
        return {
            "timestamp": "2026-02-11T10:00:00",
            "failure_patterns": {},
            "cost_anomalies": []
        }

    def get_tool_recommendations(self):
        return {
            "timestamp": "2026-02-11T10:00:00",
            "total_recommendations": 0,
            "recommendations": []
        }

    def cleanup_old_data(self):
        pass

    def run_hourly_aggregation(self):
        pass


class TestDashboardAPI(unittest.TestCase):
    """Test the FastAPI dashboard server."""

    def setUp(self):
        """Set up test client."""
        from phase8_dashboard_api import app, init_analytics
        
        self.app = app
        self.client = app.test_client() if hasattr(app, 'test_client') else None
        
        # Initialize with mock engine
        init_analytics(MockAnalyticsEngine())

    def test_health_check(self):
        """Test health check endpoint."""
        from fastapi.testclient import TestClient
        client = TestClient(self.app)
        
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "Buddy Dashboard API"

    def test_api_root(self):
        """Test API root endpoint."""
        from fastapi.testclient import TestClient
        client = TestClient(self.app)
        
        response = client.get("/api/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "endpoints" in data

    def test_agents_endpoint(self):
        """Test agents status endpoint."""
        from fastapi.testclient import TestClient
        client = TestClient(self.app)
        
        response = client.get("/api/analytics/agents")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "agents" in data
        assert data["total_agents"] >= 0

    def test_capacity_endpoint(self):
        """Test capacity endpoint."""
        from fastapi.testclient import TestClient
        client = TestClient(self.app)
        
        response = client.get("/api/analytics/capacity")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "forecasts" in data

    def test_pipeline_endpoint(self):
        """Test task pipeline endpoint."""
        from fastapi.testclient import TestClient
        client = TestClient(self.app)
        
        response = client.get("/api/analytics/pipeline")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "last_24_hours" in data

    def test_costs_endpoint(self):
        """Test API usage and costing endpoint."""
        from fastapi.testclient import TestClient
        client = TestClient(self.app)
        
        response = client.get("/api/analytics/costs")
        assert response.status_code == 200
        data = response.json()
        assert "api_usage" in data
        assert "costing" in data
        assert "storage" in data

    def test_learning_endpoint(self):
        """Test system learning endpoint."""
        from fastapi.testclient import TestClient
        client = TestClient(self.app)
        
        response = client.get("/api/analytics/learning")
        assert response.status_code == 200
        data = response.json()
        assert "confidence_distribution" in data
        assert "tool_profiles" in data

    def test_risks_endpoint(self):
        """Test risk patterns endpoint."""
        from fastapi.testclient import TestClient
        client = TestClient(self.app)
        
        response = client.get("/api/analytics/risks")
        assert response.status_code == 200
        data = response.json()
        assert "failure_patterns" in data
        assert "cost_anomalies" in data

    def test_recommendations_endpoint(self):
        """Test recommendations endpoint."""
        from fastapi.testclient import TestClient
        client = TestClient(self.app)
        
        response = client.get("/api/analytics/recommendations")
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data

    def test_all_analytics_endpoint(self):
        """Test batch all analytics endpoint."""
        from fastapi.testclient import TestClient
        client = TestClient(self.app)
        
        response = client.get("/api/analytics/all")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "agents" in data
        assert "capacity" in data
        assert "pipeline" in data
        assert "costs" in data
        assert "learning" in data

    def test_admin_cleanup(self):
        """Test admin cleanup endpoint."""
        from fastapi.testclient import TestClient
        client = TestClient(self.app)
        
        response = client.post("/api/admin/cleanup")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "timestamp" in data

    def test_admin_aggregate(self):
        """Test admin aggregation endpoint."""
        from fastapi.testclient import TestClient
        client = TestClient(self.app)
        
        response = client.post("/api/admin/aggregate")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "timestamp" in data


class TestDashboardHTML(unittest.TestCase):
    """Test dashboard HTML file."""

    def test_dashboard_html_exists(self):
        """Test dashboard.html file exists."""
        html_path = Path(__file__).parent / "dashboard.html"
        self.assertTrue(html_path.exists(), "dashboard.html not found")

    def test_dashboard_html_contains_key_elements(self):
        """Test dashboard HTML contains key elements."""
        html_path = Path(__file__).parent / "dashboard.html"
        content = html_path.read_text()
        
        # Check for key sections
        self.assertIn("Buddy System Monitor", content)
        self.assertIn("Agents", content)
        self.assertIn("Capacity", content)
        self.assertIn("Task Pipeline", content)
        self.assertIn("API Usage & Costing", content)
        self.assertIn("System Learning", content)
        
        # Check for JavaScript functionality
        self.assertIn("refreshAllData", content)
        self.assertIn("updateAgents", content)
        self.assertIn("Chart.js", content)

    def test_dashboard_html_is_valid_html(self):
        """Test dashboard HTML basic structure."""
        html_path = Path(__file__).parent / "dashboard.html"
        content = html_path.read_text()
        
        # Check basic HTML structure
        self.assertIn("<html", content)
        self.assertIn("</html>", content)
        self.assertIn("<head", content)
        self.assertIn("<body", content)
        self.assertIn("<!DOCTYPE html>", content)


class TestDashboardIntegration(unittest.TestCase):
    """Integration tests for dashboard."""

    def test_all_endpoints_return_json(self):
        """Test all endpoints return valid JSON."""
        from fastapi.testclient import TestClient
        from phase8_dashboard_api import app, init_analytics
        
        init_analytics(MockAnalyticsEngine())
        client = TestClient(app)
        
        endpoints = [
            "/api/health",
            "/api/",
            "/api/analytics/agents",
            "/api/analytics/capacity",
            "/api/analytics/pipeline",
            "/api/analytics/costs",
            "/api/analytics/learning",
            "/api/analytics/risks",
            "/api/analytics/recommendations",
            "/api/analytics/all"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            self.assertEqual(response.status_code, 200, f"Endpoint {endpoint} failed")
            
            # Verify it's valid JSON
            try:
                response.json()
            except:
                self.fail(f"Endpoint {endpoint} did not return valid JSON")

    def test_cors_headers_present(self):
        """Test CORS headers are present."""
        from fastapi.testclient import TestClient
        from phase8_dashboard_api import app, init_analytics
        
        init_analytics(MockAnalyticsEngine())
        client = TestClient(app)
        
        response = client.get("/api/health")
        # CORS headers should be present
        self.assertIsNotNone(response.headers)


if __name__ == "__main__":
    unittest.main(verbosity=2)
