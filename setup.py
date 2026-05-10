#!/usr/bin/env python
"""
Setup script untuk install MAVProxy stack dependencies
"""

import subprocess
import sys
import os
from pathlib import Path

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
END = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{END}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{END}")

def print_error(text):
    print(f"{RED}❌ {text}{END}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{END}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{END}")

def run_command(cmd, description=""):
    """Run command and return success status"""
    if description:
        print(f"Running: {description}...")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            if description:
                print_success(description)
            return True
        else:
            if description:
                print_error(f"{description} failed")
                if result.stderr:
                    print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print_error(f"Command failed: {e}")
        return False

def check_python_version():
    """Check if Python version is 3.8+"""
    print_info(f"Python version: {sys.version}")
    
    version_info = sys.version_info
    if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 8):
        print_error("Python 3.8+ required")
        return False
    
    print_success("Python version OK")
    return True

def install_pip_packages():
    """Install pip packages from requirements file"""
    print_header("Installing Python Packages")
    
    req_file = Path(__file__).parent / "requirements_mavproxy.txt"
    
    if not req_file.exists():
        print_error(f"requirements file not found: {req_file}")
        return False
    
    print_info(f"Requirements file: {req_file}")
    
    # Try pip install
    if run_command(f"pip install -r {req_file}", "Installing packages from requirements"):
        print_success("All packages installed")
        return True
    else:
        print_error("Failed to install packages")
        return False

def verify_installation():
    """Verify all packages are installed"""
    print_header("Verifying Installation")
    
    packages = {
        'pymavlink': 'PyMAVLink',
        'paho': 'Paho MQTT',
        'mavsdk': 'MAVSDK (optional)',
    }
    
    all_ok = True
    
    for pkg, name in packages.items():
        try:
            __import__(pkg)
            print_success(f"{name} installed")
        except ImportError:
            if pkg == 'mavsdk':
                print_warning(f"{name} not installed (optional for bridge)")
            else:
                print_error(f"{name} not installed")
                all_ok = False
    
    # Check mavproxy command
    if run_command("which mavproxy.py", ""):
        print_success("MAVProxy executable found")
    else:
        print_error("MAVProxy executable not found (may still work if installed in venv)")
        all_ok = False
    
    return all_ok

def print_next_steps():
    """Print next steps"""
    print_header("Setup Complete! ✨")
    
    print(f"""{GREEN}Next steps:{END}

1. {YELLOW}Start MAVProxy (Terminal 1):{END}
   mavproxy.py --master=udpin://0.0.0.0:14540 \\
       --out=127.0.0.1:14550 \\
       --out=udpserver:0.0.0.0:14551

2. {YELLOW}Start MAVLink Bridge (Terminal 2):{END}
   cd publisher
   python mavlink_bridge.py

3. {YELLOW}Connect Mission Planner (Terminal 3):{END}
   Open Mission Planner → CONNECT → TCP
   IP: 127.0.0.1, Port: 14550

4. {YELLOW}View Dashboard (Terminal 4):{END}
   cd dashboard
   python -m http.server 8000
   Open: http://localhost:8000

📖 See QUICKSTART.md for quick setup
📚 See SETUP_MAVPROXY.md for detailed documentation

""")

def main():
    print_header("🛰️  MAVLink Stack Setup 🛰️")
    
    print("This script will:")
    print("  • Verify Python version")
    print("  • Install required packages")
    print("  • Verify installation")
    print()
    
    # Check Python
    if not check_python_version():
        sys.exit(1)
    
    print()
    response = input("Continue? (y/n): ").strip().lower()
    if response != 'y':
        print("Setup cancelled")
        sys.exit(0)
    
    # Install packages
    if not install_pip_packages():
        sys.exit(1)
    
    # Verify
    if not verify_installation():
        print_warning("Some packages may not be installed, but setup might still work")
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            sys.exit(1)
    
    # Success
    print_next_steps()
    print_success("Setup complete! Ready to launch stack.")

if __name__ == "__main__":
    main()
