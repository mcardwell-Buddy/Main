"""
Run all phase tests and show summary
"""
import subprocess
import sys

tests = ['test_phase1.py', 'test_phase2.py', 'test_phase3.py']
results = {}

for test in tests:
    print(f"\n{'='*70}")
    print(f"Running {test}...")
    print('='*70)
    
    result = subprocess.run(
        [sys.executable, test],
        capture_output=False,
        text=True
    )
    
    results[test] = result.returncode

print(f"\n{'='*70}")
print("SUMMARY")
print('='*70)

all_passed = True
for test, code in results.items():
    status = "✅ PASSED" if code == 0 else "❌ FAILED"
    print(f"{test:20} {status} (exit code: {code})")
    if code != 0:
        all_passed = False

print('='*70)
if all_passed:
    print("🎉 ALL TESTS PASSED!")
else:
    print("⚠️ Some tests failed")

sys.exit(0 if all_passed else 1)
