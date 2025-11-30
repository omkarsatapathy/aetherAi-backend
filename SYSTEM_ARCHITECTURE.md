# System Architecture Diagram

## 🏗️ Multi-Agent System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE                                │
│                     (API / CLI / Interactive Mode)                      │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          AgentRunner                                    │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  • Session Management (InMemorySessionService)                   │  │
│  │  • Query Processing                                              │  │
│  │  • Async Event Handling                                          │  │
│  │  • Response Streaming                                            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      COORDINATOR AGENT (Parent)                         │
│                      gemini-2.0-flash-exp                              │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Role: Intelligent Router & Task Coordinator                     │  │
│  │  • Analyzes user intent                                          │  │
│  │  • Routes to appropriate specialist                              │  │
│  │  • Uses transfer_to_agent() for delegation                       │  │
│  │  • Handles general conversation                                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───┬────────────────┬─────────────────┬─────────────────┬───────────────┘
    │                │                 │                 │
    ▼                ▼                 ▼                 ▼
┌───────────┐  ┌───────────┐    ┌──────────┐    ┌────────────────┐
│  EMAIL    │  │   NEWS    │    │   MAPS   │    │   RESEARCHER   │
│  AGENT    │  │  READER   │    │  AGENT   │    │     AGENT      │
│           │  │  AGENT    │    │          │    │                │
└───────────┘  └───────────┘    └──────────┘    └────────────────┘
```

---

## 📊 Agent Details

### 1️⃣ Email Agent
```
┌─────────────────────────────────────────┐
│         EMAIL AGENT                     │
│  gemini-2.0-flash-exp                  │
├─────────────────────────────────────────┤
│ SPECIALIZATION:                         │
│  • Gmail reading & management           │
│  • Email authentication                 │
│  • Message filtering & organization     │
├─────────────────────────────────────────┤
│ TOOLS (3):                              │
│  🔧 gmail_messages_tool                 │
│     - Fetch emails with filters         │
│     - Support for queries, date ranges  │
│  🔧 gmail_auth_tool                     │
│     - Check authentication status       │
│  🔧 datetime_ist_tool                   │
│     - Temporal context                  │
├─────────────────────────────────────────┤
│ TRIGGERS:                               │
│  • "show my emails"                     │
│  • "check inbox"                        │
│  • "unread messages"                    │
│  • "emails from..."                     │
└─────────────────────────────────────────┘
```

### 2️⃣ News Reader Agent
```
┌─────────────────────────────────────────┐
│       NEWS READER AGENT                 │
│  gemini-2.0-flash-exp                  │
├─────────────────────────────────────────┤
│ SPECIALIZATION:                         │
│  • News briefs & headlines              │
│  • Engaging storytelling format         │
│  • Morning briefings                    │
│  • Quick current events updates         │
├─────────────────────────────────────────┤
│ TOOLS (4):                              │
│  🔧 google_search_tool                  │
│     - Search for news articles          │
│  🔧 fetch_url_content_tool              │
│     - Get article details               │
│  🔧 fetch_multiple_urls_tool            │
│     - Multi-source gathering            │
│  🔧 datetime_ist_tool                   │
│     - Time-relevant context             │
├─────────────────────────────────────────┤
│ STYLE:                                  │
│  • Conversational & engaging            │
│  • Storytelling approach                │
│  • Quick & accessible                   │
├─────────────────────────────────────────┤
│ TRIGGERS:                               │
│  • "today's news"                       │
│  • "headlines"                          │
│  • "morning brief"                      │
│  • "current events"                     │
└─────────────────────────────────────────┘
```

### 3️⃣ Maps Agent
```
┌─────────────────────────────────────────┐
│          MAPS AGENT                     │
│  gemini-2.0-flash-exp                  │
├─────────────────────────────────────────┤
│ SPECIALIZATION:                         │
│  • Location services                    │
│  • Navigation & directions              │
│  • Place discovery                      │
│  • Traffic information                  │
├─────────────────────────────────────────┤
│ TOOLS (6):                              │
│  🔧 search_nearby_places_tool           │
│     - Find restaurants, businesses      │
│  🔧 get_directions_tool                 │
│     - Routes & travel info              │
│  🔧 get_traffic_info_tool               │
│     - Real-time traffic                 │
│  🔧 get_place_details_tool              │
│     - Hours, ratings, reviews           │
│  🔧 explore_area_tool                   │
│     - Area recommendations              │
│  🔧 datetime_ist_tool                   │
│     - Time-based suggestions            │
├─────────────────────────────────────────┤
│ FEATURES:                               │
│  • Google Maps grounding                │
│  • Widget token generation              │
│  • Distance & ETA calculations          │
│  • Rating & review integration          │
├─────────────────────────────────────────┤
│ TRIGGERS:                               │
│  • "nearby restaurants"                 │
│  • "directions to..."                   │
│  • "traffic update"                     │
│  • "find coffee shops"                  │
└─────────────────────────────────────────┘
```

### 4️⃣ Researcher Agent
```
┌─────────────────────────────────────────┐
│       RESEARCHER AGENT                  │
│  gemini-2.0-flash-exp                  │
├─────────────────────────────────────────┤
│ SPECIALIZATION:                         │
│  • Deep multi-source research           │
│  • Formal analysis & reports            │
│  • Evidence-based recommendations       │
│  • Comparative studies                  │
├─────────────────────────────────────────┤
│ TOOLS (4):                              │
│  🔧 google_search_tool                  │
│     - Multi-query research              │
│  🔧 fetch_url_content_tool              │
│     - Deep content analysis             │
│  🔧 fetch_multiple_urls_tool            │
│     - Cross-reference sources           │
│  🔧 datetime_ist_tool                   │
│     - Information currency              │
├─────────────────────────────────────────┤
│ OUTPUT FORMAT:                          │
│  1. Executive Summary                   │
│  2. Introduction                        │
│  3. Methodology                         │
│  4. Findings                            │
│  5. Analysis                            │
│  6. Recommendations (w/ pros/cons)      │
│  7. Conclusion                          │
│  8. Sources                             │
├─────────────────────────────────────────┤
│ STYLE:                                  │
│  • Formal & academic                    │
│  • Evidence-based                       │
│  • Structured with tables               │
│  • Third-person perspective             │
├─────────────────────────────────────────┤
│ TRIGGERS:                               │
│  • "research..."                        │
│  • "analyze..."                         │
│  • "compare..."                         │
│  • "deep dive on..."                    │
└─────────────────────────────────────────┘
```

---

## 🔄 Request Flow

```
1. USER QUERY
   ↓
   "Give me today's news"
   ↓

