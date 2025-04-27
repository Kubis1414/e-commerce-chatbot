"""
Simple script to verify the provider test logging functionality.
This script runs a single provider test and checks if the result files are created.
"""

import os
import subprocess
from pathlib import Path
import json
import time

# Colors for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(text, color):
    print(f"{color}{text}{Colors.END}")

def main():
    print_colored("\n==== Provider Test Logging Verification ====\n", Colors.BOLD)
    
    # Step 1: Count existing files
    results_dir = Path("test_results")
    csv_files_before = list(results_dir.glob("provider_test_results_*.csv"))
    json_files_before = list(results_dir.glob("provider_test_detail_*.json"))
    
    print(f"Found {len(csv_files_before)} CSV files and {len(json_files_before)} JSON files before test")
    
    # Step 2: Run a single test
    print_colored("\nRunning a single provider test...", Colors.YELLOW)
    provider = "OPENAI"  # You can change this to test a different provider
    
    try:
        cmd = ["pytest", f"tests/provider_tests/test_providers.py::test_provider_{provider.lower()}", "-v"]
        print(f"Command: {' '.join(cmd)}")
        
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        # Print a summary of the test output
        if process.returncode == 0:
            print_colored("Test executed successfully!", Colors.GREEN)
        else:
            print_colored("Test failed, but we'll still check for log files", Colors.YELLOW)
            print(f"Error: {process.stderr}")
    
    except Exception as e:
        print_colored(f"Error running test: {e}", Colors.RED)
        return
    
    # Step 3: Count files after test
    time.sleep(1)  # Give a moment for file system to update
    csv_files_after = list(results_dir.glob("provider_test_results_*.csv"))
    json_files_after = list(results_dir.glob("provider_test_detail_*.json"))
    
    new_csv_files = len(csv_files_after) - len(csv_files_before)
    new_json_files = len(json_files_after) - len(json_files_before)
    
    # Step 4: Verify results
    print_colored("\n==== Results ====\n", Colors.BOLD)
    
    if new_csv_files > 0:
        print_colored(f"✓ Created {new_csv_files} new CSV file(s)", Colors.GREEN)
        # Show the newest CSV file
        newest_csv = max(csv_files_after, key=os.path.getctime)
        print(f"  Latest CSV file: {newest_csv.name}")
    else:
        print_colored("✗ No new CSV files were created", Colors.RED)
    
    if new_json_files > 0:
        print_colored(f"✓ Created {new_json_files} new JSON file(s)", Colors.GREEN)
        # Show the newest JSON file
        newest_json = max(json_files_after, key=os.path.getctime)
        print(f"  Latest JSON file: {newest_json.name}")
        
        # Optionally peek at the JSON content
        try:
            with open(newest_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print("\nJSON file contains these keys:")
                print("  " + ", ".join(data.keys()))
                
                # Verify that the important data is present
                required_keys = ['llm_provider', 'customer_input', 'evaluation', 'flow_result']
                missing_keys = [key for key in required_keys if key not in data]
                
                if missing_keys:
                    print_colored(f"✗ Missing required keys: {', '.join(missing_keys)}", Colors.RED)
                else:
                    print_colored("✓ All required data present in JSON file", Colors.GREEN)
        except Exception as e:
            print_colored(f"Error reading JSON file: {e}", Colors.RED)
    else:
        print_colored("✗ No new JSON files were created", Colors.RED)
    
    print_colored("\nLogging verification complete!", Colors.BOLD)

if __name__ == "__main__":
    main()
