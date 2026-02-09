#!/usr/bin/env python3
"""
Buddy Traffic Metrics Visualizer
==================================

Reads JSON traffic metrics and generates visualizations and analysis.
Provides real-time plotting of key metrics over time.

Status: PRODUCTION READY
Safe: YES (read-only to all files)
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple, Any
import statistics

def load_metrics(filepath: str = 'buddy_traffic_metrics.json') -> Dict[str, Any]:
    """Load metrics from JSON file."""
    if not os.path.exists(filepath):
        print(f"❌ ERROR: Metrics file not found: {filepath}")
        print("Run buddy_continuous_traffic_simulator.py first to generate metrics.")
        return None
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ ERROR loading metrics: {e}")
        return None

def print_summary(data: Dict[str, Any]) -> None:
    """Print summary statistics."""
    if not data or 'reports' not in data or not data['reports']:
        print("No reports available")
        return
    
    reports = data['reports']
    latest = reports[-1]
    
    print("\n" + "="*80)
    print("BUDDY TRAFFIC SUMMARY")
    print("="*80)
    print(f"\nLatest Report: {latest['timestamp']}")
    print(f"Total Requests: {latest['total_requests']}")
    print(f"Success Rate: {latest['success_rate']:.1f}%")
    print(f"\nPerformance Metrics:")
    print(f"  Average Execution: {latest['execution_time']['average']:.2f}ms")
    print(f"  Min/Max: {latest['execution_time']['min']:.2f}ms / {latest['execution_time']['max']:.2f}ms")
    print(f"  P95/P99: {latest['execution_time']['p95']:.2f}ms / {latest['execution_time']['p99']:.2f}ms")
    print(f"\nConfidence Distribution:")
    print(f"  Mean: {latest['confidence']['mean']:.3f}")
    print(f"  Std Dev: {latest['confidence']['std_dev']:.3f}")
    print(f"  Range: {latest['confidence']['min']:.3f} - {latest['confidence']['max']:.3f}")
    print(f"\nPre-validation: {latest['pre_validation']['pass_rate']:.1f}% pass rate")
    print(f"Approval Routing: {latest['approval_path']['approval_rate']:.1f}% approved")
    print(f"Adversarial Blocking: {latest['adversarial']['block_rate']:.1f}%")
    print(f"Error Rate: {latest['error_rate']:.2f}%")
    print(f"Load Level: {latest['load_level']}")
    print("="*80 + "\n")

def print_trends(data: Dict[str, Any]) -> None:
    """Print trends across reports."""
    if not data or 'reports' not in data or len(data['reports']) < 2:
        print("Not enough reports for trend analysis")
        return
    
    reports = data['reports']
    
    # Calculate trends
    success_rates = [r['success_rate'] for r in reports]
    avg_exec_times = [r['execution_time']['average'] for r in reports]
    std_devs = [r['confidence']['std_dev'] for r in reports]
    error_rates = [r['error_rate'] for r in reports]
    
    print("\n" + "="*80)
    print("TREND ANALYSIS")
    print("="*80)
    
    print(f"\nSuccess Rate: {success_rates[0]:.1f}% → {success_rates[-1]:.1f}%")
    if success_rates[-1] > success_rates[0]:
        print(f"  ✓ Improved by {success_rates[-1] - success_rates[0]:.1f}%")
    elif success_rates[-1] < success_rates[0]:
        print(f"  ✗ Degraded by {success_rates[0] - success_rates[-1]:.1f}%")
    else:
        print(f"  → Stable")
    
    print(f"\nAverage Execution Time: {avg_exec_times[0]:.2f}ms → {avg_exec_times[-1]:.2f}ms")
    if avg_exec_times[-1] < avg_exec_times[0]:
        print(f"  ✓ Improved by {avg_exec_times[0] - avg_exec_times[-1]:.2f}ms")
    elif avg_exec_times[-1] > avg_exec_times[0]:
        print(f"  ✗ Degraded by {avg_exec_times[-1] - avg_exec_times[0]:.2f}ms")
    else:
        print(f"  → Stable")
    
    print(f"\nConfidence Distribution Std Dev: {std_devs[0]:.3f} → {std_devs[-1]:.3f}")
    if std_devs[-1] >= std_devs[0]:
        print(f"  ✓ Healthy distribution variation")
    else:
        print(f"  ⚠ Reduced variation")
    
    print(f"\nError Rate: {error_rates[0]:.2f}% → {error_rates[-1]:.2f}%")
    if error_rates[-1] < error_rates[0]:
        print(f"  ✓ Improved by {error_rates[0] - error_rates[-1]:.2f}%")
    elif error_rates[-1] > error_rates[0]:
        print(f"  ✗ Degraded by {error_rates[-1] - error_rates[0]:.2f}%")
    else:
        print(f"  → Stable")
    
    print("="*80 + "\n")

def print_category_analysis(data: Dict[str, Any]) -> None:
    """Analyze results by input category."""
    if not data or 'requests' not in data or not data['requests']:
        print("No request data available")
        return
    
    requests = data['requests']
    categories = {}
    
    for req in requests:
        category = req['request']['category']
        if category not in categories:
            categories[category] = {
                'count': 0,
                'success': 0,
                'execution_times': [],
                'confidence_values': [],
                'errors': 0,
            }
        
        categories[category]['count'] += 1
        if req['success']:
            categories[category]['success'] += 1
        categories[category]['execution_times'].append(req['execution_time'])
        if req['confidence'] is not None:
            categories[category]['confidence_values'].append(req['confidence'])
        if req['error']:
            categories[category]['errors'] += 1
    
    print("\n" + "="*80)
    print("ANALYSIS BY INPUT CATEGORY")
    print("="*80)
    
    for category in sorted(categories.keys()):
        stats = categories[category]
        success_rate = (stats['success'] / stats['count'] * 100) if stats['count'] > 0 else 0
        avg_exec = statistics.mean(stats['execution_times']) if stats['execution_times'] else 0
        avg_conf = statistics.mean(stats['confidence_values']) if stats['confidence_values'] else 0
        
        print(f"\n{category.upper()}")
        print(f"  Count: {stats['count']} | Success: {success_rate:.1f}%")
        print(f"  Avg Execution: {avg_exec:.2f}ms | Avg Confidence: {avg_conf:.3f}")
        print(f"  Errors: {stats['errors']}")

def print_error_analysis(data: Dict[str, Any]) -> None:
    """Analyze errors."""
    if not data or 'reports' not in data or not data['reports']:
        print("No error data available")
        return
    
    all_errors = []
    for report in data['reports']:
        # Errors are in aggregate_metrics (from raw data if available)
        pass
    
    # Alternative: extract from requests
    if data.get('requests'):
        errors = [r for r in data['requests'] if r['error']]
        if not errors:
            print("\n✓ No errors detected in recent requests")
            return
        
        print("\n" + "="*80)
        print("ERROR ANALYSIS")
        print("="*80)
        print(f"\nTotal Errors: {len(errors)}")
        
        error_types = {}
        for error_req in errors:
            error_msg = error_req.get('error', 'unknown')[:50]  # First 50 chars
            if error_msg not in error_types:
                error_types[error_msg] = 0
            error_types[error_msg] += 1
        
        for error_msg, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {count}x: {error_msg}")
        
        print("="*80 + "\n")

def simple_ascii_chart(values: List[float], label: str, width: int = 60, height: int = 10) -> None:
    """Print simple ASCII chart."""
    if not values:
        print(f"{label}: No data")
        return
    
    min_val = min(values)
    max_val = max(values)
    range_val = max_val - min_val if max_val > min_val else 1
    
    print(f"\n{label}:")
    
    # Create histogram
    bucket_size = len(values) // width if len(values) > width else 1
    if bucket_size < 1:
        bucket_size = 1
    
    buckets = []
    for i in range(0, len(values), bucket_size):
        bucket = values[i:i+bucket_size]
        avg = sum(bucket) / len(bucket)
        buckets.append(avg)
    
    # Normalize to 0-height
    max_bucket = max(buckets) if buckets else 1
    min_bucket = min(buckets) if buckets else 0
    bucket_range = max_bucket - min_bucket if max_bucket > min_bucket else 1
    
    # Print bars
    for row in range(height, 0, -1):
        threshold = min_bucket + (bucket_range * row / height)
        line = ""
        for bucket in buckets:
            if bucket >= threshold:
                line += "█"
            else:
                line += " "
        print(f"  {line}")
    
    print(f"  Min: {min_val:.2f} | Max: {max_val:.2f} | Avg: {sum(values)/len(values):.2f}")

def main():
    """Main visualization function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Buddy Traffic Metrics Visualizer')
    parser.add_argument('--file', default='buddy_traffic_metrics.json',
                       help='Metrics JSON file (default: buddy_traffic_metrics.json)')
    parser.add_argument('--summary', action='store_true', help='Print summary only')
    parser.add_argument('--trends', action='store_true', help='Print trends only')
    parser.add_argument('--categories', action='store_true', help='Print category analysis')
    parser.add_argument('--errors', action='store_true', help='Print error analysis')
    parser.add_argument('--all', action='store_true', help='Print all analyses')
    
    args = parser.parse_args()
    
    # Load metrics
    data = load_metrics(args.file)
    if not data:
        sys.exit(1)
    
    # Print requested sections
    if args.all:
        print_summary(data)
        print_trends(data)
        print_category_analysis(data)
        print_error_analysis(data)
    else:
        if args.summary or not (args.trends or args.categories or args.errors):
            print_summary(data)
        if args.trends:
            print_trends(data)
        if args.categories:
            print_category_analysis(data)
        if args.errors:
            print_error_analysis(data)

if __name__ == '__main__':
    main()
