#!/usr/bin/env python3
"""
Simple validation script for Docker configuration files.
Validates that Docker configs are syntactically correct.
"""

import yaml
import os
import sys

def validate_dockerfile():
    """Check that Dockerfile exists and contains required instructions."""
    dockerfile_path = "docker/Dockerfile"
    
    if not os.path.exists(dockerfile_path):
        print("❌ Dockerfile not found")
        return False
    
    with open(dockerfile_path, 'r') as f:
        content = f.read()
    
    required_instructions = ['FROM', 'WORKDIR', 'COPY', 'RUN', 'EXPOSE', 'CMD']
    missing = []
    
    for instruction in required_instructions:
        if instruction not in content:
            missing.append(instruction)
    
    if missing:
        print(f"❌ Dockerfile missing instructions: {', '.join(missing)}")
        return False
    
    print("✅ Dockerfile validation passed")
    return True

def validate_docker_compose():
    """Check that docker-compose.yml is valid YAML with required services."""
    compose_path = "docker/docker-compose.yml"
    
    if not os.path.exists(compose_path):
        print("❌ docker-compose.yml not found")
        return False
    
    try:
        with open(compose_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"❌ docker-compose.yml invalid YAML: {e}")
        return False
    
    # Check required services
    required_services = ['web', 'postgres', 'redis']
    if 'services' not in config:
        print("❌ No 'services' section found in docker-compose.yml")
        return False
    
    services = config['services']
    missing_services = []
    
    for service in required_services:
        if service not in services:
            missing_services.append(service)
    
    if missing_services:
        print(f"❌ Missing services: {', '.join(missing_services)}")
        return False
    
    # Check web service has correct port mapping
    web_service = services.get('web', {})
    ports = web_service.get('ports', [])
    if not any('8080:8000' in str(port) for port in ports):
        print("❌ Web service should map port 8080:8000")
        return False
    
    print("✅ docker-compose.yml validation passed")
    return True

def validate_requirements():
    """Check that requirements.txt exists with essential packages."""
    req_path = "schooldriver-modern/requirements.txt"
    
    if not os.path.exists(req_path):
        print("❌ requirements.txt not found")
        return False
    
    with open(req_path, 'r') as f:
        content = f.read().lower()
    
    required_packages = ['django', 'gunicorn', 'psycopg2']
    missing = []
    
    for package in required_packages:
        if package not in content:
            missing.append(package)
    
    if missing:
        print(f"❌ requirements.txt missing packages: {', '.join(missing)}")
        return False
    
    print("✅ requirements.txt validation passed")
    return True

def main():
    """Run all validation checks."""
    print("🔍 Validating Docker configuration...\n")
    
    checks = [
        validate_dockerfile(),
        validate_docker_compose(),
        validate_requirements()
    ]
    
    if all(checks):
        print("\n🎉 All Docker configuration files are valid!")
        return 0
    else:
        print("\n💥 Some validation checks failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
