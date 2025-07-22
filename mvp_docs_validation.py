#!/usr/bin/env python3
"""
MVP Documentation Completeness Validation
"""

import os
import sys

def validate_document(file_path, required_sections):
    """Validate that a document contains required sections"""
    if not os.path.exists(file_path):
        return False, ["File does not exist"]
    
    try:
        with open(file_path, 'r') as f:
            content = f.read().lower()
        
        missing_sections = []
        for section in required_sections:
            if section.lower() not in content:
                missing_sections.append(section)
        
        return len(missing_sections) == 0, missing_sections
    except Exception as e:
        return False, [f"Error reading file: {e}"]

def validate_deployment_docs():
    """Validate DEPLOYMENT.md completeness"""
    print("📋 Validating DEPLOYMENT.md...")
    
    required_sections = [
        "Prerequisites",
        "Docker",
        "docker-compose",
        "Environment",
        "migrate",
        "createsuperuser",
        "Production",
        "SSL",
        "backup",
        "monitoring"
    ]
    
    is_complete, missing = validate_document('docs/DEPLOYMENT.md', required_sections)
    
    if is_complete:
        print("   ✅ DEPLOYMENT.md is comprehensive")
    else:
        print(f"   ⚠️  DEPLOYMENT.md missing sections: {missing}")
    
    return is_complete

def validate_api_docs():
    """Validate API_USAGE.md completeness"""
    print("📋 Validating API_USAGE.md...")
    
    required_sections = [
        "Authentication",
        "Base URL", 
        "Students",
        "Applicants",
        "examples",
        "curl",
        "JSON",
        "Error",
        "Rate limiting"
    ]
    
    is_complete, missing = validate_document('docs/API_USAGE.md', required_sections)
    
    if is_complete:
        print("   ✅ API_USAGE.md is comprehensive")
    else:
        print(f"   ⚠️  API_USAGE.md missing sections: {missing}")
    
    return is_complete

def validate_qa_report():
    """Validate QA_REPORT.md completeness"""
    print("📋 Validating QA_REPORT.md...")
    
    required_sections = [
        "Executive Summary",
        "Test Results",
        "Authentication",
        "Dashboard",
        "Mobile",
        "Performance",
        "Security",
        "Recommendations",
        "Production Readiness"
    ]
    
    is_complete, missing = validate_document('docs/QA_REPORT.md', required_sections)
    
    if is_complete:
        print("   ✅ QA_REPORT.md is comprehensive")
    else:
        print(f"   ⚠️  QA_REPORT.md missing sections: {missing}")
    
    return is_complete

def check_document_sizes():
    """Check that documents are substantial enough"""
    print("📏 Checking document sizes...")
    
    min_sizes = {
        'docs/DEPLOYMENT.md': 200,     # At least 200 lines
        'docs/API_USAGE.md': 200,      # At least 200 lines  
        'docs/QA_REPORT.md': 150       # At least 150 lines
    }
    
    all_adequate = True
    for file_path, min_lines in min_sizes.items():
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                line_count = len(f.readlines())
            
            if line_count >= min_lines:
                print(f"   ✅ {file_path}: {line_count} lines (adequate)")
            else:
                print(f"   ⚠️  {file_path}: {line_count} lines (needs more content)")
                all_adequate = False
        else:
            print(f"   ❌ {file_path}: Missing")
            all_adequate = False
    
    return all_adequate

def run_docs_validation():
    """Run complete documentation validation"""
    print("🎯 MVP DOCUMENTATION VALIDATION")
    print("=" * 60)
    
    results = {
        'deployment': validate_deployment_docs(),
        'api_usage': validate_api_docs(), 
        'qa_report': validate_qa_report(),
        'sizes': check_document_sizes()
    }
    
    print(f"\n📊 DOCUMENTATION VALIDATION RESULTS:")
    for doc_type, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {doc_type.replace('_', ' ').title()}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    pass_rate = (passed_tests / total_tests) * 100
    
    print(f"\n   Overall: {passed_tests}/{total_tests} validations passed ({pass_rate:.1f}%)")
    
    # MVP Assessment - all docs should be present and adequate
    mvp_ready = all(results.values())
    
    if mvp_ready:
        print(f"\n✅ DOCUMENTATION: MVP READY")
        print("   📝 All required documentation is complete and comprehensive")
    else:
        print(f"\n⚠️  DOCUMENTATION: NEEDS IMPROVEMENT")
        print("   📝 Some documentation sections need enhancement")
    
    return mvp_ready

if __name__ == "__main__":
    success = run_docs_validation()
    sys.exit(0 if success else 1)
