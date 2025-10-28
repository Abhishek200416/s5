#!/usr/bin/env python3
"""
Find all .to_list() calls without proper await
"""
import re

with open('/app/backend/server.py', 'r') as f:
    lines = f.readlines()

print("=" * 80)
print("FINDING .to_list() CALLS WITHOUT PROPER AWAIT")
print("=" * 80)

issues_found = []

for i, line in enumerate(lines, 1):
    if '.to_list(' in line:
        # Check if this line or previous lines have await
        has_await = False
        
        # Check current line
        if 'await' in line and line.index('await') < line.index('.to_list('):
            has_await = True
        
        # Check if this is a continuation of a previous await
        # Look back up to 5 lines
        if not has_await:
            for j in range(max(0, i-6), i):
                prev_line = lines[j]
                if '=' in prev_line and 'await' in prev_line:
                    # This might be a multi-line statement with await
                    has_await = True
                    break
        
        if not has_await:
            issues_found.append((i, line.strip()))
            print(f"\n❌ Line {i}: Missing await")
            print(f"   {line.strip()}")
            
            # Show context
            print("   Context:")
            for j in range(max(0, i-3), min(len(lines), i+2)):
                marker = ">>>" if j == i-1 else "   "
                print(f"   {marker} {j+1}: {lines[j].rstrip()}")

print("\n" + "=" * 80)
print(f"Total issues found: {len(issues_found)}")
print("=" * 80)
