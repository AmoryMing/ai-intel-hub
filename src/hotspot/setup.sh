#!/bin/bash

# ======================================
# AI Hotspot Daily Report - Quick Setup
# ======================================

set -e  # Exit on error

echo "🔥 AI Hotspot Daily Report - Quick Setup"
echo "========================================"
echo ""

# Check Python version
echo "📌 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Found Python $PYTHON_VERSION"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "ℹ️  Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet
echo "✅ Pip upgraded"
echo ""

# Install dependencies
echo "📚 Installing dependencies..."
echo "   This may take a few minutes..."
pip install -r requirements.txt --quiet
echo "✅ Dependencies installed"
echo ""

# Create config from template
echo "⚙️  Setting up configuration..."
if [ ! -f "config/.env" ]; then
    cp config/.env.example config/.env
    echo "✅ Created config/.env from template"
    echo ""
    echo "⚠️  IMPORTANT: Please edit config/.env and add your API keys:"
    echo "   1. ANTHROPIC_API_KEY (get from console.anthropic.com)"
    echo "   2. MODELSCOPE_API_KEY (get from modelscope.cn)"
else
    echo "ℹ️  config/.env already exists"
fi
echo ""

# Create Obsidian directories
echo "📂 Creating output directories..."
DEFAULT_VAULT="$HOME/Documents/Obsidian Vault/AI-Hotspots/Daily"
mkdir -p "$DEFAULT_VAULT/images"
echo "✅ Created: $DEFAULT_VAULT"
echo ""

# Install Claude Code skill (optional)
echo "🤖 Installing Claude Code skill..."
SKILL_DIR="$HOME/.claude/skills/ai-hotspot-dailyreport"
if [ ! -d "$SKILL_DIR" ]; then
    mkdir -p "$SKILL_DIR"
    cp skill/SKILL.md "$SKILL_DIR/"
    echo "✅ Claude Code skill installed"
else
    echo "ℹ️  Claude Code skill already installed"
fi
echo ""

# Summary
echo "========================================"
echo "✅ Setup Complete!"
echo "========================================"
echo ""
echo "📝 Next Steps:"
echo "   1. Edit config/.env and add your API keys"
echo "   2. Run: source venv/bin/activate"
echo "   3. Run: python3 main.py --hours 24"
echo "   4. Run: python3 generate_enhanced_top10.py"
echo ""
echo "📖 Documentation:"
echo "   - README.md - Project overview"
echo "   - docs/INSTALLATION.md - Detailed setup"
echo "   - docs/USAGE.md - Usage guide"
echo ""
echo "🚀 Quick Start:"
echo "   source venv/bin/activate"
echo "   python3 main.py --hours 24"
echo ""
