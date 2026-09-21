#!/usr/bin/env python3
import time
import urllib.request
import urllib.error
import subprocess
import json
import sys

BASE_URL = "http://127.0.0.1:8080"

def print_step(msg):
    print(f"\n\033[94m==> {msg}\033[0m")

def docker_action(action, container):
    subprocess.run(["docker", "compose", action, container], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def measure_traffic(duration=5, expected_instances=None):
    success = 0
    errors = 0
    instances_seen = set()
    
    start = time.time()
    while time.time() - start < duration:
        try:
            req = urllib.request.urlopen(f"{BASE_URL}/instance", timeout=1)
            if req.getcode() == 200:
                success += 1
                data = json.loads(req.read().decode())
                instances_seen.add(data.get("instance_id"))
            else:
                errors += 1
        except Exception:
            errors += 1
        time.sleep(0.1) # Simulate rapid traffic
        
    print(f"  Traffic Stats: {success} successful requests, {errors} errors.")
    print(f"  Instances responding: {list(instances_seen)}")
    
    if expected_instances and not all(inst in instances_seen for inst in expected_instances):
        print(f"\033[91mFAIL\033[0m: Expected instances {expected_instances} but got {instances_seen}")
        sys.exit(1)
        
    return success, errors

if __name__ == "__main__":
    print_step("Pre-flight check (Both backends should be alive)")
    measure_traffic(duration=3, expected_instances=["app-01", "app-02"])

    print_step("Simulating failure: Stopping app-01")
    docker_action("stop", "app-01")
    
    # NGINX needs a second to realize app-01 is dead and reroute to app-02
    time.sleep(2) 

    print_step("Measuring traffic during failure (app-02 should handle everything)")
    success, errors = measure_traffic(duration=5, expected_instances=["app-02"])
    if success == 0:
        print("\033[91mFAIL\033[0m: Site went down completely!")
        sys.exit(1)

    print_step("Recovering: Starting app-01")
    docker_action("start", "app-01")
    
    # Wait for app-01 to boot up and pass Docker Healthchecks
    print("  Waiting 10 seconds for app-01 to become healthy...")
    time.sleep(10)

    print_step("Verifying recovery (Both backends should serve traffic again)")
    measure_traffic(duration=5, expected_instances=["app-01", "app-02"])

    print("\n\033[92mFAILURE TEST PASSED SUCCESSFULLY!\033[0m")
    sys.exit(0)