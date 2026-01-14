# Binary Brute Force Team - Project Documentation

## Overview

**Binary Brute Force Team** is a full-stack multi-agent system designed for creating interactive STEM educational content. The project combines FastAPI, HTMX, and LangGraph to provide a powerful platform for AI-driven educational content generation.

### Key Features

- 🤖 **Multi-Agent System**: LangGraph-powered agents with analyzer-executor workflow
- 🎨 **Interactive UI**: HTMX-based dashboard with real-time updates (no page reloads)
- ⚡ **Async Processing**: Celery task queue for long-running agent workflows
- 🗄️ **Persistent Storage**: MySQL database with SQLAlchemy ORM
- 🐳 **Docker-Ready**: Multi-service Docker Compose setup
- 📊 **Production-Ready**: Gunicorn + Uvicorn workers with health checks

---

## Architecture

### Technology Stack

**Backend:**
- FastAPI 0.115.12 - Modern Python web framework
- Python 3.12.9 - Language runtime
- Gunicorn + Uvicorn - ASGI server with workers
- SQLAlchemy 2.0 - Database ORM
- Alembic - Database migrations

**Queue & Cache:**
- Celery 5.4 - Distributed task queue
- Redis 7 - Message broker and cache

**Database:**
- MySQL 8.0 - Relational database

**AI/ML:**
- LangChain 1.2+ - LLM framework
- LangGraph 1.0+ - Multi-agent orchestration
- OpenAI API - GPT models (gpt-4)

**Frontend:**
- HTMX 1.9 - Dynamic HTML without JavaScript
- Jinja2 - Template engine
- CSS3 - Custom styling

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Browser                         │
│                    (HTMX Dashboard)                          │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Web Service                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Frontend   │  │   Agents     │  │    Health    │     │
│  │   Router     │  │   Router     │  │    Check     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────────────────────────────────────────┐     │
│  │         LangGraph Multi-Agent System              │     │
│  │  Analyzer Agent → Executor Agent → Result         │     │
│  └──────────────────────────────────────────────────┘     │
└───────┬──────────────────────┬──────────────────┬──────────┘
        │                      │                  │
        ↓                      ↓                  ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│    MySQL     │    │    Redis     │    │   Celery     │
│   Database   │    │    Broker    │    │   Worker     │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## Project Structure

```
binary-brute-force-team/
├── project/                        # Main application package
│   ├── __init__.py                 # App factory with FastAPI setup
│   ├── main.py                     # Entry point
│   ├── config.py                   # Settings (Pydantic)
│   ├── celery_utils.py             # Celery factory
│   ├── session.py                  # DB session (root level)
│   ├── models.py                   # SQLAlchemy models (root level)
│   ├── env.py                      # Alembic environment
│   ├── gunicorn_conf.py            # Gunicorn configuration
│   │
│   └── app/                        # Application modules
│       ├── routers/                # API route handlers
│       │   ├── __init__.py         # Router registration
│       │   ├── health_check.py     # Health endpoint
│       │   ├── frontend.py         # HTMX page routes
│       │   └── agents.py           # LangGraph API endpoints
│       │
│       ├── agents/                 # LangGraph implementations
│       │   ├── __init__.py
│       │   └── simple_agent.py     # Multi-agent workflow
│       │
│       ├── schemas/                # Pydantic schemas
│       │   └── agent.py            # Agent request/response models
│       │
│       ├── models/                 # SQLAlchemy models
│       │   └── models.py           # Database models
│       │
│       ├── database/               # Database layer
│       │   ├── session.py          # Session management
│       │   └── repository/         # Data access layer
│       │
│       ├── celery/                 # Celery tasks
│       │   ├── setup.py            # Celery initialization
│       │   └── tasks.py            # Async agent tasks
│       │
│       ├── templates/              # Jinja2 templates
│       │   ├── base.html           # Base template
│       │   ├── index.html          # Dashboard page
│       │   └── components/         # HTMX components
│       │       └── agent_status.html
│       │
│       └── static/                 # Static assets
│           ├── css/
│           │   └── styles.css      # Custom styles
│           └── js/
│               └── htmx.min.js     # HTMX library (CDN)
│
├── migrations/                     # Alembic migrations
│   ├── env.py                      # Migration environment
│   └── versions/                   # Migration scripts
│
├── docker-compose.yaml             # Multi-service orchestration
├── Dockerfile                      # Production image
├── entrypoint.sh                   # Container startup script
├── alembic.ini                     # Alembic configuration
├── pyproject.toml                  # Dependencies (uv)
├── uv.lock                         # Lockfile
├── .env                            # Environment variables (not in git)
├── .env.example                    # Environment template
├── .dockerignore                   # Docker build exclusions
└── README.md                       # Project README
```

