#!/usr/bin/env python3
"""
Test read-only codebase awareness tools.
"""

import sys
sys.path.insert(0, '.')

from Back_End.codebase_analyzer import CodebaseAnalyzer


def test_repo_index():
    print("\n=== Testing Repo Index ===\n")
    analyzer = CodebaseAnalyzer(root_path='.')
    result = analyzer.get_repo_index()
    assert result["type"] == "repo_index"
    assert "backend" in result["structure"]
    assert "python" in result["languages"]
    print("✓ Repo index passed")


def test_file_summary():
    print("\n=== Testing File Summary ===\n")
    analyzer = CodebaseAnalyzer(root_path='.')
    summary = analyzer.get_file_summary("backend/agent.py")
    assert summary["type"] == "file_summary"
    assert "Agent" in summary.get("classes", [])
    print("✓ File summary passed")


def test_dependency_map():
    print("\n=== Testing Dependency Map ===\n")
    analyzer = CodebaseAnalyzer(root_path='.')
    dep_map = analyzer.get_dependency_map()
    assert dep_map["type"] == "dependency_map"
    assert "backend/agent.py" in dep_map["analysis"]
    print("✓ Dependency map passed")


if __name__ == '__main__':
    print("=" * 60)
    print("CODE AWARENESS TEST SUITE")
    print("=" * 60)

    test_repo_index()
    test_file_summary()
    test_dependency_map()

    print("\n" + "=" * 60)
    print("✓ All code awareness tests completed!")
    print("=" * 60)

