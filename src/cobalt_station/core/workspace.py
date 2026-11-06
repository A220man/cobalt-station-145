"""Workspace isolation for agents."""
from pathlib import Path
from typing import Final

WORKSPACES_ROOT: Final[Path] = Path("./workspaces").resolve()


class WorkspaceError(Exception):
    """Base exception for workspace errors."""

    pass


class WorkspacePermissionError(WorkspaceError):
    """Raised when an agent tries to access another agent's workspace."""

    pass


class PathTraversalError(WorkspaceError):
    """Raised when a path traversal attempt is detected."""

    pass


class WorkspaceNotFoundError(WorkspaceError):
    """Raised when an agent's workspace doesn't exist."""

    pass


def get_workspace_root() -> Path:
    """Get the root workspaces directory."""
    WORKSPACES_ROOT.mkdir(parents=True, exist_ok=True)
    return WORKSPACES_ROOT


def get_agent_workspace(agent_id: str) -> Path:
    """Get the workspace directory for a specific agent.

    Args:
        agent_id: The agent's unique identifier.

    Returns:
        Absolute path to the agent's workspace directory.
    """
    workspace_root = get_workspace_root()
    agent_workspace = (workspace_root / agent_id).resolve()

    # Ensure the workspace is within the workspaces root
    try:
        agent_workspace.relative_to(workspace_root)
    except ValueError:
        raise PathTraversalError(f"Invalid agent_id: {agent_id}")

    agent_workspace.mkdir(parents=True, exist_ok=True)
    return agent_workspace


def validate_path_within_workspace(agent_id: str, target_path: str | Path) -> Path:
    """Validate that a target path is within the agent's workspace.

    Args:
        agent_id: The agent's unique identifier.
        target_path: The path to validate (relative or absolute).

    Returns:
        Resolved absolute path within the workspace.

    Raises:
        WorkspacePermissionError: If the path is outside the agent's workspace.
        PathTraversalError: If path traversal is attempted.
    """
    workspace = get_agent_workspace(agent_id)

    # Resolve the target path relative to workspace
    if isinstance(target_path, str):
        target_path = Path(target_path)

    # If target_path is absolute, use it directly; otherwise resolve relative to workspace
    if target_path.is_absolute():
        resolved_target = target_path.resolve()
    else:
        resolved_target = (workspace / target_path).resolve()

    # Check for path traversal - ensure resolved path is within workspace
    try:
        resolved_target.relative_to(workspace)
    except ValueError:
        raise WorkspacePermissionError(
            f"Agent {agent_id} cannot access path outside its workspace: {target_path}"
        )

    return resolved_target


def ensure_workspace_exists(agent_id: str) -> Path:
    """Ensure an agent's workspace exists, creating it if necessary.

    Args:
        agent_id: The agent's unique identifier.

    Returns:
        Absolute path to the agent's workspace directory.
    """
    return get_agent_workspace(agent_id)


def list_agent_workspaces() -> list[str]:
    """List all agent workspace directories.

    Returns:
        List of agent IDs that have workspaces.
    """
    workspace_root = get_workspace_root()
    if not workspace_root.exists():
        return []

    return [
        d.name
        for d in workspace_root.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ]