2. AGENT RUNNER
   ↓
   • Creates/retrieves session
   • Formats message
   • Calls coordinator.run_async()
   ↓

3. COORDINATOR AGENT
   ↓
   • Analyzes: "news" keyword detected
   • Decision: Route to NewsReaderAgent
   • Action: transfer_to_agent(NewsReaderAgent)
   ↓

4. NEWS READER AGENT
   ↓
   • Step 1: get_current_datetime_ist() → "2025-11-30"
   • Step 2: google_search_tool("today's top news")
   • Step 3: fetch_url_content_tool(top_result)
   • Step 4: Synthesize into story format
   ↓

5. AGENT RUNNER
   ↓
   • Receives final_response event
   • Returns formatted response
   ↓

6. USER
   ↓
   Receives engaging news summary
```

---

## 🛠️ Tool Architecture

```
┌────────────────────────────────────────────────────────────┐
│              TOOLS FACTORY LAYER                           │
│         (src/tools/tools_factory/)                         │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  build_adk_tools.py                                        │
│  ├─ Import: Raw tool functions                            │
│  ├─ Wrap: FunctionTool(func=tool_function)                │
│  └─ Export: ADK-compatible tools                          │
│                                                            │
└────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│              TOOL IMPLEMENTATIONS                          │
│              (src/tools/*.py)                              │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ✓ gmail.py                 (2 tools)                      │
│  ✓ google_search.py         (1 tool)                      │
│  ✓ image_analysis.py        (1 tool)                      │
│  ✓ google_maps.py           (5 tools)                     │
│  ✓ document_rag.py          (1 tool)                      │
│  ✓ link_executor.py         (2 tools)                     │
│  ✓ datetime_ist.py          (1 tool)                      │
│                                                            │
│  Total: 13 ADK-wrapped tools                              │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 📊 Session Management

```
┌─────────────────────────────────────────────────────────┐
│          InMemorySessionService                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Session Structure:                                     │
│  {                                                      │
│    "app_name": "AetherAI_MultiAgent_System",           │
│    "user_id": "user_001",                              │
│    "session_id": "session_abc123",                     │
│    "state": {                                          │
│      "preferences": {...},                             │
│      "context": {...},                                 │
│      "history": [...]                                  │
│    }                                                   │
│  }                                                     │
│                                                         │
│  Features:                                             │
│  • Persistent context across queries                   │
│  • State sharing between agents                        │
│  • Conversation history                                │
│  • User preferences storage                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Routing Logic

```
┌──────────────────────────────────────────────────────────┐
│         COORDINATOR ROUTING DECISION TREE                │
└──────────────────────────────────────────────────────────┘

User Query
    │
    ├─ Contains: email, inbox, gmail, messages
    │  └─> EmailAgent
    │
    ├─ Contains: news, headlines, brief, current events
    │  └─> NewsReaderAgent
    │
    ├─ Contains: nearby, directions, traffic, restaurant, location
    │  └─> MapsAgent
    │
    ├─ Contains: research, analyze, compare, investigate, deep dive
    │  └─> ResearcherAgent
    │
    └─ Else: greeting, general chat, capability questions
       └─> Handle directly (no delegation)
```

---

## 🔐 Security & Best Practices

```
┌─────────────────────────────────────────────────────────┐
│              SECURITY CONSIDERATIONS                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ✓ Environment Variables                               │
│    • API keys stored in .env                           │
│    • Not committed to version control                  │
│                                                         │
│  ✓ Tool Permissions                                    │
│    • Each agent has limited tool access                │
│    • Principle of least privilege                      │
│                                                         │
│  ✓ Session Isolation                                   │
│    • Each user has separate sessions                   │
│    • State not shared across users                     │
│                                                         │
│  ✓ Input Validation                                    │
│    • Type hints enforce parameter types                │
│    • Tools validate inputs                             │
│                                                         │
│  ✓ Rate Limiting (Recommended)                         │
│    • Implement in production API                       │
│    • Prevent abuse of search/fetch tools               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📈 Performance Characteristics

| Agent | Avg Response Time | Tools Called | Complexity |
|-------|------------------|--------------|------------|
| EmailAgent | 2-5 sec | 1-2 | Low |
| NewsReaderAgent | 5-8 sec | 2-3 | Medium |
| MapsAgent | 3-6 sec | 1-2 | Low-Medium |
| ResearcherAgent | 10-20 sec | 3-5 | High |

---

## 🚀 Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  PRODUCTION SETUP                        │
└─────────────────────────────────────────────────────────┘

FastAPI Backend
    │
    ├─ POST /api/chat
    │  └─> AgentRunner.run_query()
    │
    ├─ POST /api/chat/stream
    │  └─> AgentRunner.run_async() → SSE
    │
    ├─ POST /api/session/create
    │  └─> AgentRunner.create_session()
    │
    └─ GET /api/session/{id}/history
       └─> SessionService.get_history()

Recommended Additions:
  • Redis for session persistence
  • PostgreSQL for chat history
  • Prometheus for metrics
  • Sentry for error tracking
```

---

This architecture provides:
- ✓ Modularity & Maintainability
- ✓ Scalability (easy to add agents)
- ✓ Separation of Concerns
- ✓ Testability
- ✓ Production-Ready Design