---

## Setup Instructions

### Prerequisites

- Docker & Docker Compose (or `docker compose` v2)
- OpenAI API key
- (Optional) `uv` package manager for local development

### Quick Start

1. **Clone and navigate to the project:**
   ```bash
   cd binary-brute-force-team
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Add your OpenAI API key to `.env`:**
   ```bash
   # Edit .env
   OPENAI_API_KEY=sk-your-openai-api-key-here
   ```

4. **Start all services:**
   ```bash
   docker compose up -d
   ```

5. **Wait for services to initialize (~15 seconds):**
   ```bash
   # Check logs
   docker logs bbf-web
   ```

6. **Access the application:**
   - Dashboard: http://localhost:8010
   - Health Check: http://localhost:8010/health
   - API Docs: http://localhost:8010/docs

### Local Development Setup

For local development without Docker:

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Set up database:**
   ```bash
   # Start MySQL and Redis locally, or use Docker for just these services
   docker compose up -d mysql redis
   ```

3. **Configure environment:**
   ```bash
   export MYSQL_HOST=localhost
   export MYSQL_DATABASE=bbf_db
   export MYSQL_USER=admin
   export MYSQL_PASSWORD=admin
   export BROKER_URL=redis://localhost:6379/0
   export OPENAI_API_KEY=sk-your-key-here
   ```

4. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Start the application:**
   ```bash
   uvicorn project.main:app --reload --port 8010
   ```

6. **Start Celery worker (separate terminal):**
   ```bash
   celery -A project.main.celery worker -l info
   ```

---

## Docker Services

### Service Overview

| Service | Container | Port | Description |
|---------|-----------|------|-------------|
| `web` | `bbf-web` | 8010 | FastAPI application (Gunicorn + Uvicorn) |
| `worker` | `bbf-worker` | - | Celery worker for async tasks |
| `mysql` | `bbf-mysql` | 3306 | MySQL 8.0 database |
| `redis` | `bbf-redis` | 6379 | Redis cache and message broker |

### Docker Commands

```bash
# Start all services
docker compose up -d

# View logs
docker logs bbf-web -f
docker logs bbf-worker -f

# Restart a service
docker compose restart web

# Stop all services
docker compose down

# Rebuild after code changes
docker compose build
docker compose up -d

# Clean rebuild (removes cache)
docker compose build --no-cache

# Access container shell
docker exec -it bbf-web bash

# Run migrations inside container
docker exec bbf-web alembic upgrade head

# Access MySQL database
docker exec -it bbf-mysql mysql -uadmin -padmin bbf_db
```

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for GPT models | `sk-proj-...` |
| `MYSQL_HOST` | MySQL host | `mysql` (Docker) or `localhost` |
| `MYSQL_DATABASE` | Database name | `bbf_db` |
| `MYSQL_USER` | Database user | `admin` |
| `MYSQL_PASSWORD` | Database password | `admin` |
| `BROKER_URL` | Redis/Celery broker URL | `redis://redis:6379/0` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_MODEL` | OpenAI model to use | `gpt-4` |
| `LLM_TEMPERATURE` | Model temperature | `0.0` |
| `GUNICORN_CONCURRENCY` | Number of Gunicorn workers | `2` |
| `WORKER_CONCURRENCY` | Number of Celery workers | `4` |
| `POD_TYPE` | Service type (`web` or `worker`) | Auto-detected |

