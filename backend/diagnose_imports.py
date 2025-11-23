#!/usr/bin/env python3
"""
Diagnostic script to find all import issues in the codebase.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def find_python_files(root_dir):
    """Find all Python files in the project."""
    python_files = []
    for root, dirs, files in os.walk(root_dir):
        # Skip venv and __pycache__
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules']]
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def check_imports(file_path):
    """Check for problematic imports in a file."""
    issues = []

    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            content = f.read()
        except Exception as e:
            return [(file_path, f"Error reading file: {e}")]

    lines = content.split('\n')

    for i, line in enumerate(lines, 1):
        # Check for app.db.session imports
        if 'from app.db.session import' in line or 'from app.db import' in line:
            issues.append((file_path, i, line.strip(), 'BAD_DB_IMPORT', 'Should use app.core.database'))

        # Check for direct database imports that should use get_db dependency
        if 'from app.db.session import get_db' in line:
            issues.append((file_path, i, line.strip(), 'BAD_GET_DB_IMPORT', 'Should use app.api.deps or app.core.database'))

    return issues

def check_missing_modules():
    """Check for modules that are imported but don't exist."""
    missing = []

    # Check if app.db exists
    if not os.path.exists('app/db'):
        missing.append(('app/db', 'Directory does not exist - should use app.core.database'))

    # Check if app.api.deps exists
    if not os.path.exists('app/api/deps.py'):
        missing.append(('app/api/deps.py', 'File does not exist'))

    return missing

def main():
    print("=" * 80)
    print("DIAGNOSTIC REPORT: Import Issues")
    print("=" * 80)
    print()

    # Check for missing modules
    print("1. MISSING MODULES/DIRECTORIES:")
    print("-" * 80)
    missing = check_missing_modules()
    if missing:
        for module, reason in missing:
            print(f"  ❌ {module}")
            print(f"     → {reason}")
    else:
        print("  ✓ All expected modules exist")
    print()

    # Find all Python files
    python_files = find_python_files('app')
    print(f"2. SCANNING {len(python_files)} PYTHON FILES:")
    print("-" * 80)

    # Check imports in all files
    all_issues = []
    files_with_issues = set()

    for file_path in python_files:
        issues = check_imports(file_path)
        if issues:
            all_issues.extend(issues)
            files_with_issues.add(file_path)

    # Group issues by type
    issues_by_type = defaultdict(list)
    for issue in all_issues:
        if len(issue) == 5:
            file_path, line_num, line_content, issue_type, suggestion = issue
            issues_by_type[issue_type].append((file_path, line_num, line_content, suggestion))

    # Report issues
    print()
    print("3. IMPORT ISSUES FOUND:")
    print("-" * 80)

    if not all_issues:
        print("  ✓ No import issues found!")
    else:
        for issue_type, issues in sorted(issues_by_type.items()):
            print(f"\n  {issue_type} ({len(issues)} occurrences):")
            for file_path, line_num, line_content, suggestion in issues:
                rel_path = os.path.relpath(file_path)
                print(f"    ❌ {rel_path}:{line_num}")
                print(f"       {line_content}")
                print(f"       → Fix: {suggestion}")

    print()
    print("=" * 80)
    print(f"SUMMARY: {len(files_with_issues)} files with issues, {len(all_issues)} total issues")
    print("=" * 80)
    print()

    # Generate fix commands
    if all_issues:
        print("4. SUGGESTED FIXES:")
        print("-" * 80)
        print("Run these sed commands to fix the issues:")
        print()

        files_to_fix = set()
        for issue in all_issues:
            if len(issue) == 5:
                file_path = issue[0]
                files_to_fix.add(file_path)

        for file_path in sorted(files_to_fix):
            rel_path = os.path.relpath(file_path)
            print(f"# Fix {rel_path}")
            print(f"sed -i '' 's/from app\\.db\\.session import/from app.core.database import/g' {rel_path}")
            print(f"sed -i '' 's/from app\\.db import/from app.core.database import/g' {rel_path}")
            print()

if __name__ == '__main__':
    main()
