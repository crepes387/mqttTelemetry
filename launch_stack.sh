#!/bin/bash

# ============================================================================
# MAVLink + Mission Planner + MQTT Launcher
# Usage: ./launch_stack.sh
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PUBLISHER_DIR="${SCRIPT_DIR}/publisher"
DASHBOARD_DIR="${SCRIPT_DIR}/dashboard"

# Configuration defaults
PIXHAWK_CONNECTION="${PIXHAWK_CONNECTION:-udpin://0.0.0.0:14540}"
MAVPROXY_OUT_MP="${MAVPROXY_OUT_MP:-127.0.0.1:14550}"
MAVPROXY_OUT_APP="${MAVPROXY_OUT_APP:-udpserver:0.0.0.0:14551}"

# MQTT Configuration
export MQTT_BROKER="${MQTT_BROKER:-ef6ff411.ala.asia-southeast1.emqxsl.com}"
export MQTT_PORT="${MQTT_PORT:-8883}"
export MQTT_USERNAME="${MQTT_USERNAME:-user1}"
export MQTT_PASSWORD="${MQTT_PASSWORD:-public1}"
export MQTT_TOPIC="${MQTT_TOPIC:-uav/telemetry/crepes387}"
export PUBLISH_INTERVAL="${PUBLISH_INTERVAL:-1.0}"
export MAVLINK_LISTEN_PORT="${MAVLINK_LISTEN_PORT:-14551}"

# ============================================================================
# FUNCTIONS
# ============================================================================

print_banner() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║        🛰️  MAVLink + Mission Planner + MQTT Stack 🛰️          ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 not found. Please install it."
        return 1
    fi
}

check_python_module() {
    if ! python -c "import $1" 2>/dev/null; then
        print_error "Python module '$1' not installed"
        return 1
    fi
}

# ============================================================================
# CHECKS
# ============================================================================

check_dependencies() {
    print_section "Checking dependencies..."
    
    local all_ok=true
    
    if ! check_command "python"; then all_ok=false; fi
    if ! check_command "mavproxy.py"; then
        print_warning "MAVProxy not installed. Install with: pip install MAVProxy"
        all_ok=false
    fi
    
    if ! check_python_module "pymavlink"; then
        print_warning "pymavlink not installed. Install with: pip install pymavlink"
        all_ok=false
    fi
    
    if ! check_python_module "paho"; then
        print_warning "paho-mqtt not installed. Install with: pip install paho-mqtt"
        all_ok=false
    fi
    
    if [ "$all_ok" = false ]; then
        print_error "Some dependencies are missing"
        return 1
    fi
    
    print_success "All dependencies found"
    return 0
}

check_directories() {
    print_section "Checking directories..."
    
    if [ ! -d "$PUBLISHER_DIR" ]; then
        print_error "Publisher directory not found: $PUBLISHER_DIR"
        return 1
    fi
    
    if [ ! -d "$DASHBOARD_DIR" ]; then
        print_error "Dashboard directory not found: $DASHBOARD_DIR"
        return 1
    fi
    
    print_success "Directories OK"
    return 0
}

# ============================================================================
# SETUP
# ============================================================================

setup_environment() {
    print_section "Setting up environment..."
    
    # Create data directory if not exists
    mkdir -p "${SCRIPT_DIR}/data"
    
    # Create virtual environment if not exists (optional)
    # if [ ! -d "$PUBLISHER_DIR/publishenv" ]; then
    #     print_section "Creating virtual environment..."
    #     python -m venv "$PUBLISHER_DIR/publishenv"
    #     source "$PUBLISHER_DIR/publishenv/bin/activate"
    #     pip install MAVProxy pymavlink paho-mqtt
    # fi
    
    print_success "Environment ready"
}

print_startup_info() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                  🚀 STARTUP CONFIGURATION 🚀                  ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "Pixhawk Connection: ${GREEN}${PIXHAWK_CONNECTION}${NC}"
    echo -e "MAVProxy→MP Output:  ${GREEN}${MAVPROXY_OUT_MP}${NC}"
    echo -e "MAVProxy→App Output: ${GREEN}${MAVPROXY_OUT_APP}${NC}"
    echo ""
    echo -e "MQTT Broker: ${GREEN}${MQTT_BROKER}:${MQTT_PORT}${NC}"
    echo -e "MQTT User:   ${GREEN}${MQTT_USERNAME}${NC}"
    echo -e "MQTT Topic:  ${GREEN}${MQTT_TOPIC}${NC}"
    echo ""
    echo -e "Bridge Listen Port: ${GREEN}${MAVLINK_LISTEN_PORT}${NC}"
    echo -e "Publish Interval:   ${GREEN}${PUBLISH_INTERVAL}s${NC}"
    echo ""
}

print_next_steps() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                      📋 NEXT STEPS 📋                         ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}1. Terminal 1 - MAVProxy will start in this window${NC}"
    echo "   (Press Ctrl+C to stop)"
    echo ""
    echo -e "${YELLOW}2. Terminal 2 - Open new terminal and run:${NC}"
    echo "   cd $PUBLISHER_DIR"
    echo "   python mavlink_bridge.py"
    echo ""
    echo -e "${YELLOW}3. Terminal 3 - Mission Planner (Windows GUI)${NC}"
    echo "   Open Mission Planner"
    echo "   Click CONNECT → TCP/UDP"
    echo "   IP: 127.0.0.1 (or remote IP)"
    echo "   Port: 14550"
    echo ""
    echo -e "${YELLOW}4. Terminal 4 (optional) - Dashboard${NC}"
    echo "   cd $DASHBOARD_DIR"
    echo "   python -m http.server 8000"
    echo "   Visit: http://localhost:8000"
    echo ""
    echo -e "${GREEN}ℹ️  Check logs for any errors. Common issues: port already in use, Pixhawk not connected${NC}"
    echo ""
}

# ============================================================================
# MAIN LAUNCHER
# ============================================================================

main() {
    print_banner
    
    # Run checks
    if ! check_dependencies; then
        print_error "Please install missing dependencies first"
        exit 1
    fi
    
    if ! check_directories; then
        print_error "Directory structure error"
        exit 1
    fi
    
    # Setup
    setup_environment
    
    # Show info
    print_startup_info
    
    # Confirm before starting
    echo -e "${YELLOW}Ready to launch MAVProxy. Continue? (y/n)${NC}"
    read -r -n 1 response
    echo ""
    
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        print_warning "Launch cancelled"
        exit 0
    fi
    
    # Start MAVProxy
    echo ""
    print_section "Starting MAVProxy..."
    echo ""
    
    mavproxy.py --master="$PIXHAWK_CONNECTION" \
                --out="$MAVPROXY_OUT_MP" \
                --out="$MAVPROXY_OUT_APP" \
                --default-modules=compass,streamrate \
                --show-errors
}

# ============================================================================
# RUN
# ============================================================================

main "$@"
