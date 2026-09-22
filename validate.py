#!/usr/bin/env python3
#!/usr/bin/env python3
import time
import urllib.request
import urllib.error
import socket
import json
import sys

BASE_URL = "http://127.0.0.1:8080"
TIMEOUT = 30  # seconds to wait for boot

def print_result(name, success, details=""):
    status = "\033[92mPASS\033[0m" if success else "\033[91mFAIL\033[0m"
    print(f"[{status}] {name} {details}")
    if not success:
        sys.exit(1)

def wait_for_ready():
    print(f"Waiting up to {TIMEOUT}s for {BASE_URL}/ready...")
    start = time.time()
    while time.time() - start < TIMEOUT:
        try:
            req = urllib.request.urlopen(f"{BASE_URL}/ready", timeout=2)
            if req.getcode() == 200:
                data = json.loads(req.read().decode())
                if data.get("status") == "ready":
                    print_result("System Readiness", True)
                    return
        except urllib.error.URLError:
            pass
        time.sleep(2)
    print_result("System Readiness", False, "Timed out waiting for dependencies.")

def test_endpoints():
    endpoints = ["/", "/health", "/records", "/counter"]
    for ep in endpoints:
        try:
            req = urllib.request.urlopen(f"{BASE_URL}{ep}", timeout=2)
            if req.getcode() in [200, 201]:
                print_result(f"Endpoint {ep}", True)
            else:
                print_result(f"Endpoint {ep}", False, f"Returned {req.getcode()}")
        except Exception as e:
            print_result(f"Endpoint {ep}", False, str(e))

def test_load_balancing():
    instances_seen = set()
    print("Checking load balancing...")
    for _ in range(12):
        try:
            req = urllib.request.urlopen(f"{BASE_URL}/instance", timeout=2)
            data = json.loads(req.read().decode())
            instances_seen.add(data.get("instance_id"))
        except Exception:
            pass
        time.sleep(0.2)
    
    if "app-01" in instances_seen and "app-02" in instances_seen:
        print_result("Load Balancing", True, f"Instances responding: {sorted(instances_seen)}")
    else:
        print_result("Load Balancing", False, f"Only saw: {instances_seen}")

def test_port_isolation():
    prohibited_ports = {"Postgres": 15432, "Postgres (Default)": 5432, "Redis": 16379, "Redis (Default)": 6379, "App-01": 8081}
    for name, port in prohibited_ports.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        if result == 0:
            print_result(f"Port Isolation ({name} on {port})", False, "Port is exposed!")
        else:
            print_result(f"Port Isolation ({name} on {port})", True, "Port safely blocked.")

if __name__ == "__main__":
    print("Starting Environment Validation...")
    wait_for_ready()
    test_endpoints()
    test_load_balancing()
    test_port_isolation()
    print("\n\033[92mALL TESTS PASSED SUCCESSFULLY!\033[0m")
    sys.exit(0)