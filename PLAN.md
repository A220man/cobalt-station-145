# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

core-api-skeleton

## Roadmap

### core-api-skeleton — Core FastAPI Skeleton with Health Check

Status: done

Acceptance:
- FastAPI app starts on port 8000
- GET /api/health returns 200 with status info
- Basic project structure with pyproject.toml
- Dockerfile for containerization

Implementation: `pyproject.toml`, `src/cobalt_station/main.py`, `src/cobalt_station/api/health.py`, `Dockerfile`, `README.md`

Tests: `tests/test_health.py`

### agent-workspace-isolation — Agent Workspace File Isolation (Issue #1160)

Status: planned

Acceptance:
- Each agent has dedicated workspace under ./workspaces/{agent_id}/
- File operations (read/write/create) restricted to agent's workspace
- Cross-agent workspace access returns permission error
- Path traversal attempts blocked

Implementation: `src/cobalt_station/api/agents.py`, `src/cobalt_station/core/workspace.py`, `src/cobalt_station/tools/file_ops.py`

Tests: `tests/test_workspace_isolation.py`

### multi-user-auth — Multi-user Authentication & Authorization

Status: planned

Acceptance:
- User registration and login endpoints
- JWT token-based authentication
- Role-based access control (admin, user)
- User data isolation

Implementation: `src/cobalt_station/api/auth.py`, `src/cobalt_station/core/auth.py`, `src/cobalt_station/models/user.py`

Tests: `tests/test_auth.py`

### mcp-server — MCP Server for External AI Access (Issue #322)

Status: planned

Acceptance:
- MCP server exposes tools/resources to external AI clients
- Standard MCP protocol compliance
- Tool registration and invocation

Implementation: `src/cobalt_station/mcp/server.py`, `src/cobalt_station/mcp/tools.py`

Tests: `tests/test_mcp.py`

### shared-specialist-agents — Shared Specialist Agents for Users (Issue #2207)

Status: planned

Acceptance:
- Admins can configure shared specialist agents
- Regular users access pre-configured specialists without setup
- User data/workspace isolation maintained

Implementation: `src/cobalt_station/api/specialists.py`, `src/cobalt_station/core/specialist.py`

Tests: `tests/test_specialists.py`

