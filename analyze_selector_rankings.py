#!/usr/bin/env python
"""
Phase 1 Step 4: Selector Ranking Analysis

Read-only analysis of selector-level learning signals.
Computes ranked selector preference table based on evidence.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict


def load_selector_signals(signal_file: Path) -> List[Dict[str, Any]]:
    """Load selector signals from learning_signals.jsonl"""
    signals = []
    
    if not signal_file.exists():
        print(f"⚠️  Signal file not found: {signal_file}")
        return signals
    
    with open(signal_file, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            
            try:
                signal = json.loads(line)
                
                # Filter for selector-level signals only
                if (signal.get('signal_layer') == 'selector' and 
                    signal.get('signal_source') == 'web_navigator'):
                    signals.append(signal)
            except json.JSONDecodeError as e:
                print(f"⚠️  Failed to parse line: {e}")
    
    return signals


def compute_selector_metrics(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute metrics for each unique selector"""
    
    # Group by selector + selector_type
    selector_groups = defaultdict(lambda: {
        'selector': None,
        'selector_type': None,
        'attempts': 0,
        'successes': 0,
        'failures': 0,
        'total_duration_ms': 0,
        'total_retry_count': 0
    })
    
    for signal in signals:
        selector = signal.get('selector', 'unknown')
        selector_type = signal.get('selector_type', 'unknown')
        key = (selector, selector_type)
        
        group = selector_groups[key]
        group['selector'] = selector
        group['selector_type'] = selector_type
        group['attempts'] += 1
        
        outcome = signal.get('outcome', 'unknown')
        if outcome == 'success':
            group['successes'] += 1
        elif outcome == 'failure':
            group['failures'] += 1
        
        duration = signal.get('duration_ms', 0)
        group['total_duration_ms'] += duration
        
        retry_count = signal.get('retry_count', 0)
        group['total_retry_count'] += retry_count
    
    # Compute final metrics
    results = []
    for group in selector_groups.values():
        attempts = group['attempts']
        successes = group['successes']
        failures = group['failures']
        
        success_rate = successes / attempts if attempts > 0 else 0.0
        avg_duration_ms = group['total_duration_ms'] / attempts if attempts > 0 else 0
        avg_retry_count = group['total_retry_count'] / attempts if attempts > 0 else 0
        
        results.append({
            'selector': group['selector'],
            'selector_type': group['selector_type'],
            'attempts': attempts,
            'successes': successes,
            'failures': failures,
            'success_rate': round(success_rate, 4),
            'avg_duration_ms': round(avg_duration_ms, 2),
            'avg_retry_count': round(avg_retry_count, 2)
        })
    
    return results


def rank_selectors(metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rank selectors by success_rate (desc), avg_retry_count (asc), avg_duration_ms (asc)"""
    
    # Sort by: success_rate desc, then avg_retry_count asc, then avg_duration_ms asc
    sorted_metrics = sorted(
        metrics,
        key=lambda x: (-x['success_rate'], x['avg_retry_count'], x['avg_duration_ms'])
    )
    
    # Assign ranks
    for rank, metric in enumerate(sorted_metrics, start=1):
        metric['rank'] = rank
    
    return sorted_metrics


def write_rankings(rankings: List[Dict[str, Any]], output_file: Path) -> None:
    """Write rankings to JSON file"""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(rankings, f, indent=2)
    
    print(f"✓ Rankings written to: {output_file}")


def print_summary(rankings: List[Dict[str, Any]]) -> None:
    """Print analysis summary"""
    print("\n" + "=" * 70)
    print("SELECTOR RANKING ANALYSIS SUMMARY")
    print("=" * 70)
    
    if not rankings:
        print("\n⚠️  No selector signals found")
        return
    
    print(f"\nTotal unique selectors analyzed: {len(rankings)}")
    
    # Top 3 selectors
    print("\n📊 TOP 3 SELECTORS:")
    for rank_entry in rankings[:3]:
        rank = rank_entry['rank']
        selector = rank_entry['selector']
        selector_type = rank_entry['selector_type']
        success_rate = rank_entry['success_rate']
        avg_duration = rank_entry['avg_duration_ms']
        avg_retries = rank_entry['avg_retry_count']
        attempts = rank_entry['attempts']
        
        print(f"\n  #{rank}: {selector_type}:{selector}")
        print(f"      Success Rate: {success_rate:.1%} ({attempts} attempts)")
        print(f"      Avg Duration: {avg_duration:.1f}ms")
        print(f"      Avg Retries: {avg_retries:.2f}")
    
    # Selectors with <70% success
    low_success = [r for r in rankings if r['success_rate'] < 0.70]
    
    if low_success:
        print(f"\n⚠️  SELECTORS WITH <70% SUCCESS RATE: {len(low_success)}")
        for rank_entry in low_success:
            selector = rank_entry['selector']
            selector_type = rank_entry['selector_type']
            success_rate = rank_entry['success_rate']
            attempts = rank_entry['attempts']
            
            print(f"    - {selector_type}:{selector} → {success_rate:.1%} ({attempts} attempts)")
    else:
        print("\n✅ All selectors have ≥70% success rate")
    
    print("\n" + "=" * 70)


def main():
    print("=" * 70)
    print("PHASE 1 STEP 4: SELECTOR RANKING ANALYSIS")
    print("=" * 70)
    
    # Paths
    signal_file = Path("outputs/phase25/learning_signals.jsonl")
    output_file = Path("outputs/phase25/selector_rankings.json")
    
    print(f"\n📂 Reading signals from: {signal_file}")
    
    # Load selector signals
    signals = load_selector_signals(signal_file)
    print(f"   Found {len(signals)} selector-level signals")
    
    if not signals:
        print("\n⚠️  No selector signals found. Run phase1_validation_run_v2.py first.")
        return
    
    # Compute metrics
    print("\n📊 Computing selector metrics...")
    metrics = compute_selector_metrics(signals)
    print(f"   Analyzed {len(metrics)} unique selectors")
    
    # Rank selectors
    print("\n🏆 Ranking selectors...")
    rankings = rank_selectors(metrics)
    
    # Write output
    print(f"\n💾 Writing rankings to: {output_file}")
    write_rankings(rankings, output_file)
    
    # Print summary
    print_summary(rankings)
    
    print("\n✅ Phase 1 Step 4 Complete")


if __name__ == "__main__":
    main()
