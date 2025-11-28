# 🤖 First Agent - Architecture Document

## Overview

This project is an **Agentic AI system** built with a FastAPI backend. The agent is designed to autonomously perform tasks including browser automation, memory management, and extensible skills.

## 🏗️ Project Structure

```
first_agent/
├── 📁 app/                    # Core application code
│   ├── 📁 browser/            # Browser automation module
│   │   └── test_browser.py    # Browser testing utilities
│   ├── 📁 memory/             # Agent memory systems
│   │   ├── short_term.py      # Working memory (context window)
│   │   ├── long_term.py       # Persistent storage (vector DB)
│   │   └── episodic.py        # Experience/conversation history
│   ├── 📁 skills/             # Extensible agent capabilities
│   │   ├── base.py            # Base skill interface
│   │   ├── web_search.py      # Web search skill
│   │   └── code_execution.py  # Code execution skill
│   ├── 📁 core/               # Core utilities (to be added)
│   │   ├── config.py          # Configuration management
│   │   ├── logging.py         # Logging setup
│   │   └── exceptions.py      # Custom exceptions
│   └── 📁 models/             # Pydantic models (to be added)
│       ├── agent.py           # Agent-related models
│       └── api.py             # API request/response models
│
├── 📁 server/                 # FastAPI server
│   ├── main.py                # Application entry point
│   ├── 📁 routers/            # API route handlers (to be added)
│   │   ├── agent.py           # Agent endpoints
│   │   ├── memory.py          # Memory endpoints
│   │   └── health.py          # Health check endpoints
│   ├── 📁 services/           # Business logic (to be added)
│   └── 📁 middleware/         # Custom middleware (to be added)
│
├── 📁 tests/                  # Test suite (to be added)
│   ├── conftest.py            # Pytest fixtures
│   ├── test_api.py            # API tests
│   └── test_agent.py          # Agent tests
│
├── 📄 .cursorrules            # AI coding guidelines
├── 📄 .env.example            # Environment template
├── 📄 requirements.txt        # Python dependencies
├── 📄 ARCHITECTURE.md         # This file
└── 📄 README.md               # Project readme
```

## 🛠️ Technology Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **FastAPI** | High-performance async web framework |
| **Pydantic** | Data validation and settings management |
| **Uvicorn** | ASGI server |
| **Python 3.10+** | Runtime |

### AI & Agent
| Technology | Purpose |
|------------|---------|
| **OpenAI API** | LLM provider for agent reasoning |
| **browser-use** | Browser automation framework |
| **Playwright** | Browser automation engine |

### Data & Storage
| Technology | Purpose |
|------------|---------|
| **SQLAlchemy** | Database ORM (optional) |
| **Redis** | Caching and queues (optional) |
| **Vector DB** | Long-term memory (ChromaDB/Pinecone) |

### Development
| Technology | Purpose |
|------------|---------|
| **pytest** | Testing framework |
| **Black** | Code formatter |
| **Ruff** | Fast Python linter |
| **python-dotenv** | Environment management |

## 🧠 Agent Architecture

### Memory System

```
┌─────────────────────────────────────────────────────────────┐
│                      AGENT MEMORY                           │
├─────────────────┬─────────────────┬─────────────────────────┤
│  SHORT-TERM     │   LONG-TERM     │      EPISODIC           │
│  (Working)      │   (Persistent)  │      (Experience)       │
├─────────────────┼─────────────────┼─────────────────────────┤
│ • Current task  │ • Vector store  │ • Conversation logs     │
│ • Context       │ • Knowledge     │ • Past interactions     │
│ • Recent msgs   │ • Facts/docs    │ • Success/failure       │
│ • Token limit   │ • Embeddings    │ • Learning history      │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### Skill System

Skills are modular, plug-and-play capabilities:

```python
class BaseSkill(ABC):
    """Base interface for all agent skills."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique skill identifier."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description for LLM to understand when to use."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> SkillResult:
        """Execute the skill with given parameters."""
        pass
```

### Agent Flow

```
User Request
     │
     ▼
┌─────────────┐
│   FastAPI   │ ◄── HTTP Request
│   Server    │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│   Agent     │ ◄── Load memory context
│   Core      │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│    LLM      │ ◄── Reasoning & planning
│  (OpenAI)   │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│   Skills    │ ◄── Execute actions
│  (Tools)    │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│   Memory    │ ◄── Store results
│   Update    │
└─────┬───────┘
      │
      ▼
   Response
```

## 🔌 API Endpoints

### Current Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check / status |

### Planned Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/agent/chat` | Send message to agent |
| POST | `/agent/task` | Submit task for execution |
| GET | `/agent/status` | Get agent status |
| GET | `/memory/history` | Get conversation history |
| DELETE | `/memory/clear` | Clear agent memory |

## 🔐 Security Considerations

1. **API Keys**: Never commit to git; use `.env` files
2. **Input Validation**: All inputs validated via Pydantic
3. **Rate Limiting**: Implement for production
4. **CORS**: Configure for web clients
5. **Logging**: Sanitize sensitive data before logging

## 🚀 Getting Started

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env with your API keys

# 3. Run the server
cd server
uvicorn main:app --reload

# 4. Test the API
curl http://localhost:8000
```

## 📝 Development Guidelines

See `.cursorrules` for detailed coding standards and AI assistant guidelines.

## 🔮 Future Enhancements

- [ ] Multi-agent collaboration
- [ ] Voice interface integration
- [ ] Plugin system for custom skills
- [ ] Web UI dashboard
- [ ] Scheduled task execution
- [ ] Webhook integrations