---

## API Endpoints

### Health Check

**GET** `/health`

Returns service health status.

**Response:**
```json
{
  "Status": "ok"
}
```

### Frontend Routes

**GET** `/`

Main dashboard page (HTMX interface).

**GET** `/components/agent-status`

HTMX partial component for agent status (auto-refreshes every 5 seconds).

### LangGraph Agent API

#### Synchronous Execution

**POST** `/api/agents/execute`

Execute agent workflow synchronously (returns HTML for HTMX).

**Request Body:**
```json
{
  "query": "What is the Pythagorean theorem?"
}
```

**Response (HTML):**
```html
<div class="result success">
  <h4>Agent Response:</h4>
  <p>The Pythagorean theorem states that in a right-angled triangle...</p>
</div>
```

#### Asynchronous Execution

**POST** `/api/agents/execute-async`

Execute agent workflow asynchronously via Celery (for long-running tasks).

**Request Body:**
```json
{
  "query": "Explain quantum entanglement in detail"
}
```

**Response:**
```json
{
  "task_id": "abc123-def456-...",
  "status": "processing"
}
```

#### Task Status Check

**GET** `/api/agents/task/{task_id}`

Check status of async agent task.

**Response (Processing):**
```json
{
  "status": "processing"
}
```

**Response (Completed):**
```json
{
  "status": "completed",
  "result": "Quantum entanglement is a phenomenon where..."
}
```

---

## LangGraph Multi-Agent System

### Agent Workflow

The system uses a **two-stage agent workflow**:

```
User Query → Analyzer Agent → Executor Agent → Result
```

1. **Analyzer Agent**: Understands and breaks down the query, identifying key concepts
2. **Executor Agent**: Generates a detailed, educational response based on the analysis

### Agent Implementation

Located in: `project/app/agents/simple_agent.py`

**Key Features:**
- **State Management**: Uses `TypedDict` for strongly-typed state
- **Async Execution**: Fully async with `ainvoke`
- **Graph Compilation**: LangGraph compiles the workflow into an executable graph
- **Configurable LLM**: Model, temperature, and API key from settings

**Example Agent State:**
```python
class AgentState(TypedDict):
    query: str       # User's input
    analysis: str    # Analyzer's breakdown
    result: str      # Executor's final response
```

### Adding New Agents

To add a new agent workflow:

1. **Create agent file**: `project/app/agents/your_agent.py`
2. **Define state**: Create a `TypedDict` for state management
3. **Implement nodes**: Create functions for each agent in the workflow
4. **Build graph**: Use `StateGraph` to connect nodes
5. **Expose API**: Add endpoint in `project/app/routers/agents.py`

**Example:**
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class YourAgentState(TypedDict):
    input: str
    output: str

async def run_your_agent(input: str) -> str:
    def node1(state: YourAgentState) -> YourAgentState:
        # Your logic here
        return {**state, "output": "processed"}

    workflow = StateGraph(YourAgentState)
    workflow.add_node("node1", node1)
    workflow.add_edge("node1", END)
    workflow.set_entry_point("node1")

    graph = workflow.compile()
    result = await graph.ainvoke({"input": input})
    return result["output"]
```

---

## Database

### Schema Management

The project uses **Alembic** for database migrations.

**Create a new migration:**
```bash
# Inside container
docker exec bbf-web alembic revision --autogenerate -m "Add new table"

# Locally
alembic revision --autogenerate -m "Add new table"
```

**Apply migrations:**
```bash
# Inside container
docker exec bbf-web alembic upgrade head

