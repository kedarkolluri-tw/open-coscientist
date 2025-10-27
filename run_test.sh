#!/bin/bash
set -e

cd /Users/kedarkolluri/projects/co-scientist/open-coscientist-agents

# Export API keys
export GOOGLE_API_KEY=$(grep GOOGLE_API_KEY .env | cut -d= -f2)
export PERPLEXITY_API_KEY=$(grep PERPLEXITY_API_KEY coscientist/researcher_config.json | cut -d'"' -f4)

echo "✅ Keys loaded"
echo "🚀 Starting test..."
echo ""

# Run test and save output
uv run python test_quick_integration.py 2>&1 | tee test_run.log

