# AetherAI Multi-Agent System

A sophisticated multi-agent system built with Google's Agent Development Kit (ADK), featuring specialized agents coordinated by a parent agent for intelligent task routing and execution.

## Architecture Overview

```
CoordinatorAgent (Parent)
├── EmailAgent - Gmail reading and management
├── NewsReaderAgent - News briefs and storytelling
├── MapsAgent - Location, navigation, and places
└── ResearcherAgent - Deep research and formal analysis
```

## Components

### 1. Coordinator Agent (`coordinator_agent.py`)

The parent agent that manages all sub-agents and routes user requests to the appropriate specialist using LLM-driven delegation.

**Capabilities:**
- Intelligent routing based on user intent
- Context-aware agent selection
- Seamless delegation using `transfer_to_agent()`
- Handles general conversation when no specialist is needed

### 2. Email Agent (`sub_agents/email_agent.py`)

Specializes in email-related tasks using Gmail integration.

**Tools:**
- `gmail_messages_tool` - Fetch and read Gmail messages
- `gmail_auth_tool` - Check authentication status
- `datetime_ist_tool` - Provide temporal context

**Use Cases:**
- "Show me my recent emails"
- "Check my inbox for unread messages"
- "Get emails from the last week"

### 3. News Reader Agent (`sub_agents/news_reader_agent.py`)

Delivers news in an engaging, storytelling format for quick updates and morning briefs.

**Tools:**
- `google_search_tool` - Search for news articles
- `fetch_url_content_tool` - Fetch article details
- `fetch_multiple_urls_tool` - Gather multiple sources
- `datetime_ist_tool` - Time-relevant context

**Use Cases:**
- "Give me today's top headlines"
- "What's the latest tech news?"
- "Provide a morning news brief"

**Style:** Conversational, engaging, storytelling approach

### 4. Maps Agent (`sub_agents/maps_agent.py`)

Handles all location-based queries including navigation, places, and traffic.

**Tools:**
- `search_nearby_places_tool` - Find restaurants, shops, services
- `get_directions_tool` - Route planning
- `get_traffic_info_tool` - Real-time traffic conditions
- `get_place_details_tool` - Business hours, ratings, reviews
- `explore_area_tool` - Area exploration and recommendations
- `datetime_ist_tool` - Time-based recommendations

**Use Cases:**
- "Find nearby Italian restaurants"
- "Directions to Hitech City"
- "What's the traffic like right now?"

### 5. Researcher Agent (`sub_agents/researcher_agent.py`)

Conducts thorough, multi-source research and generates formal analysis reports.

**Tools:**
- `google_search_tool` - Multi-query research
- `fetch_url_content_tool` - Deep content analysis
- `fetch_multiple_urls_tool` - Cross-reference sources
- `datetime_ist_tool` - Information currency

**Use Cases:**
- "Research quantum computing developments"
- "Compare cloud storage providers"
- "Analyze the EV market trends"

**Style:** Formal, academic, evidence-based with structured reports

**Output Format:**
- Executive Summary
- Introduction
- Methodology
- Findings (with tables/comparisons)
- Analysis
- Recommendations
- Conclusion
- Sources

## File Structure

```
src/
├── agent/
│   ├── __init__.py                 # Package exports
│   ├── adk_agents.py              # Main module with documentation
│   ├── coordinator_agent.py       # Parent coordinator agent
│   ├── runner_setup.py            # Runner and session management
│   └── sub_agents/
│       ├── __init__.py
│       ├── email_agent.py
│       ├── news_reader_agent.py
│       ├── maps_agent.py
│       └── researcher_agent.py
└── tools/
    └── tools_factory/
        ├── __init__.py
        └── build_adk_tools.py     # FunctionTool wrappers

test_agents.py                     # Test suite
```

## Usage

### Basic Usage

```python
import asyncio
from src.agent import AgentRunner

async def main():
    runner = AgentRunner()

    # Single query
    response = await runner.run_query("Show me my recent emails")
    print(response)

asyncio.run(main())
```

### Interactive Session

```python
import asyncio
from src.agent import AgentRunner

async def main():
    runner = AgentRunner()
    await runner.run_interactive_session()

asyncio.run(main())
```

### Convenience Function

```python
import asyncio
from src.agent import run_single_query

async def main():
    response = await run_single_query("Give me today's news")
    print(response)

asyncio.run(main())
```

### Session Management

```python
import asyncio
from src.agent import AgentRunner

async def main():
    runner = AgentRunner()

    # Create a persistent session
    session_id = await runner.create_session(
        user_id="user_123",
        initial_state={"preferences": "tech news"}
    )

    # Use the same session for multiple queries
    await runner.run_query("Get my emails", session_id=session_id)
    await runner.run_query("What's the latest tech news?", session_id=session_id)

asyncio.run(main())
```

