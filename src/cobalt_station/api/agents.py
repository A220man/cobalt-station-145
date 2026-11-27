"""Agent API endpoints with workspace isolation."""
from typing import cast

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from cobalt_station.core.workspace import (
    PathTraversalError,
    WorkspaceNotFoundError,
    WorkspacePermissionError,
    ensure_workspace_exists,
    list_agent_workspaces,
)
from cobalt_station.tools.file_ops import (
    FileNotFoundError,
    FileOperationError,
    FileTooLargeError,
    create_file,
    delete_file,
    get_workspace_info,
    list_files,
    read_file,
    write_file,
)



class AgentStatsResponse(BaseModel):
    """Agent workspace statistics."""
    agent_id: str
    workspace_path: str
    file_count: int
    directory_count: int
    total_size_bytes: int
    created_at: float = 0.0
router = APIRouter(prefix="/api/agents", tags=["agents"])


class AgentCreate(BaseModel):
    """Agent creation request."""
    agent_id: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")


class AgentResponse(BaseModel):
    """Agent response."""
    agent_id: str
    workspace_path: str
    file_count: int


class FileReadResponse(BaseModel):
    """File read response."""
    path: str
    content: str


class FileWriteRequest(BaseModel):
    """File write request."""
    path: str = Field(..., min_length=1)
    content: str


class FileCreateRequest(BaseModel):
    """File create request."""
    path: str = Field(..., min_length=1)
    content: str = ""


class FileListResponse(BaseModel):
    """File list response."""
    path: str
    items: list[dict[str, object]]


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: str


def _map_workspace_error(e: Exception) -> HTTPException:
    """Map workspace errors to HTTP exceptions."""
    if isinstance(e, PathTraversalError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "path_traversal", "detail": str(e)},
        )
    if isinstance(e, WorkspacePermissionError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "workspace_permission", "detail": str(e)},
        )
    if isinstance(e, WorkspaceNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "workspace_not_found", "detail": str(e)},
        )
    if isinstance(e, FileNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "file_not_found", "detail": str(e)},
        )
    if isinstance(e, FileTooLargeError):
        return HTTPException(
            status_code=413,
            detail={"error": "file_too_large", "detail": str(e)},
        )
    if isinstance(e, FileOperationError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "file_operation", "detail": str(e)},
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"error": "internal", "detail": "Internal server error"},
    )


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(agent_data: AgentCreate) -> AgentResponse:
    """Create a new agent with its own workspace."""
    try:
        workspace = ensure_workspace_exists(agent_data.agent_id)
        return AgentResponse(
            agent_id=agent_data.agent_id,
            workspace_path=str(workspace),
            file_count=0,
        )
    except PathTraversalError as e:
        raise _map_workspace_error(e)


@router.get("", response_model=list[AgentResponse])
async def list_agents() -> list[AgentResponse]:
    """List all agents with workspaces."""
    agent_ids = list_agent_workspaces()
    result = []
    for agent_id in agent_ids:
        info = get_workspace_info(agent_id)
        result.append(AgentResponse(
            agent_id=cast(str, info["agent_id"]),
            workspace_path=cast(str, info["workspace_path"]),
            file_count=cast(int, info["file_count"]),
        ))
    return result


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str) -> AgentResponse:
    """Get agent workspace info."""
    try:
        info = get_workspace_info(agent_id)
        return AgentResponse(
            agent_id=cast(str, info["agent_id"]),
            workspace_path=cast(str, info["workspace_path"]),
            file_count=cast(int, info["file_count"]),
        )
    except (WorkspaceNotFoundError, PathTraversalError) as e:
        raise _map_workspace_error(e)


@router.get("/{agent_id}/files", response_model=FileListResponse)
async def list_agent_files(agent_id: str, path: str = ".") -> FileListResponse:
    """List files in agent's workspace directory."""
    try:
        ensure_workspace_exists(agent_id)
        items = list_files(agent_id, path)
        return FileListResponse(path=path, items=items)
    except (WorkspacePermissionError, PathTraversalError, FileNotFoundError, FileOperationError) as e:
        raise _map_workspace_error(e)


@router.get("/{agent_id}/files/read", response_model=FileReadResponse)
async def read_agent_file(agent_id: str, path: str) -> FileReadResponse:
    """Read a file from agent's workspace."""
    try:
        ensure_workspace_exists(agent_id)
        content = read_file(agent_id, path)
        return FileReadResponse(path=path, content=content)
    except (WorkspacePermissionError, PathTraversalError, FileNotFoundError, FileTooLargeError) as e:
        raise _map_workspace_error(e)


@router.post("/{agent_id}/files/write", response_model=FileReadResponse)
async def write_agent_file(agent_id: str, request: FileWriteRequest) -> FileReadResponse:
    """Write a file to agent's workspace (create or overwrite)."""
    try:
        ensure_workspace_exists(agent_id)
        write_file(agent_id, request.path, request.content)
        content = read_file(agent_id, request.path)
        return FileReadResponse(path=request.path, content=content)
    except (WorkspacePermissionError, PathTraversalError, FileTooLargeError) as e:
        raise _map_workspace_error(e)


@router.post("/{agent_id}/files/create", response_model=FileReadResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_file(agent_id: str, request: FileCreateRequest) -> FileReadResponse:
    """Create a new file in agent's workspace."""
    try:
        ensure_workspace_exists(agent_id)
        create_file(agent_id, request.path, request.content)
        content = read_file(agent_id, request.path)
        return FileReadResponse(path=request.path, content=content)
    except (WorkspacePermissionError, PathTraversalError, FileOperationError, FileTooLargeError) as e:
        raise _map_workspace_error(e)


@router.delete("/{agent_id}/files", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent_file(agent_id: str, path: str) -> None:
    """Delete a file from agent's workspace."""
    try:
        ensure_workspace_exists(agent_id)
        delete_file(agent_id, path)
    except (WorkspacePermissionError, PathTraversalError, FileNotFoundError, FileOperationError) as e:
        raise _map_workspace_error(e)

@router.get("/{agent_id}/stats", response_model=AgentStatsResponse)
async def get_agent_stats(agent_id: str) -> AgentStatsResponse:
    """Get agent workspace statistics."""
    try:
        workspace = ensure_workspace_exists(agent_id)
        info = get_workspace_info(agent_id)
        # Get directory count and total size
        from pathlib import Path
        import os
        workspaces_root = Path("./workspaces").resolve()
        agent_workspace = workspaces_root / agent_id
        
        dir_count = 0
        total_size = 0
        if agent_workspace.exists():
            for root, dirs, files in os.walk(agent_workspace):
                dir_count += len(dirs)
                for f in files:
                    fp = Path(root) / f
                    if fp.exists():
                        total_size += fp.stat().st_size
        
        return AgentStatsResponse(
            agent_id=agent_id,
            workspace_path=str(workspace),
            file_count=info["file_count"],
            directory_count=dir_count,
            total_size_bytes=total_size,
        )
    except (WorkspaceNotFoundError, PathTraversalError) as e:
        raise _map_workspace_error(e)



    """Agent workspace statistics."""
    agent_id: str
    workspace_path: str
    file_count: int
    directory_count: int
    total_size_bytes: int
    created_at: float = 0.0
