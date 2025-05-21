#!/bin/bash
# Script to start the Multi-Agent Lead Processing System

# Go to the project directory
cd "$(dirname "$0")" || exit

# Define colors for better visibility
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Display banner
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║             MULTI-AGENT LEAD PROCESSING SYSTEM               ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create a .env file with the required credentials."
    exit 1
fi

# Parse command line arguments
DOCKER_MODE=false
RESET_DB=false
API_ONLY=false
API_PORT=8000
VOICE_BATCH=5
ENTRY_BATCH=3

while [[ $# -gt 0 ]]; do
    case $1 in
        --docker)
            DOCKER_MODE=true
            shift
            ;;
        --reset-db)
            RESET_DB=true
            shift
            ;;
        --api-only)
            API_ONLY=true
            shift
            ;;
        --api-port)
            API_PORT="$2"
            shift 2
            ;;
        --voice-batch)
            VOICE_BATCH="$2"
            shift 2
            ;;
        --entry-batch)
            ENTRY_BATCH="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown parameter: $1${NC}"
            exit 1
            ;;
    esac
done

# Start the system
if [ "$DOCKER_MODE" = true ]; then
    echo -e "${YELLOW}Starting in Docker mode...${NC}"
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker not found!${NC}"
        echo "Please install Docker to use this mode."
        exit 1
    fi
    
    echo "Building and starting containers..."
    docker-compose up -d
    
    echo -e "${GREEN}System started in Docker mode. API available at http://localhost:$API_PORT${NC}"
    echo "Use 'docker-compose logs -f' to view logs."
else
    echo -e "${YELLOW}Starting in local mode...${NC}"
    
    # Check if Python is installed
    if ! command -v python &> /dev/null; then
        echo -e "${RED}Error: Python not found!${NC}"
        echo "Please install Python 3.9 or higher."
        exit 1
    fi
    
    # Check if virtualenv exists, if not create it
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python -m venv venv
    fi
    
    # Activate virtual environment
    echo "Activating virtual environment..."
    source venv/bin/activate || source venv/Scripts/activate
    
    # Install dependencies if not already installed
    if [ ! -f "venv/.deps_installed" ]; then
        echo "Installing dependencies..."
        pip install -r requirements.txt
        playwright install
        touch venv/.deps_installed
    fi
    
    # Build command with arguments
    CMD="python run.py --api --api-port $API_PORT --voice-batch $VOICE_BATCH --entry-batch $ENTRY_BATCH"
    
    if [ "$RESET_DB" = true ]; then
        CMD="$CMD --reset-db"
    fi
    
    if [ "$API_ONLY" = true ]; then
        CMD="$CMD --api-only"
    fi
    
    echo "Running command: $CMD"
    eval "$CMD"
fi 