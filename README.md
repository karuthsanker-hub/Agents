# 🧊 Arctic Debate Card Agent

**AI-powered research assistant for Policy Debate (2025-2026 Arctic Topic)**

Author: **Shiv Sanker**  
License: MIT  
Version: 2.0.0

---

## 📋 Overview

The Arctic Debate Card Agent is a comprehensive AI-powered tool designed to help high school policy debaters research and prepare evidence for the 2025-2026 NSDA policy debate topic:

> "Resolved: The United States federal government should significantly increase its exploration and/or development of the Arctic."

### Key Features

- 🔍 **Article Discovery** - Find and analyze debate-relevant articles
- ✂️ **Card Cutting** - Auto-format evidence into proper CX debate cards
- 💬 **Research Chat** - AI assistant for debate research questions
- 📚 **Article Library** - Organized database of sources
- 🎯 **Argument Classification** - Auto-tag articles as Aff/Neg evidence
- 🔐 **Google Authentication** - Secure user login
- 📊 **Usage Tracking** - Monitor OpenAI token usage

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Articles   │  │ Card Editor │  │    Chat     │             │
│  │     Tab     │  │     Tab     │  │     Tab     │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Server (main.py)                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                     Middleware Layer                         ││
│  │  • CORS • Verbose Logging • Request Timing • Auth Check     ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐│
│  │  /auth   │ │  /chat   │ │/articles │ │  /admin  │ │/system ││
│  │  Router  │ │  Router  │ │  Router  │ │  Router  │ │ Router ││
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬───┘│
└───────┼────────────┼────────────┼────────────┼────────────┼────┘
        │            │            │            │            │
        ▼            ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Service Layer                             │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ AuthManager  │  │ResearchAgent │  │   ArticleAnalyzer    │  │
│  │ (Google SSO) │  │  (Chat AI)   │  │  (Content Analysis)  │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │CardFormatter │  │ArticleManager│  │  AdminConfigManager  │  │
│  │ (Card Gen)   │  │  (CRUD)      │  │    (Settings)        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
        │            │            │            │
        ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Data Layer                                 │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  PostgreSQL  │  │    Redis     │  │      ChromaDB        │  │
│  │              │  │              │  │                      │  │
│  │ • Users      │  │ • L1 Cache   │  │ • Semantic Memory    │  │
│  │ • Sessions   │  │ • Rate Limit │  │ • Response Cache     │  │
│  │ • Articles   │  │ • Quick KV   │  │ • Article Embeddings │  │
│  │ • Chat Logs  │  │              │  │                      │  │
│  │ • Usage      │  │              │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                     External Services                            │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   OpenAI     │  │   Google     │  │   Web Sources        │  │
│  │   GPT-4o     │  │   OAuth 2.0  │  │   (Articles/PDFs)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema

### PostgreSQL Tables

| Table | Purpose |
|-------|---------|
| `users` | Google OAuth user profiles |
| `user_sessions` | Authentication sessions |
| `articles` | Article metadata and analysis |
| `conversations` | Chat history logs |
| `agent_stats` | Daily usage statistics |
| `admin_config` | Configuration settings |
| `admin_auth` | Admin password (bcrypt hashed) |
| `usage_tracking` | OpenAI token usage per request |
| `usage_summary` | Daily token usage aggregates |

### ChromaDB Collections

| Collection | Purpose |
|------------|---------|
| `agent_memory` | Conversation context for semantic search |
| `agent_responses` | Cached responses for semantic deduplication |
| `article_content` | Article embeddings for similarity search |

---

## 🚀 Token Optimization Strategy

The agent uses a **tiered caching system** to minimize OpenAI API calls:

```
User Query
    │
    ▼
┌─────────────────────────────────────┐
│ Layer 1: Redis (Exact Match)        │  ◀── Fastest (ms)
│ Check for identical query           │      TTL: 1 hour
└─────────────────────────────────────┘
    │ Miss
    ▼
┌─────────────────────────────────────┐
│ Layer 2: ChromaDB (Semantic Match)  │  ◀── Fast (10-50ms)
│ Check for similar questions         │      Similarity > 65%
│ using vector embeddings             │
└─────────────────────────────────────┘
    │ Miss
    ▼
┌─────────────────────────────────────┐
│ Layer 3: OpenAI API                 │  ◀── Expensive
│ Generate new response               │      Tokens tracked
│ Cache in both Redis & ChromaDB      │
└─────────────────────────────────────┘
```

