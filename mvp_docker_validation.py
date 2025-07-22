#!/usr/bin/env python3
"""
MVP Docker Configuration Validation
Validates Docker setup without requiring Docker to be installed
"""

import os
import sys
from pathlib import Path

def validate_docker_files():
    """Validate that required Docker files exist and are properly configured"""
    print("🐳 Validating Docker Configuration...")
    print("=" * 50)
    
    required_files = [
        'docker/Dockerfile',
        'docker/docker-compose.yml', 
        'docker/nginx.conf',
        'docker/test_docker.sh'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
            print(f"   ❌ Missing: {file_path}")
        else:
            print(f"   ✅ Found: {file_path}")
    
    if missing_files:
        print(f"\n❌ Docker configuration incomplete: {len(missing_files)} files missing")
        return False
    
    print(f"\n✅ All Docker configuration files present")
    return True

def validate_dockerfile():
    """Validate Dockerfile content"""
    print("\n🔧 Validating Dockerfile...")
    
    try:
        with open('docker/Dockerfile', 'r') as f:
            dockerfile_content = f.read()
        
        required_sections = [
            'FROM python:',
            'WORKDIR',
            'requirements.txt',
            'RUN pip install',
            'COPY schooldriver-modern',
            'EXPOSE 8000',
            'CMD'
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in dockerfile_content:
                missing_sections.append(section)
                print(f"   ❌ Missing: {section}")
            else:
                print(f"   ✅ Found: {section}")
        
        if missing_sections:
            print(f"\n⚠️  Dockerfile may be incomplete: {len(missing_sections)} sections missing")
            return False
        
        print(f"\n✅ Dockerfile appears well-formed")
        return True
        
    except Exception as e:
        print(f"   ❌ Error reading Dockerfile: {e}")
        return False

def validate_docker_compose():
    """Validate docker-compose.yml content"""
    print("\n🔧 Validating docker-compose.yml...")
    
    try:
        with open('docker/docker-compose.yml', 'r') as f:
            compose_content = f.read()
        
        required_services = ['web', 'postgres', 'redis', 'nginx']
        required_sections = [
            'version:',
            'services:',
            'volumes:',
            'ports:',
            'environment:',
            'healthcheck:'
        ]
        
        missing_services = []
        for service in required_services:
            if f'{service}:' not in compose_content:
                missing_services.append(service)
                print(f"   ❌ Missing service: {service}")
            else:
                print(f"   ✅ Found service: {service}")
        
        missing_sections = []
        for section in required_sections:
            if section not in compose_content:
                missing_sections.append(section)
                print(f"   ❌ Missing section: {section}")
            else:
                print(f"   ✅ Found section: {section}")
        
        if missing_services or missing_sections:
            print(f"\n⚠️  docker-compose.yml may be incomplete")
            return False
        
        print(f"\n✅ docker-compose.yml appears well-formed")
        return True
        
    except Exception as e:
        print(f"   ❌ Error reading docker-compose.yml: {e}")
        return False

def validate_health_endpoint():
    """Check if health endpoint exists in the codebase"""
    print("\n🏥 Validating health endpoint...")
    
    # Look for health endpoint in URLs
    url_files = [
        'schooldriver-modern/schooldriver_modern/urls.py',
        'schooldriver-modern/students/urls.py',
        'schooldriver-modern/admissions/urls.py'
    ]
    
    health_endpoint_found = False
    for url_file in url_files:
        if os.path.exists(url_file):
            try:
                with open(url_file, 'r') as f:
                    content = f.read()
                    if 'health' in content.lower():
                        health_endpoint_found = True
                        print(f"   ✅ Health endpoint reference found in {url_file}")
                        break
            except:
                continue
    
    if not health_endpoint_found:
        print("   ⚠️  No health endpoint found - may need implementation")
        return False
    
    print("   ✅ Health endpoint configuration detected")
    return True

def check_environment_requirements():
    """Check if environment is properly configured for Docker"""
    print("\n🌍 Checking Environment Requirements...")
    
    # Check for requirements.txt
    if os.path.exists('schooldriver-modern/requirements.txt'):
        print("   ✅ requirements.txt found")
        requirements_ok = True
    else:
        print("   ❌ requirements.txt missing")
        requirements_ok = False
    
    # Check for Django settings
    if os.path.exists('schooldriver-modern/schooldriver_modern/settings.py'):
        print("   ✅ Django settings found")
        settings_ok = True
    else:
        print("   ❌ Django settings missing")
        settings_ok = False
    
    # Check for manage.py
    if os.path.exists('schooldriver-modern/manage.py'):
        print("   ✅ Django manage.py found")
        manage_ok = True
    else:
        print("   ❌ manage.py missing")
        manage_ok = False
    
    return requirements_ok and settings_ok and manage_ok

def run_docker_validation():
    """Run complete Docker validation suite"""
    print("🎯 MVP DOCKER VALIDATION")
    print("=" * 60)
    
    results = {
        'files': validate_docker_files(),
        'dockerfile': validate_dockerfile(),
        'compose': validate_docker_compose(),
        'health': validate_health_endpoint(),
        'environment': check_environment_requirements()
    }
    
    # Summary
    print(f"\n📊 DOCKER VALIDATION RESULTS:")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name.title()}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    pass_rate = (passed_tests / total_tests) * 100
    
    print(f"\n   Overall: {passed_tests}/{total_tests} tests passed ({pass_rate:.1f}%)")
    
    # MVP Assessment
    critical_tests = ['files', 'dockerfile', 'compose', 'environment']
    critical_passed = sum(results[test] for test in critical_tests if test in results)
    critical_total = len(critical_tests)
    
    mvp_ready = critical_passed >= critical_total
    
    if mvp_ready:
        print(f"\n✅ DOCKER: MVP READY")
        print("   📝 Note: Docker configuration is complete and ready for deployment")
        if not results.get('health', True):
            print("   📝 Recommendation: Add health endpoint for production monitoring")
    else:
        print(f"\n❌ DOCKER: NOT MVP READY")
        print("   📝 Critical Docker configuration issues need to be resolved")
    
    return mvp_ready

if __name__ == "__main__":
    success = run_docker_validation()
    sys.exit(0 if success else 1)
