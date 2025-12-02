#!/bin/bash

# Kill any process running on port 8000
lsof -ti :8000 | xargs kill -9 2>/dev/null || true

# Launch the uvicorn app
/opt/homebrew/Caskroom/miniconda/base/envs/ai_env/bin/python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
