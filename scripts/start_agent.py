#!/usr/bin/env python3
"""
Start Buddy Local Agent
Windows batch script wrapper
"""

import subprocess
import sys
import os

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
agent_script = os.path.join(script_dir, 'Back_End', 'buddy_local_agent.py')

# Activate venv and start agent
if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Starting Buddy Local Agent")
    print("=" * 70)
    print()
    
    # Run agent with arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else ['--start']
    
    try:
        result = subprocess.run(
            [sys.executable, agent_script] + args,
            cwd=project_dir
        )
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n\nShutdown signal received")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