# Locally
alembic upgrade head
```

**Rollback migration:**
```bash
alembic downgrade -1
```

### Adding Models

1. **Create model** in `project/app/models/models.py`:
   ```python
   from sqlalchemy import Column, Integer, String, DateTime
   from sqlalchemy.ext.declarative import declarative_base
   from datetime import datetime

   Base = declarative_base()

   class YourModel(Base):
       __tablename__ = "your_table"

       id = Column(Integer, primary_key=True)
       name = Column(String(255))
       created_at = Column(DateTime, default=datetime.utcnow)
   ```

2. **Generate migration**:
   ```bash
   alembic revision --autogenerate -m "Add YourModel"
   ```

3. **Apply migration**:
   ```bash
   alembic upgrade head
   ```

---

## Frontend Development

### HTMX Patterns

The frontend uses **HTMX** for dynamic interactions without writing JavaScript.

**Common Patterns:**

**1. Form Submission (No Page Reload):**
```html
<form hx-post="/api/agents/execute"
      hx-target="#result"
      hx-swap="innerHTML">
    <input type="text" name="query" required>
    <button type="submit">Execute</button>
</form>
<div id="result"></div>
```

**2. Auto-Refresh Component:**
```html
<div hx-get="/components/agent-status"
     hx-trigger="load, every 5s"
     hx-swap="innerHTML">
    Loading...
</div>
```

**3. Click Action:**
```html
<button hx-post="/api/action"
        hx-vals='{"param": "value"}'
        hx-target="#output">
    Click Me
</button>
```

**4. Loading Indicator:**
```html
<form hx-post="/api/endpoint"
      hx-indicator="#loading">
    <button type="submit">Submit</button>
    <div id="loading" class="htmx-indicator">Processing...</div>
</form>
```

### Adding New Pages

1. **Create template** in `project/app/templates/your_page.html`
2. **Add route** in `project/app/routers/frontend.py`:
   ```python
   @router.get("/your-page", response_class=HTMLResponse)
   async def your_page(request: Request):
       return request.app.state.templates.TemplateResponse(
           "your_page.html",
           {"request": request, "data": "value"}
       )
   ```

---

## Celery Tasks

### Task Structure

Tasks are defined in `project/app/celery/tasks.py`.

**Example Task:**
```python
from celery import shared_task
import asyncio

@shared_task(bind=True, name="project.app.celery.tasks.my_task")
def my_task(self, param: str):
    """Your task description"""
    try:
        # For async code
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(async_function(param))
        loop.close()
        return result
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise
```

### Running Tasks

**From API endpoint:**
```python
from project.app.celery.tasks import my_task

# Async execution
task = my_task.delay("parameter")
task_id = task.id

# Check status
result = my_task.AsyncResult(task_id)
if result.ready():
    print(result.result)
```

### Monitoring

**View Celery logs:**
```bash
docker logs bbf-worker -f
```

**Check task status in code:**
```python
from celery.result import AsyncResult

task = AsyncResult(task_id)
print(task.state)  # PENDING, STARTED, SUCCESS, FAILURE
print(task.info)   # Task result or error info
```

---

## Testing

### Running Tests

```bash
# Install dev dependencies
uv sync --dev

# Run all tests
pytest

# Run with coverage
pytest --cov=project --cov-report=html

# Run specific test
pytest tests/test_agents.py::test_simple_agent
```

### Example Tests

**API Test:**
```python
from fastapi.testclient import TestClient
from project.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"Status": "ok"}
```

**Agent Test:**
```python
import pytest
from project.app.agents.simple_agent import run_simple_agent

@pytest.mark.asyncio
async def test_simple_agent():
    result = await run_simple_agent("Test query")
    assert isinstance(result, str)
    assert len(result) > 0
```

---

## Troubleshooting

### Common Issues

#### 1. Services Won't Start

**Check logs:**
```bash
docker logs bbf-web
docker logs bbf-worker
```

**Common causes:**
- Missing `OPENAI_API_KEY` in `.env`
- MySQL not ready (wait 10-15 seconds)
- Port conflicts (8010, 3306, 6379 in use)

**Solution:**
```bash
# Restart services
docker compose restart

# Or rebuild
docker compose down
docker compose up -d
```

#### 2. Database Connection Errors

**Error:** `MySQL connection failed`

**Solution:**
```bash
# Check MySQL is running
docker ps | grep mysql

