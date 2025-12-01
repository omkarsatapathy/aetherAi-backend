# Quick Start Guide - AetherAI Multi-Agent System

## 🚀 Getting Started in 5 Minutes

### Step 1: Set Up Environment Variables

Create or update your `.env` file:

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional (uses defaults if not specified)
GEMINI_MODEL_ID=gemini-2.5-flash-exp

# For Gmail features (optional)
# Place credentials.json in credentials/gmail/

# For Google Search (optional)
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
```

### Step 2: Run Your First Query

```python
import asyncio
from src.agent import AgentRunner

async def main():
    runner = AgentRunner()
    response = await runner.run_query("What's in the news today?")
    print(response)

asyncio.run(main())
```

### Step 3: Try Interactive Mode

```bash
python -c "
import asyncio
from src.agent import AgentRunner

async def main():
    runner = AgentRunner()
    await runner.run_interactive_session()

asyncio.run(main())
"
```

## 📋 Example Queries

### Email Agent
```
- "Show me my recent emails"
- "Check my inbox for unread messages"
- "Get emails from the last 7 days"
```

### News Reader Agent
```
- "Give me today's top headlines"
- "What's the latest tech news?"
- "Provide a morning news brief"
```

### Maps Agent
```
- "Find nearby Italian restaurants"
- "Directions from Gachibowli to Hitech City"
- "What's the traffic like right now?"
```

### Researcher Agent
```
- "Research quantum computing developments"
- "Compare different cloud storage providers"
- "Analyze the electric vehicle market trends"
```

## 🧪 Testing

Run the test suite:

```bash
python test_agents.py
```

## 🏗️ Architecture

```
User Query
    ↓
CoordinatorAgent (decides which specialist to use)
    ↓
├── EmailAgent → Gmail Tools
├── NewsReaderAgent → Search + URL Tools
├── MapsAgent → Location Tools
└── ResearcherAgent → Search + URL Tools (formal analysis)
```

## 📁 File Structure

```
src/agent/
├── adk_agents.py              # Main entry point
├── coordinator_agent.py       # Parent agent
├── runner_setup.py            # Runner & session management
└── sub_agents/
    ├── email_agent.py
    ├── news_reader_agent.py
    ├── maps_agent.py
    └── researcher_agent.py
```

## 🔧 Common Use Cases

### Use Case 1: Morning Routine Assistant
```python
runner = AgentRunner()
session_id = await runner.create_session()

await runner.run_query("Show me unread emails", session_id=session_id)
await runner.run_query("Give me today's news brief", session_id=session_id)
await runner.run_query("What's the traffic like?", session_id=session_id)
```

### Use Case 2: Research Assistant
```python
runner = AgentRunner()
response = await runner.run_query(
    "Research the pros and cons of different AI frameworks"
)
```

### Use Case 3: Location Helper
```python
runner = AgentRunner()
response = await runner.run_query(
    "Find highly rated coffee shops near me and give me directions to the best one"
)
```

## 🎯 How Routing Works

The Coordinator Agent automatically routes your query:

| Query Contains | Routes To | Example |
|---------------|-----------|---------|
| email, inbox, gmail | EmailAgent | "show my emails" |
| news, headlines, brief | NewsReaderAgent | "today's news" |
| nearby, directions, traffic | MapsAgent | "find restaurants" |
| research, analyze, compare | ResearcherAgent | "research AI trends" |

## 💡 Pro Tips

1. **Persistent Sessions**: Use the same `session_id` to maintain context across queries
2. **News vs Research**:
   - News = Quick, conversational updates
   - Research = Deep, formal analysis with reports
3. **Location Context**: MapsAgent defaults to Hyderabad coordinates (can be customized)
4. **API Keys**: Only GEMINI_API_KEY is strictly required; other features need their respective keys

## 🐛 Troubleshooting

**"GEMINI_API_KEY not found"**
- Check your `.env` file exists in the project root
- Verify the key name is exactly `GEMINI_API_KEY`

**"Import error"**
- Ensure you're running from the project root directory
- Check Python path includes the `src` directory

**Agent not responding as expected**
- Check the agent routing logic in `coordinator_agent.py`
- Verify tools are properly imported in `build_adk_tools.py`

## 📚 Next Steps

1. Read the full [MULTI_AGENT_README.md](MULTI_AGENT_README.md) for detailed documentation
2. Explore individual agent files in `src/agent/sub_agents/`
3. Customize agent instructions for your use case
4. Add new tools or create custom agents

## 🤝 Need Help?

- Check the logs for detailed error messages
- Review agent instructions in each agent file
- Test individual agents using the test suite
- Verify all environment variables are set correctly
