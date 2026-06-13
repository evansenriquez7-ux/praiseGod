#!/usr/bin/env python3
"""
Helper script to process pending Claude extraction tasks in batch.
Reads tasks from /tmp/ccmed_claude_tasks/, processes them, and writes responses.
"""

import json
import os
from pathlib import Path

def main():
    task_dir = Path("/tmp/ccmed_claude_tasks")
    response_dir = Path("/tmp/ccmed_claude_responses")
    
    if not task_dir.exists():
        print("No tasks directory found")
        return
    
    # List pending tasks
    tasks = sorted([f for f in task_dir.glob("*.json")])
    
    if not tasks:
        print("No pending tasks")
        return
    
    print(f"\n{'='*60}")
    print(f"Found {len(tasks)} pending extraction task(s)")
    print(f"{'='*60}\n")
    
    for task_file in tasks:
        with open(task_file, 'r') as f:
            task = json.load(f)
        
        task_id = task.get("task_id")
        task_type = task.get("task_type", "extraction")
        print(f"\n[TASK {task_id}] {task_type.upper()}")
        print(f"Prompt preview: {task.get('prompt', '')[:150]}...")
        print(f"\nPaste the JSON response below and press Enter twice when done:")
        print(f"{'-'*60}")
        
        response_lines = []
        empty_count = 0
        while True:
            line = input()
            if line == "":
                empty_count += 1
                if empty_count >= 2:
                    break
            else:
                empty_count = 0
                response_lines.append(line)
        
        response_text = "\n".join(response_lines).strip()
        
        if response_text:
            response_file = response_dir / f"response_{task_id}.json"
            with open(response_file, 'w') as f:
                json.dump({
                    "task_id": task_id,
                    "response": response_text
                }, f)
            print(f"✓ Response saved")
        else:
            print(f"✗ No response provided, skipping")

if __name__ == "__main__":
    main()