# Check MySQL logs
docker logs bbf-mysql

# Verify environment variables
docker exec bbf-web env | grep MYSQL
```

#### 3. Import Errors (Pydantic)

**Error:** `BaseSettings has been moved to pydantic-settings`

**Solution:** Already fixed in `project/config.py`:
```python
from pydantic_settings import BaseSettings  # ✓ Correct
```

#### 4. HTMX Not Loading

**Check static files:**
```bash
curl http://localhost:8010/static/css/styles.css
```

**Verify HTMX CDN:**
- Open browser console (F12)
- Check for HTMX errors
- Ensure internet connection (CDN requires internet)

#### 5. Agent Execution Fails

**Check:**
1. OpenAI API key is valid
2. API key has sufficient credits
3. Model name is correct (`gpt-4` or `gpt-3.5-turbo`)

**Debug:**
```bash
# Check environment
docker exec bbf-web env | grep OPENAI

# Test API key manually
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

## Performance Optimization

### Production Recommendations

1. **Increase Workers:**
   ```yaml
   # docker-compose.yaml
   environment:
     GUNICORN_CONCURRENCY: 4  # More workers for web
     WORKER_CONCURRENCY: 8    # More Celery workers
   ```

2. **Add Redis Result Backend:**
   ```python
   # celery_utils.py
   celery_app.conf.result_backend = 'redis://redis:6379/1'
   ```

3. **Enable Connection Pooling:**
   ```python
   # project/app/database/session.py
   engine = create_engine(
       DATABASE_URL,
       pool_size=10,
       max_overflow=20,
       pool_pre_ping=True
   )
   ```

4. **Cache Frequently Used Data:**
   ```python
   import redis
   r = redis.Redis(host='redis', port=6379, decode_responses=True)

   # Cache pattern
   cached = r.get('key')
   if not cached:
       data = expensive_operation()
       r.setex('key', 3600, data)  # 1 hour TTL
   ```

---

## Future Enhancements

### Planned Features

- [ ] **User Authentication**: JWT-based auth with user accounts
- [ ] **Agent History**: Store and retrieve past agent executions
- [ ] **Multiple Agent Types**: Add specialized agents for different subjects
- [ ] **WebSocket Support**: Real-time progress updates for long-running tasks
- [ ] **API Rate Limiting**: Prevent abuse with rate limiting
- [ ] **Observability**: Add Prometheus metrics and Grafana dashboards
- [ ] **S3 Integration**: Store generated content in S3
- [ ] **Advanced UI**: Enhanced dashboard with charts and analytics
- [ ] **Agent Marketplace**: Allow users to create and share custom agents
- [ ] **Multi-Language Support**: I18n for frontend

### Enhancement Ideas

1. **Advanced LangGraph Workflows:**
   - Multi-turn conversations
   - Agent memory/context
   - Conditional branching
   - Human-in-the-loop approval

2. **Rich Media Generation:**
   - Generate diagrams with Matplotlib
   - Create interactive simulations
   - Produce educational videos

3. **Collaborative Features:**
   - Share agent results
   - Team workspaces
   - Comment on outputs

---

## Contributing

### Development Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Make changes and test:**
   ```bash
   # Run tests
   pytest

   # Check linting
   ruff check .

   # Format code
   ruff format .
   ```

3. **Commit with descriptive messages:**
   ```bash
   git commit -m "Add: New agent workflow for physics problems"
   ```

4. **Push and create PR:**
   ```bash
   git push origin feature/your-feature
   ```

### Code Style

- Follow **PEP 8** for Python code
- Use **type hints** for all function signatures
- Write **docstrings** for classes and functions
- Keep functions **small and focused**
- Use **meaningful variable names**

---

## License

[Your License Here]

---

## Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Contact the maintainers
- Check the troubleshooting section above

---

## Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [LangChain](https://python.langchain.com/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [HTMX](https://htmx.org/)
- [Celery](https://docs.celeryproject.org/)

---

**Last Updated:** January 2026
**Version:** 0.1.0