---

## 📁 Project Structure

```
first_agent/
├── app/
│   ├── core/
│   │   ├── config.py           # Pydantic settings
│   │   ├── logging_config.py   # Verbose logging
│   │   ├── admin_config.py     # Admin settings & usage tracking
│   │   └── auth.py             # Google OAuth
│   ├── debate/
│   │   ├── article_analyzer.py # GPT article analysis
│   │   ├── article_manager.py  # Article CRUD
│   │   ├── card_formatter.py   # Debate card formatting
│   │   └── seed_articles.py    # Starter articles
│   ├── memory/
│   │   └── memory_manager.py   # PostgreSQL/Redis/ChromaDB
│   └── agent.py                # Research agent
├── server/
│   ├── main.py                 # FastAPI app
│   ├── ui_templates.py         # HTML/CSS/JS UI
│   └── routers/
│       ├── auth.py             # /auth/* endpoints
│       ├── chat.py             # /chat/* endpoints
│       ├── articles.py         # /articles/* endpoints
│       ├── admin.py            # /admin/* endpoints
│       └── system.py           # /, /health, /stats
├── tests/
│   └── test_api.py             # API tests for CI/CD
├── logs/                       # Application logs
├── chroma_db/                  # ChromaDB persistence
├── requirements.txt            # Dependencies
├── .env                        # Environment variables (not in git)
└── env.example                 # Example environment file
```

---

## ⚙️ Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- OpenAI API key
- Google OAuth credentials (optional)

### Setup

```bash
# Clone repository
git clone <repo-url>
cd first_agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp env.example .env
# Edit .env with your credentials

# Run database migrations (auto on first start)
# Start the server
cd server
python main.py
```

### Environment Variables

```env
# Required
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0

# Optional - Google Auth
GOOGLE_CLIENT_ID=...apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=...

# Optional - Pinecone
PINECONE_API_KEY=...
```

---

## 🌐 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/status` | Check if auth is enabled |
| GET | `/auth/login` | Redirect to Google OAuth |
| GET | `/auth/callback` | OAuth callback handler |
| GET | `/auth/logout` | Log out user |
| GET | `/auth/me` | Get current user |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Send message to research agent |
| POST | `/chat/search` | Semantic search chat history |
| GET | `/chat/history/{session}` | Get session history |

### Articles
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/articles` | List all articles |
| POST | `/articles` | Add new article |
| GET | `/articles/{id}` | Get article details |
| DELETE | `/articles/{id}` | Delete article |
| POST | `/articles/analyze` | Analyze article URL |
| POST | `/articles/search` | Semantic article search |
| GET | `/articles/check-url` | Check for duplicates |
| POST | `/articles/seed` | Add starter articles |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/admin/login` | Admin login |
| GET | `/admin/config` | Get all settings |
| POST | `/admin/config` | Update setting |
| GET | `/admin/usage` | Get usage stats |
| GET | `/admin/rate-check` | Check rate limits |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| GET | `/stats` | System statistics |
| GET | `/db-info` | Database status |
| GET | `/ui` | Web interface |

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test
pytest tests/test_api.py::test_health_check -v
```

### GitHub Actions CI

Tests are configured to run on push/PR:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ --tb=short
```

---

## 📊 Usage Limits

Default limits (configurable via Admin panel):

| Limit | Default | Description |
|-------|---------|-------------|
| Daily Tokens | 100,000 | Max tokens per day |
| Monthly Tokens | 2,000,000 | Max tokens per month |
| Requests/Minute | 20 | Rate limit |
| Tokens/Request | 4,000 | Max per single request |

---

## 🔒 Security

- **Passwords**: Hashed with bcrypt (12 rounds)
- **Sessions**: Secure random tokens (64 bytes)
- **OAuth**: Google OAuth 2.0 with PKCE
- **Cookies**: HttpOnly, SameSite=Lax
- **API Keys**: Environment variables only

---

## 📝 License

MIT License - See LICENSE file

---

## 👤 Author

**Shiv Sanker**

Built for NSDA Policy Debate 2025-2026

---

## 🙏 Acknowledgments

- OpenAI for GPT-4
- The debate community for topic expertise
- FastAPI, ChromaDB, and all open source contributors

