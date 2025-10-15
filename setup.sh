#!/bin/bash

# Smart Code Review - Automated Setup Script
# This script sets up the entire project

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# ASCII Art Banner
echo "
╔═══════════════════════════════════════════════╗
║                                               ║
║     Smart Code Review Assistant Setup         ║
║     AI-Powered Code Analysis Tool             ║
║                                               ║
╚═══════════════════════════════════════════════╝
"

# Check prerequisites
print_status "Checking prerequisites..."

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION found"
else
    print_error "Python 3.9+ is required but not found"
    exit 1
fi

# Check pip
if command -v pip3 &> /dev/null; then
    print_success "pip3 found"
else
    print_error "pip3 is required but not found"
    exit 1
fi

# Check Node.js (optional for frontend)
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_success "Node.js $NODE_VERSION found"
    HAS_NODE=true
else
    print_warning "Node.js not found (optional for frontend development)"
    HAS_NODE=false
fi

# Check Docker (optional)
if command -v docker &> /dev/null; then
    print_success "Docker found"
    HAS_DOCKER=true
else
    print_warning "Docker not found (optional)"
    HAS_DOCKER=false
fi

# Step 1: Create virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
print_success "Virtual environment created"

# Step 2: Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Step 3: Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
print_success "pip upgraded"

# Step 4: Install Python dependencies
print_status "Installing Python dependencies (this may take a few minutes)..."
pip install -r requirements.txt > /dev/null 2>&1
print_success "Python dependencies installed"

# Step 5: Setup environment variables
print_status "Setting up environment variables..."
if [ ! -f .env ]; then
    cp .env.example .env
    print_success ".env file created"
    print_warning "Please edit .env file and add your API keys!"
    
    # Prompt for OpenAI API key
    echo ""
    read -p "Enter your OpenAI API key (or press Enter to skip): " api_key
    if [ ! -z "$api_key" ]; then
        sed -i "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$api_key/" .env
        print_success "OpenAI API key configured"
    fi
else
    print_warning ".env file already exists, skipping..."
fi

# Step 6: Initialize database
print_status "Initializing database..."
python database.py
print_success "Database initialized"

# Step 7: Run tests
print_status "Running tests..."
pytest test_api.py -v --tb=short > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_success "All tests passed!"
else
    print_warning "Some tests failed (may be due to missing API keys)"
fi

# Step 8: Setup frontend (if Node.js available)
if [ "$HAS_NODE" = true ]; then
    if [ -d "frontend" ]; then
        print_status "Setting up frontend..."
        cd frontend
        npm install > /dev/null 2>&1
        print_success "Frontend dependencies installed"
        cd ..
    fi
fi

# Step 9: Create necessary directories
print_status "Creating project directories..."
mkdir -p logs uploads temp docs/screenshots
print_success "Directories created"

# Step 10: Setup complete
echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║                                               ║"
echo "║            Setup Complete! 🎉                 ║"
echo "║                                               ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

print_success "Installation successful!"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file and add your API keys:"
echo "   ${BLUE}nano .env${NC}"
echo ""
echo "2. Start the backend server:"
echo "   ${BLUE}python main.py${NC}"
echo "   or"
echo "   ${BLUE}python manage.py run${NC}"
echo ""
echo "3. Access the application:"
echo "   ${GREEN}API:${NC}  http://localhost:8000"
echo "   ${GREEN}Docs:${NC} http://localhost:8000/docs"
echo ""

if [ "$HAS_NODE" = true ]; then
    echo "4. Start the frontend (optional):"
    echo "   ${BLUE}cd frontend && npm run dev${NC}"
    echo ""
fi

if [ "$HAS_DOCKER" = true ]; then
    echo "Alternative: Run with Docker:"
    echo "   ${BLUE}docker-compose up -d${NC}"
    echo ""
fi

echo "5. Try the CLI tool:"
echo "   ${BLUE}python cli.py review examples/sample_code.py${NC}"
echo ""
echo "6. Run the demo:"
echo "   ${BLUE}python demo.py${NC}"
echo ""
echo "For more information, see: ${BLUE}README.md${NC}"
echo ""

# Optional: Open browser
read -p "Open API documentation in browser? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8000/docs &
    elif command -v open &> /dev/null; then
        open http://localhost:8000/docs &
    fi
fi

# Deactivate virtual environment message
echo ""
print_warning "To activate the virtual environment in the future, run:"
echo "   ${BLUE}source venv/bin/activate${NC}"
echo ""
