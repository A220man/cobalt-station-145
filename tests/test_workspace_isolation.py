"""Tests for agent workspace isolation."""
import pytest
from httpx import ASGITransport, AsyncClient

from cobalt_station.main import create_app


@pytest.fixture
async def client():
    """Create test client."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_agent_creates_workspace(client: AsyncClient):
    """Test that creating an agent creates a workspace."""
    response = await client.post("/api/agents", json={"agent_id": "test_agent"})
    assert response.status_code == 201
    data = response.json()
    assert data["agent_id"] == "test_agent"
    assert "workspace_path" in data
    assert data["file_count"] == 0


@pytest.mark.asyncio
async def test_agent_workspace_isolation(client: AsyncClient):
    """Test that agents cannot access each other's workspaces."""
    # Create two agents
    await client.post("/api/agents", json={"agent_id": "agent_a"})
    await client.post("/api/agents", json={"agent_id": "agent_b"})

    # Agent A writes a file
    await client.post(
        "/api/agents/agent_a/files/write",
        json={"path": "secret.txt", "content": "agent_a_secret"}
    )

    # Agent B tries to read Agent A's file - should fail
    response = await client.get("/api/agents/agent_b/files/read", params={"path": "../agent_a/secret.txt"})
    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "workspace_permission"


@pytest.mark.asyncio
async def test_path_traversal_blocked(client: AsyncClient):
    """Test that path traversal attempts are blocked."""
    await client.post("/api/agents", json={"agent_id": "test_agent"})

    # Try to escape workspace with various path traversal patterns
    for bad_path in ["../../../etc/passwd", "..", "../", "subdir/../../../etc/passwd"]:
        response = await client.get("/api/agents/test_agent/files/read", params={"path": bad_path})
        assert response.status_code in (400, 403), f"Path {bad_path} should be blocked"


@pytest.mark.asyncio
async def test_cross_agent_write_blocked(client: AsyncClient):
    """Test that agents cannot write to each other's workspaces."""
    await client.post("/api/agents", json={"agent_id": "agent_a"})
    await client.post("/api/agents", json={"agent_id": "agent_b"})

    # Agent A tries to write to Agent B's workspace
    response = await client.post(
        "/api/agents/agent_a/files/write",
        json={"path": "../agent_b/malicious.txt", "content": "hack"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_file_operations_within_workspace(client: AsyncClient):
    """Test normal file operations within an agent's workspace."""
    await client.post("/api/agents", json={"agent_id": "test_agent"})

    # Create a file
    response = await client.post(
        "/api/agents/test_agent/files/create",
        json={"path": "new_file.txt", "content": "hello"}
    )
    assert response.status_code == 201
    assert response.json()["content"] == "hello"

    # Read the file
    response = await client.get("/api/agents/test_agent/files/read", params={"path": "new_file.txt"})
    assert response.status_code == 200
    assert response.json()["content"] == "hello"

    # Write (overwrite) the file
    response = await client.post(
        "/api/agents/test_agent/files/write",
        json={"path": "new_file.txt", "content": "world"}
    )
    assert response.status_code == 200
    assert response.json()["content"] == "world"

    # List files
    response = await client.get("/api/agents/test_agent/files")
    assert response.status_code == 200
    data = response.json()
    names = {item["name"] for item in data["items"]}
    assert "new_file.txt" in names

    # Delete the file
    response = await client.delete("/api/agents/test_agent/files", params={"path": "new_file.txt"})
    assert response.status_code == 204

    # Verify deleted
    response = await client.get("/api/agents/test_agent/files/read", params={"path": "new_file.txt"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_existing_file_fails(client: AsyncClient):
    """Test that creating an existing file fails."""
    await client.post("/api/agents", json={"agent_id": "test_agent"})
    await client.post(
        "/api/agents/test_agent/files/create",
        json={"path": "existing.txt", "content": "first"}
    )
    response = await client.post(
        "/api/agents/test_agent/files/create",
        json={"path": "existing.txt", "content": "second"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_files_with_subdirectories(client: AsyncClient):
    """Test listing files in subdirectories."""
    await client.post("/api/agents", json={"agent_id": "test_agent"})
    await client.post(
        "/api/agents/test_agent/files/write",
        json={"path": "subdir/file1.txt", "content": "1"}
    )
    await client.post(
        "/api/agents/test_agent/files/write",
        json={"path": "subdir/file2.txt", "content": "2"}
    )
    response = await client.get("/api/agents/test_agent/files", params={"path": "subdir"})
    assert response.status_code == 200
    data = response.json()
    names = {item["name"] for item in data["items"]}
    assert names == {"file1.txt", "file2.txt"}


@pytest.mark.asyncio
async def test_oversized_file_rejected(client: AsyncClient):
    """Test that oversized files are rejected."""
    await client.post("/api/agents", json={"agent_id": "test_agent"})
    large_content = "x" * (11 * 1024 * 1024)  # 11 MB
    response = await client.post(
        "/api/agents/test_agent/files/write",
        json={"path": "large.txt", "content": large_content}
    )
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_invalid_agent_id_rejected(client: AsyncClient):
    """Test that invalid agent IDs are rejected."""
    # Path traversal in agent_id - rejected by pattern validation
    response = await client.post("/api/agents", json={"agent_id": "../evil"})
    assert response.status_code == 422

    # Special characters - rejected by pattern validation
    response = await client.post("/api/agents", json={"agent_id": "agent@evil"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_agents(client: AsyncClient):
    """Test listing all agents."""
    # Use unique agent IDs to avoid conflicts with other tests
    await client.post("/api/agents", json={"agent_id": "list_test_1"})
    await client.post("/api/agents", json={"agent_id": "list_test_2"})

    response = await client.get("/api/agents")
    assert response.status_code == 200
    data = response.json()
    agent_ids = {a["agent_id"] for a in data}
    assert "list_test_1" in agent_ids
    assert "list_test_2" in agent_ids

