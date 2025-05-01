import sys
import os
import subprocess
import time

def test_component(component_name, script_path):
    print(f"\nTesting {component_name}...")
    try:
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for 5 seconds to see if it starts
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            print(f"{component_name} started successfully!")
            process.terminate()
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"Error starting {component_name}:")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False
            
    except Exception as e:
        print(f"Exception while testing {component_name}: {str(e)}")
        return False

def main():
    components = {
        "Client": "client/main.py",
        "Intermediate": "intermediate/main.py",
        "Server": "server/main.py"
    }
    
    print("Testing all components...")
    for name, path in components.items():
        if not os.path.exists(path):
            print(f"Error: {path} does not exist!")
            continue
        test_component(name, path)

if __name__ == "__main__":
    main() 