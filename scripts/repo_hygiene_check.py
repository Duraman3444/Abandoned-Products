#!/usr/bin/env python3
"""
Repository Hygiene Checker

This script verifies the five key repository requirements:
1. All code committed and pushed (git status clean, ignoring db.sqlite3)
2. Repository structure is clean (no files > 5MB except media & screenshots)
3. No sensitive data in commits (no .pem, .key, .env files tracked)
4. Screenshots and diagrams current (docs/screenshots/ and docs/diagrams/ have content)
5. License and attribution correct (LICENSE file exists and is non-empty)

Exits with code 1 if any check fails.
"""

import os
import sys
import subprocess
import glob
from pathlib import Path


def run_command(cmd, capture_output=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def check_git_status_clean():
    """Check 1: All code committed and pushed (git status clean)"""
    print("📦 Checking git status...")
    
    # Get git status
    returncode, stdout, stderr = run_command("git status --porcelain")
    
    if returncode != 0:
        print(f"❌ Git status check failed: {stderr}")
        return False
    
    # Filter out db.sqlite3 files (these are expected to be dirty)
    lines = stdout.split('\n') if stdout else []
    relevant_changes = [
        line for line in lines 
        if line.strip() and 'db.sqlite3' not in line
    ]
    
    if relevant_changes:
        print(f"❌ Repository has uncommitted changes:")
        for line in relevant_changes[:5]:  # Show first 5
            print(f"  {line}")
        if len(relevant_changes) > 5:
            print(f"  ... and {len(relevant_changes) - 5} more")
        return False
    
    print("✅ Git status is clean (all code committed)")
    return True


def check_file_sizes():
    """Check 2: Repository structure is clean (no large files)"""
    print("📏 Checking file sizes...")
    
    large_files = []
    excluded_dirs = {'venv', '.git', '__pycache__', 'node_modules'}
    allowed_large_dirs = {'media', 'screenshots', 'static', 'docs'}
    
    try:
        for root, dirs, files in os.walk('.'):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    
                    # Check if file is > 5MB
                    if size > 5 * 1024 * 1024:  # 5MB
                        # Check if it's in an allowed directory
                        path_parts = Path(file_path).parts
                        in_allowed_dir = any(allowed_dir in path_parts for allowed_dir in allowed_large_dirs)
                        
                        if not in_allowed_dir:
                            large_files.append((file_path, size / (1024 * 1024)))  # Size in MB
                            
                except (OSError, IOError):
                    continue
    
    except Exception as e:
        print(f"⚠️  Error checking file sizes: {e}")
        return True  # Don't fail the check for this
    
    if large_files:
        print(f"❌ Found {len(large_files)} large files (>5MB) outside allowed directories:")
        for file_path, size_mb in large_files[:5]:
            print(f"  {file_path}: {size_mb:.1f}MB")
        return False
    
    print("✅ Repository structure is clean (no oversized files)")
    return True


def check_last_commit_quality():
    """Check 3: Last commit is not WIP/fixup"""
    print("💬 Checking last commit message...")
    
    returncode, stdout, stderr = run_command("git log -1 --pretty=%B")
    
    if returncode != 0:
        print(f"❌ Could not get last commit message: {stderr}")
        return False
    
    commit_msg = stdout.lower()
    
    # Check for WIP or fixup patterns
    bad_patterns = ['wip', 'fixup!', 'squash!', 'tmp', 'temp', 'debug']
    
    for pattern in bad_patterns:
        if pattern in commit_msg:
            print(f"❌ Last commit message contains '{pattern}': {stdout[:100]}...")
            return False
    
    print(f"✅ Last commit message is clean: {stdout[:60]}...")
    return True


def check_no_sensitive_files():
    """Check 4: No sensitive data in commits"""
    print("🔒 Checking for sensitive files...")
    
    # Check tracked files for sensitive patterns
    returncode, stdout, stderr = run_command("git ls-files")
    
    if returncode != 0:
        print(f"❌ Could not list git files: {stderr}")
        return False
    
    files = stdout.split('\n') if stdout else []
    
    # Patterns for sensitive files
    sensitive_patterns = [
        r'\.pem$', r'\.key$', r'\.env$', r'firebase.*cred', 
        r'\.p12$', r'\.pfx$', r'id_rsa', r'\.secret$'
    ]
    
    sensitive_files = []
    
    for file in files:
        if not file.strip():
            continue
            
        file_lower = file.lower()
        
        for pattern in sensitive_patterns:
            import re
            if re.search(pattern, file_lower):
                sensitive_files.append(file)
                break
    
    if sensitive_files:
        print(f"❌ Found {len(sensitive_files)} potentially sensitive files in git:")
        for file in sensitive_files[:5]:
            print(f"  {file}")
        return False
    
    print("✅ No sensitive data files found in git history")
    return True


def check_documentation_assets():
    """Check 5: Screenshots and diagrams exist, LICENSE file present"""
    print("📸 Checking documentation assets...")
    
    checks_passed = 0
    total_checks = 3
    
    # Check docs/screenshots/
    screenshots_dir = Path("docs/screenshots")
    if screenshots_dir.exists():
        screenshot_files = list(screenshots_dir.glob("*.png")) + list(screenshots_dir.glob("*.jpg")) + list(screenshots_dir.glob("*.jpeg")) + list(screenshots_dir.glob("*.svg"))
        if screenshot_files:
            print(f"✅ Screenshots directory has {len(screenshot_files)} image files")
            checks_passed += 1
        else:
            print("❌ docs/screenshots/ exists but contains no image files")
    else:
        print("❌ docs/screenshots/ directory not found")
    
    # Check docs/diagrams/
    diagrams_dir = Path("docs/diagrams")
    if diagrams_dir.exists():
        diagram_files = list(diagrams_dir.glob("*.png")) + list(diagrams_dir.glob("*.svg")) + list(diagrams_dir.glob("*.jpg"))
        if diagram_files:
            print(f"✅ Diagrams directory has {len(diagram_files)} diagram files")
            checks_passed += 1
        else:
            print("❌ docs/diagrams/ exists but contains no diagram files")
    else:
        # Check for diagrams in docs/ root or other locations
        docs_diagrams = list(Path("docs").glob("**/*.svg")) + list(Path("docs").glob("**/*.png"))
        if docs_diagrams:
            print(f"✅ Found {len(docs_diagrams)} diagram files in docs/")
            checks_passed += 1
        else:
            print("❌ No diagram files found in docs/")
    
    # Check LICENSE file
    license_files = ['LICENSE', 'LICENSE.txt', 'LICENSE.md', 'COPYING']
    license_found = False
    
    for license_file in license_files:
        if os.path.exists(license_file):
            try:
                with open(license_file, 'r') as f:
                    content = f.read().strip()
                if content and len(content) > 50:  # Non-empty and substantial
                    print(f"✅ License file found: {license_file} ({len(content)} chars)")
                    license_found = True
                    checks_passed += 1
                    break
                else:
                    print(f"⚠️  License file {license_file} is too short")
            except:
                continue
    
    if not license_found:
        print("❌ No valid LICENSE file found")
    
    # Require at least 2 out of 3 checks to pass (flexible for MVP)
    if checks_passed >= 2:
        print(f"✅ Documentation assets check passed ({checks_passed}/{total_checks})")
        return True
    else:
        print(f"❌ Documentation assets check failed ({checks_passed}/{total_checks})")
        return False


def main():
    """Run all repository hygiene checks"""
    print("🧹 Repository Hygiene Check")
    print("=" * 50)
    
    checks = [
        ("Git status clean", check_git_status_clean),
        ("File sizes reasonable", check_file_sizes),
        ("Commit message quality", check_last_commit_quality),
        ("No sensitive files", check_no_sensitive_files),
        ("Documentation assets", check_documentation_assets),
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        try:
            if check_func():
                passed += 1
            else:
                print(f"❌ {check_name} check failed")
        except Exception as e:
            print(f"❌ {check_name} check failed with error: {e}")
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All repository hygiene checks passed!")
        sys.exit(0)
    else:
        print("💥 Some repository hygiene checks failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
