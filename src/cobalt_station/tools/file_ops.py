"""File operations for agent workspaces with isolation enforcement."""
from typing import Final

from cobalt_station.core.workspace import (
    ensure_workspace_exists,
    validate_path_within_workspace,
)

MAX_FILE_SIZE: Final[int] = 10 * 1024 * 1024  # 10 MB


class FileOperationError(Exception):
    """Base exception for file operation errors."""

    pass


class FileNotFoundError(FileOperationError):
    """Raised when a file doesn't exist."""

    pass


class FileTooLargeError(FileOperationError):
    """Raised when a file exceeds the maximum allowed size."""

    pass


def read_file(agent_id: str, path: str) -> str:
    """Read a file from the agent's workspace.

    Args:
        agent_id: The agent's unique identifier.
        path: Relative path to the file within the workspace.

    Returns:
        File contents as string.

    Raises:
        WorkspacePermissionError: If the path is outside the agent's workspace.
        FileNotFoundError: If the file doesn't exist.
        FileTooLargeError: If the file exceeds the maximum size.
    """
    validated_path = validate_path_within_workspace(agent_id, path)

    if not validated_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not validated_path.is_file():
        raise FileOperationError(f"Path is not a file: {path}")

    file_size = validated_path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        raise FileTooLargeError(f"File size {file_size} exceeds maximum {MAX_FILE_SIZE}")

    return validated_path.read_text(encoding="utf-8")


def write_file(agent_id: str, path: str, content: str) -> None:
    """Write a file to the agent's workspace.

    Args:
        agent_id: The agent's unique identifier.
        path: Relative path to the file within the workspace.
        content: Content to write.

    Raises:
        WorkspacePermissionError: If the path is outside the agent's workspace.
        FileTooLargeError: If the content exceeds the maximum size.
    """
    validated_path = validate_path_within_workspace(agent_id, path)

    if len(content.encode("utf-8")) > MAX_FILE_SIZE:
        raise FileTooLargeError(f"Content size exceeds maximum {MAX_FILE_SIZE}")

    # Ensure parent directory exists
    validated_path.parent.mkdir(parents=True, exist_ok=True)

    validated_path.write_text(content, encoding="utf-8")


def create_file(agent_id: str, path: str, content: str = "") -> None:
    """Create a new file in the agent's workspace.

    Args:
        agent_id: The agent's unique identifier.
        path: Relative path to the file within the workspace.
        content: Initial content (default: empty).

    Raises:
        WorkspacePermissionError: If the path is outside the agent's workspace.
        FileOperationError: If the file already exists.
        FileTooLargeError: If the content exceeds the maximum size.
    """
    validated_path = validate_path_within_workspace(agent_id, path)

    if validated_path.exists():
        raise FileOperationError(f"File already exists: {path}")

    if len(content.encode("utf-8")) > MAX_FILE_SIZE:
        raise FileTooLargeError(f"Content size exceeds maximum {MAX_FILE_SIZE}")

    validated_path.parent.mkdir(parents=True, exist_ok=True)
    validated_path.write_text(content, encoding="utf-8")


def delete_file(agent_id: str, path: str) -> None:
    """Delete a file from the agent's workspace.

    Args:
        agent_id: The agent's unique identifier.
        path: Relative path to the file within the workspace.

    Raises:
        WorkspacePermissionError: If the path is outside the agent's workspace.
        FileNotFoundError: If the file doesn't exist.
    """
    validated_path = validate_path_within_workspace(agent_id, path)

    if not validated_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not validated_path.is_file():
        raise FileOperationError(f"Path is not a file: {path}")

    validated_path.unlink()


def list_files(agent_id: str, path: str = ".") -> list[dict[str, object]]:
    """List files in a directory within the agent's workspace.

    Args:
        agent_id: The agent's unique identifier.
        path: Relative path to the directory (default: workspace root).

    Returns:
        List of file/directory info dicts with keys: name, is_dir, size.

    Raises:
        WorkspacePermissionError: If the path is outside the agent's workspace.
        FileNotFoundError: If the directory doesn't exist.
    """
    validated_path = validate_path_within_workspace(agent_id, path)

    if not validated_path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")

    if not validated_path.is_dir():
        raise FileOperationError(f"Path is not a directory: {path}")

    result = []
    for item in validated_path.iterdir():
        stat = item.stat()
        result.append({
            "name": item.name,
            "is_dir": item.is_dir(),
            "size": stat.st_size if item.is_file() else None,
        })

    return result


def get_workspace_info(agent_id: str) -> dict[str, object]:
    """Get workspace information for an agent.

    Args:
        agent_id: The agent's unique identifier.

    Returns:
        Dict with workspace path and file count.
    """
    workspace = ensure_workspace_exists(agent_id)
    file_count = sum(1 for _ in workspace.rglob("*") if _.is_file())
    return {
        "agent_id": agent_id,
        "workspace_path": str(workspace),
        "file_count": file_count,
    }

