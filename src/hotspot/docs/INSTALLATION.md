# Installation Guide

This guide will help you set up the AI Hotspot Daily Report skill for Claude Code.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Step 1: Install the Skill](#step-1-install-the-skill)
- [Step 2: Set Up the Collector Project](#step-2-set-up-the-collector-project)
- [Step 3: Configure API Keys](#step-3-configure-api-keys)
- [Step 4: Configure Obsidian Vault](#step-4-configure-obsidian-vault)
- [Step 5: Verify Installation](#step-5-verify-installation)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Claude Code CLI**: Install from [claude.ai/claude-code](https://claude.ai/claude-code)
- **Python 3.8+**: Check with `python3 --version`
- **Git**: For cloning repositories
- **Obsidian** (recommended): For viewing reports

### Required API Keys

1. **Anthropic API Key**
   - Sign up at [console.anthropic.com](https://console.anthropic.com)
   - Navigate to API Keys section
   - Create a new key
   - Cost: ~$0.01-0.05 per report (depending on data volume)

2. **ModelScope API Key**
   - Register at [modelscope.cn](https://modelscope.cn)
   - Go to Profile → API Tokens
   - Generate a new token
   - Cost: Free tier available, ~¥0.01-0.05 per image

### System Requirements

- **Disk Space**: ~500MB for dependencies + data
- **Memory**: 2GB+ RAM recommended
- **Network**: Stable internet connection for API calls

---

## Step 1: Install the Skill

### Option A: Install from GitHub Release (Recommended)

```bash
# Download the latest release
curl -L https://github.com/yourusername/ai-hotspot-dailyreport-skill/archive/refs/heads/main.zip -o skill.zip

# Extract and install
unzip skill.zip
mkdir -p ~/.claude/skills/ai-hotspot-dailyreport
cp ai-hotspot-dailyreport-skill-main/skill/SKILL.md ~/.claude/skills/ai-hotspot-dailyreport/

# Verify installation
ls ~/.claude/skills/ai-hotspot-dailyreport/SKILL.md
```

### Option B: Clone Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-hotspot-dailyreport-skill.git

# Install the skill
mkdir -p ~/.claude/skills/ai-hotspot-dailyreport
cp ai-hotspot-dailyreport-skill/skill/SKILL.md ~/.claude/skills/ai-hotspot-dailyreport/

# Verify installation
ls ~/.claude/skills/ai-hotspot-dailyreport/SKILL.md
```

### Option C: Manual Copy

1. Download `skill/SKILL.md` from this repository
2. Create directory: `mkdir -p ~/.claude/skills/ai-hotspot-dailyreport`
3. Copy file: `cp SKILL.md ~/.claude/skills/ai-hotspot-dailyreport/`

---

## Step 2: Set Up the Collector Project

### Clone the AI Hotspot Collector

```bash
# Choose your installation directory
cd ~/Projects  # Or any directory you prefer

# Clone the collector project
git clone https://github.com/yourusername/ai-hotspot-collector.git
cd ai-hotspot-collector
```

### Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Verify activation (should show (venv) in prompt)
which python3  # Should point to venv/bin/python3
```

### Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install required packages
pip install -r requirements.txt

# Verify installation
pip list | grep -E "anthropic|requests|pyyaml"
```

**Expected packages**:
- `anthropic` - For Claude AI analysis
- `requests` - For API calls
- `pyyaml` - For configuration
- `feedparser` - For RSS feeds
- And others...

---

## Step 3: Configure API Keys

### Create Environment File

```bash
cd ai-hotspot-collector/config

# Create .env file from template
cp .env.example .env  # If template exists
# OR create new file
nano .env
```

### Add Your API Keys

Edit `.env` file:

```bash
# Anthropic API Key (Required for AI analysis)
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# ModelScope API Key (Required for image generation)
MODELSCOPE_API_KEY=your-modelscope-token-here

# Optional: Obsidian Vault Path (will auto-detect if not set)
OBSIDIAN_VAULT_PATH=/Users/yourusername/Documents/Obsidian Vault/AI-Hotspots/Daily/
```

### Secure Your Keys

```bash
# Set proper permissions (macOS/Linux)
chmod 600 config/.env

# Add to .gitignore to prevent accidental commits
echo "config/.env" >> .gitignore
```

---

## Step 4: Configure Obsidian Vault

### Option A: Auto-Detection (Recommended)

The collector will automatically find your Obsidian vault if:
- Obsidian is installed
- You have a vault named "AI-Hotspots" or similar

No manual configuration needed!

### Option B: Manual Configuration

Edit `config/config.yaml`:

```yaml
# Obsidian Export Configuration
obsidian:
  enabled: true
  vault_path: "/Users/yourusername/Documents/Obsidian Vault"
  daily_notes_path: "AI-Hotspots/Daily"

  # Create folders if they don't exist
  auto_create_folders: true
```

### Create Directory Structure (if needed)

```bash
# Create Obsidian directories
mkdir -p "/Users/yourusername/Documents/Obsidian Vault/AI-Hotspots/Daily/images"
```

---

## Step 5: Verify Installation

### Test 1: Skill Recognition

In Claude Code, ask:
```
List all available skills
```

You should see `ai-hotspot-dailyreport` in the list.

### Test 2: Python Environment

```bash
cd ai-hotspot-collector
source venv/bin/activate

# Test imports
python3 -c "import anthropic; import requests; print('✅ All imports successful')"
```

### Test 3: API Keys

```bash
# Test Anthropic API (optional)
python3 -c "
import os
from anthropic import Anthropic
client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
print('✅ Anthropic API key valid')
"
```

### Test 4: Run Small Test

```bash
# Collect data for just 1 hour (quick test)
source venv/bin/activate
python3 main.py --hours 1 --no-ai-analysis

# Check output
ls -lh "/Users/yourusername/Documents/Obsidian Vault/AI-Hotspots/Daily/" | tail -5
```

Expected output: A markdown file with collected items.

---

## Troubleshooting

### Issue 1: Skill Not Found

**Problem**: Claude Code doesn't recognize the skill

**Solution**:
```bash
# Verify file location
ls -la ~/.claude/skills/ai-hotspot-dailyreport/SKILL.md

# Check file format (should be plain text)
file ~/.claude/skills/ai-hotspot-dailyreport/SKILL.md

# Restart Claude Code
# Then try again
```

### Issue 2: ModuleNotFoundError

**Problem**: `ModuleNotFoundError: No module named 'anthropic'`

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep anthropic
```

### Issue 3: API Key Invalid

**Problem**: `AuthenticationError: Invalid API key`

**Solution**:
```bash
# Check .env file exists
ls config/.env

# Verify key format
cat config/.env | grep API_KEY

# Test key manually
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: YOUR_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'
```

### Issue 4: Permission Denied (Obsidian)

**Problem**: Cannot write to Obsidian vault directory

**Solution**:
```bash
# Check directory permissions
ls -ld "/Users/yourusername/Documents/Obsidian Vault"

# Fix permissions if needed
chmod -R u+w "/Users/yourusername/Documents/Obsidian Vault/AI-Hotspots"

# Or change output directory in config.yaml
```

### Issue 5: Virtual Environment Issues

**Problem**: `command not found: python3` or wrong Python version

**Solution**:
```bash
# Check Python installation
which python3
python3 --version

# If not found, install Python 3.8+
# macOS: brew install python@3.11
# Ubuntu: sudo apt install python3.11

# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Issue 6: Network/Firewall Issues

**Problem**: Cannot connect to APIs

**Solution**:
```bash
# Test connectivity
ping api.anthropic.com
ping modelscope.cn

# Check proxy settings if behind corporate firewall
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Or add to config.yaml:
# proxy:
#   http: "http://proxy:8080"
#   https: "http://proxy:8080"
```

---

## Next Steps

Once installation is complete:

1. ✅ Read [USAGE.md](USAGE.md) for usage instructions
2. ✅ Try generating your first report
3. ✅ Customize configuration if needed
4. ✅ Set up a daily cron job (optional)

---

## Getting Help

If you encounter issues not covered here:

1. Check [GitHub Issues](https://github.com/yourusername/ai-hotspot-dailyreport-skill/issues)
2. Review [TDD-COMPLETION-REPORT.md](TDD-COMPLETION-REPORT.md) for troubleshooting tips
3. Open a new issue with:
   - Your OS and Python version
   - Error messages (full output)
   - Steps to reproduce
   - What you've already tried

---

**Installation complete! Ready to generate your first AI hotspot report.** 🎉
