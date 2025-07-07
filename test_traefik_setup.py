#!/usr/bin/env python3
"""
Test script to verify Traefik setup and connectivity.

This script helps diagnose Traefik configuration issues by:
1. Checking if Traefik dashboard is accessible
2. Verifying agent service discovery
3. Testing agent connectivity through Traefik
4. Checking hosts file configuration
"""

import requests
import subprocess
import sys
from pathlib import Path


def check_traefik_dashboard():
    """Check if Traefik dashboard is accessible."""
    print("🔍 Checking Traefik dashboard...")
    try:
        response = requests.get("http://localhost:8080/api/http/services", timeout=5)
        if response.status_code == 200:
            services = response.json()
            print(f"✅ Traefik dashboard accessible. Found {len(services)} HTTP services:")
            for service_name, service_data in services.items():
                print(f"   - {service_name}: {service_data.get('loadBalancer', {}).get('servers', [])}")
            return True
        else:
            print(f"❌ Traefik dashboard returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to Traefik dashboard: {e}")
        return False


def check_hosts_file():
    """Check if hosts file contains the required entries."""
    print("\n🔍 Checking hosts file configuration...")
    try:
        with open("/etc/hosts", "r") as f:
            hosts_content = f.read()
        
        required_hosts = ["mary.local", "rick.local"]
        missing_hosts = []
        
        for host in required_hosts:
            if host not in hosts_content:
                missing_hosts.append(host)
        
        if missing_hosts:
            print(f"❌ Missing hosts entries: {missing_hosts}")
            print("Add these lines to /etc/hosts:")
            for host in missing_hosts:
                print(f"127.0.0.1 {host}")
            return False
        else:
            print("✅ All required hosts entries found in /etc/hosts")
            return True
            
    except PermissionError:
        print("❌ Cannot read /etc/hosts (permission denied)")
        return False
    except FileNotFoundError:
        print("❌ /etc/hosts file not found")
        return False


def test_agent_connectivity():
    """Test connectivity to agents through Traefik."""
    print("\n🔍 Testing agent connectivity through Traefik...")
    agents = ["mary.local", "rick.local"]
    
    success_count = 0
    for agent in agents:
        try:
            print(f"   Testing {agent}...")
            response = requests.get(f"http://{agent}", timeout=10)
            if response.status_code == 200:
                print(f"   ✅ {agent} accessible")
                success_count += 1
            else:
                print(f"   ❌ {agent} returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {agent} failed: {e}")
    
    return success_count == len(agents)


def check_docker_containers():
    """Check if containers are running."""
    print("\n🔍 Checking Docker containers...")
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        
        # Check if required containers are running
        container_names = result.stdout.lower()
        required_containers = ["traefik", "mary", "rick"]
        missing_containers = []
        
        for container in required_containers:
            if container not in container_names:
                missing_containers.append(container)
        
        if missing_containers:
            print(f"❌ Missing containers: {missing_containers}")
            return False
        else:
            print("✅ All required containers are running")
            return True
            
    except subprocess.CalledProcessError:
        print("❌ Failed to check Docker containers")
        return False
    except FileNotFoundError:
        print("❌ Docker command not found")
        return False


def main():
    """Run all tests."""
    print("🚀 Traefik Setup Diagnostic Tool")
    print("=" * 50)
    
    tests = [
        ("Docker Containers", check_docker_containers),
        ("Traefik Dashboard", check_traefik_dashboard),
        ("Hosts File", check_hosts_file),
        ("Agent Connectivity", test_agent_connectivity),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Traefik setup is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