## Running the Agent System

### Method 1: Direct Python Execution

```bash
# Run the main runner script
python src/agent/runner_setup.py

# Run the test suite
python test_agents.py
```

### Method 2: Interactive Mode

```python
# In Python
import asyncio
from src.agent import AgentRunner

async def main():
    runner = AgentRunner()
    await runner.run_interactive_session()

asyncio.run(main())
```

## Configuration

Required environment variables in `.env`:

```bash
# Gemini API Key (required)
GEMINI_API_KEY=your_api_key_here

# Model configuration (optional)
GEMINI_MODEL_ID=gemini-2.5-flash-exp

# Gmail OAuth credentials (for EmailAgent)
# Place credentials.json in credentials/gmail/

# Google Search API (for news and research)
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
```

## Agent Routing Logic

The Coordinator Agent uses the following routing rules:

1. **Email Requests** → EmailAgent
   - Keywords: inbox, emails, messages, unread, Gmail
   - Examples: "show my emails", "check inbox"

2. **News Requests** → NewsReaderAgent
   - Keywords: news, headlines, brief, current events
   - Style: Quick updates, storytelling
   - Examples: "today's news", "morning brief"

3. **Location Requests** → MapsAgent
   - Keywords: nearby, directions, traffic, restaurant, navigation
   - Examples: "find restaurants", "traffic update"

4. **Research Requests** → ResearcherAgent
   - Keywords: research, analyze, compare, investigate
   - Style: Formal, in-depth analysis
   - Examples: "research quantum computing", "analyze market"

5. **General Chat** → Handled by Coordinator
   - Greetings, capability questions, general conversation

## Testing

Run the test suite:

```bash
python test_agents.py
```

Test individual agents by uncommenting specific tests in `test_agents.py`:

```python
# Individual agent tests
await test_email_agent()
await test_news_reader_agent()
await test_maps_agent()
await test_researcher_agent()

# Coordinator routing test
await test_coordinator_routing()

# Interactive mode
await interactive_mode()
```

## Advanced Features

### State Persistence

Agents can access and modify session state:

```python
# State is automatically managed by the session service
# Each agent can read/write to shared state through their tools
```

### Custom Agent Creation

Create individual agents for specific use cases:

```python
from src.agent import create_email_agent, create_researcher_agent

# Create specific agents
email_agent = create_email_agent()
researcher = create_researcher_agent()
```

### Adding New Sub-Agents

1. Create a new agent file in `src/agent/sub_agents/`
2. Define a `create_*_agent()` function
3. Add relevant tools from `tools_factory`
4. Update `coordinator_agent.py` to include the new sub-agent
5. Update routing logic in the coordinator's instructions

## Differences: News Reader vs Researcher

| Feature | News Reader Agent | Researcher Agent |
|---------|------------------|------------------|
| **Purpose** | Quick news updates | Deep analysis |
| **Tone** | Conversational, engaging | Formal, academic |
| **Format** | Storytelling, brief | Structured reports |
| **Depth** | Surface-level, headlines | Multi-source investigation |
| **Output** | Narrative summary | Executive summary, tables, recommendations |
| **Use Case** | Daily briefings, current events | Market analysis, comparisons, research |

## API Reference

### AgentRunner

```python
class AgentRunner:
    def __init__(self, app_name: str = "AetherAI_MultiAgent_System")
    async def create_session(user_id: str, session_id: str = None, initial_state: dict = None) -> str
    async def run_query(query: str, user_id: str, session_id: str = None) -> str
    async def run_interactive_session(user_id: str, session_id: str = None)
```

### Convenience Functions

```python
async def run_single_query(query: str) -> str
```

## Troubleshooting

### Common Issues

1. **API Key Error**
   - Ensure `GEMINI_API_KEY` is set in `.env`
   - Verify the key is valid

2. **Import Errors**
   - Check that all dependencies are installed
   - Verify the file structure matches the documentation

3. **Gmail Authentication**
   - Place `credentials.json` in `credentials/gmail/`
   - Run the OAuth flow to generate token

4. **Agent Not Routing Correctly**
   - Check the coordinator's routing instructions
   - Verify agent descriptions are clear

## Dependencies

```
google-adk
google-generativeai
python-dotenv
requests
beautifulsoup4
llama-index
google-auth-oauthlib
googleapiclient
```

## Future Enhancements

- [ ] Add image analysis agent
- [ ] Implement document RAG agent
- [ ] Add voice interaction capabilities
- [ ] Implement agent performance metrics
- [ ] Add caching for improved response times
- [ ] Create web interface for interaction

## License

[Your License Here]

## Contributing

[Contributing Guidelines Here]
