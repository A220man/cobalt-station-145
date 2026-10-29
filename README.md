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

## Project Structure

```
src/cobalt_station/
├── main.py              # Application entry point
├── api/
│   ├── __init__.py
│   └── health.py        # Health check endpoint
└── core/
    └── __init__.py
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
