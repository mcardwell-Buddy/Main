"""
Firebase Usage Analysis - Phase 0
Analyzes current Firebase usage to establish baseline.

Usage:
    python scripts/analyze_firebase_usage.py

This will:
1. Count documents in each collection
2. Estimate storage size
3. Estimate read/write patterns
4. Project monthly costs
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add Back_End to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Back_End'))

class FirebaseAnalyzer:
    def __init__(self):
        # Initialize Firebase if not already initialized
        if not firebase_admin._apps:
            # Try to find service account key
            service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT')
            if service_account_path and os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
            else:
                print("⚠️  No service account found. Using application default credentials.")
                cred = credentials.ApplicationDefault()
            
            firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()
        self.results = {}
    
    def count_collection(self, collection_name):
        """Count documents in a collection and estimate size."""
        try:
            collection_ref = self.db.collection(collection_name)
            docs = list(collection_ref.stream())
            count = len(docs)
            
            # Estimate size (rough)
            total_size = 0
            for doc in docs[:10]:  # Sample first 10
                doc_dict = doc.to_dict()
                # Rough size estimate (JSON bytes)
                import json
                doc_size = len(json.dumps(doc_dict, default=str).encode('utf-8'))
                total_size += doc_size
            
            avg_size = total_size / min(count, 10) if count > 0 else 0
            estimated_total_size = avg_size * count
            
            return {
                'count': count,
                'avg_size_kb': avg_size / 1024,
                'total_size_mb': estimated_total_size / (1024 * 1024)
            }
        except Exception as e:
            print(f"❌ Error analyzing {collection_name}: {e}")
            return {'count': 0, 'avg_size_kb': 0, 'total_size_mb': 0}
    
    def analyze_all_collections(self):
        """Analyze all main collections."""
        print("=" * 70)
        print("📊 FIREBASE USAGE ANALYSIS")
        print("=" * 70)
        print(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Main collections to analyze
        collections = [
            'missions',
            'sessions',
            'conversations',
            'users',
            'learning_signals',
            'selector_rankings',
            'configuration',
            'tool_registry'
        ]
        
        print("📁 Collection Analysis:")
        print("-" * 70)
        
        total_docs = 0
        total_size_mb = 0
        
        for collection_name in collections:
            print(f"\n🔍 Analyzing: {collection_name}")
            stats = self.count_collection(collection_name)
            self.results[collection_name] = stats
            
            total_docs += stats['count']
            total_size_mb += stats['total_size_mb']
            
            print(f"   Documents: {stats['count']}")
            print(f"   Avg Size: {stats['avg_size_kb']:.2f} KB")
            print(f"   Total Size: {stats['total_size_mb']:.2f} MB")
        
        print("\n" + "=" * 70)
        print("📋 SUMMARY")
        print("=" * 70)
        print(f"\nTotal Documents: {total_docs}")
        print(f"Total Storage: {total_size_mb:.2f} MB ({total_size_mb / 1024:.3f} GB)")
        
        # Estimate operations (rough)
        print(f"\n📈 Estimated Monthly Operations (based on typical usage):")
        estimated_reads_per_day = total_docs * 2  # Average 2 reads per doc per day
        estimated_writes_per_day = total_docs * 0.1  # Average 0.1 writes per doc per day
        
        estimated_reads_per_month = estimated_reads_per_day * 30
        estimated_writes_per_month = estimated_writes_per_day * 30
        
        print(f"   Reads/day: ~{estimated_reads_per_day:,.0f}")
        print(f"   Writes/day: ~{estimated_writes_per_day:,.0f}")
        print(f"   Reads/month: ~{estimated_reads_per_month:,.0f}")
        print(f"   Writes/month: ~{estimated_writes_per_month:,.0f}")
        
        # Cost estimate (Firebase free tier)
        print(f"\n💰 Firebase Firestore Pricing:")
        print(f"   Free Tier:")
        print(f"      - Reads: 50,000/day")
        print(f"      - Writes: 20,000/day")
        print(f"      - Deletes: 20,000/day")
        print(f"      - Storage: 1 GB")
        
        # Check if within free tier
        print(f"\n✅ Current Usage vs Free Tier:")
        reads_percent = (estimated_reads_per_day / 50000) * 100
        writes_percent = (estimated_writes_per_day / 20000) * 100
        storage_percent = ((total_size_mb / 1024) / 1) * 100
        
        print(f"   Reads: {reads_percent:.1f}% of free tier")
        print(f"   Writes: {writes_percent:.1f}% of free tier")
        print(f"   Storage: {storage_percent:.1f}% of free tier")
        
        if reads_percent < 100 and writes_percent < 100 and storage_percent < 100:
            print(f"\n✅ Within free tier! Estimated cost: $0/month")
        else:
            # Calculate overage costs
            excess_reads = max(0, estimated_reads_per_month - (50000 * 30))
            excess_writes = max(0, estimated_writes_per_month - (20000 * 30))
            excess_storage_gb = max(0, (total_size_mb / 1024) - 1)
            
            cost_reads = (excess_reads / 100000) * 0.06  # $0.06 per 100k reads
            cost_writes = (excess_writes / 100000) * 0.18  # $0.18 per 100k writes
            cost_storage = excess_storage_gb * 0.18  # $0.18 per GB/month
            
            total_cost = cost_reads + cost_writes + cost_storage
            
            print(f"\n⚠️  Exceeds free tier. Estimated cost: ${total_cost:.2f}/month")
            print(f"      - Reads: ${cost_reads:.2f}")
            print(f"      - Writes: ${cost_writes:.2f}")
            print(f"      - Storage: ${cost_storage:.2f}")
        
        # Save report
        self.save_report(total_docs, total_size_mb, estimated_reads_per_month, estimated_writes_per_month)
    
    def save_report(self, total_docs, total_size_mb, reads_per_month, writes_per_month):
        """Save analysis report to file."""
        report_path = os.path.join(os.path.dirname(__file__), '..', 'PHASE0_FIREBASE_USAGE_REPORT.txt')
        
        with open(report_path, 'w') as f:
            f.write("FIREBASE USAGE ANALYSIS REPORT\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("Collection Summary:\n")
            f.write("-" * 70 + "\n")
            for collection_name, stats in self.results.items():
                f.write(f"\n{collection_name}:\n")
                f.write(f"  Documents: {stats['count']}\n")
                f.write(f"  Avg Size: {stats['avg_size_kb']:.2f} KB\n")
                f.write(f"  Total Size: {stats['total_size_mb']:.2f} MB\n")
            
            f.write(f"\nTotal Documents: {total_docs}\n")
            f.write(f"Total Storage: {total_size_mb:.2f} MB\n\n")
            
            f.write(f"Estimated Operations:\n")
            f.write(f"  Reads/month: ~{reads_per_month:,.0f}\n")
            f.write(f"  Writes/month: ~{writes_per_month:,.0f}\n\n")
            
            f.write("Firebase Schema (for reference):\n")
            f.write("-" * 70 + "\n")
            for collection_name in self.results.keys():
                f.write(f"/{collection_name}\n")
        
        print(f"\n📄 Report saved to: {os.path.basename(report_path)}")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    print("\n🔥 Firebase Usage Analyzer")
    print("   This will analyze your current Firebase Firestore usage.\n")
    
    analyzer = FirebaseAnalyzer()
    analyzer.analyze_all_collections()
