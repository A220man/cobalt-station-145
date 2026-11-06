# Cobalt Station 145 — Ryan Vo

> Work in progress. This checkpoint may be incomplete or fail tests. See PLAN.md and STATUS.md before use.


A smarter, self-hosted AI assistant — multi-user, multi-agent.

## Quick Start

### Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the server
python -m cobalt_station.main
```

The API will be available at `http://localhost:8000`

### Docker

```bash
# Build image
docker build -t cobalt-station-145 .

# Run container
docker run -p 8000:8000 cobalt-station-145
```

## API Endpoints

- `GET /api/health` — Health check
- `POST /api/agents` — Create a new agent with workspace
- `GET /api/agents` — List all agents
- `GET /api/agents/{agent_id}` — Get agent workspace info
- `GET /api/agents/{agent_id}/files` — List files in agent's workspace
- `GET /api/agents/{agent_id}/files/read` — Read a file from agent's workspace
- `POST /api/agents/{agent_id}/files/write` — Write a file to agent's workspace
- `POST /api/agents/{agent_id}/files/create` — Create a new file in agent's workspace
- `DELETE /api/agents/{agent_id}/files` — Delete a file from agent's workspace

## Project Structure

```
src/cobalt_station/
├── main.py              # Application entry point
├── api/
│   ├── __init__.py
│   ├── health.py        # Health check endpoint
│   └── agents.py        # Agent workspace endpoints
├── core/
│   ├── __init__.py
│   └── workspace.py     # Workspace isolation logic
└── tools/
    ├── __init__.py
    └── file_ops.py      # File operations with isolation
```

## Development

```bash
# Run tests
pytest

# Lint
ruff check .

# Type check
mypy src/
```

## License

MIT

Maintainer: Ryan Vo <ryandtvo@gmail.com>
