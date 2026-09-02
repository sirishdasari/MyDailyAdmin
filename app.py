import os
from typing import Any
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from appwrite_client import COLLECTIONS, get_database_id, get_databases
from appwrite.query import Query

port = int(os.environ.get("PORT", "8000"))

mcp = FastMCP(
    "MyDailyMCP",
    host="0.0.0.0",
    port=port,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

def _doc_to_dict(document: Any) -> dict[str, Any]:
    if hasattr(document, "model_dump"):
        return document.model_dump()
    return dict(document)

def _list(collection: str, queries: list[str]) -> dict[str, Any]:
    result = get_databases().list_documents(
        database_id=get_database_id(),
        collection_id=COLLECTIONS[collection],
        queries=queries,
    )
    data = _doc_to_dict(result)
    data["documents"] = [_doc_to_dict(d) for d in data.get("documents", [])]
    return data

@mcp.tool()
def list_tasks(
    completed: bool | None = None,
    project_id: str | None = None,
    user_id: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> dict[str, Any]:
    """Admin-level task listing. No authenticated user is assumed.
    Omit user_id to list tasks across all users; provide it only when filtering."""
    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))
    q = [Query.order_asc("dueDate")]
    if completed is not None:
        q.append(Query.equal("isCompleted", completed))
    if project_id is not None:
        q.append(Query.equal("projectId", project_id))
    if user_id is not None:
        q.append(Query.equal("userId", user_id))
    q += [Query.limit(limit), Query.offset(offset)]
    return _list("tasks", q)

@mcp.tool()
def list_projects(
    archived: bool | None = None,
    user_id: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> dict[str, Any]:
    """Admin-level project listing. Omit user_id to list projects across all users."""
    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))
    q = [Query.order_asc("order")]
    if archived is not None:
        q.append(Query.equal("isArchived", archived))
    if user_id is not None:
        q.append(Query.equal("userId", user_id))
    q += [Query.limit(limit), Query.offset(offset)]
    return _list("projects", q)

@mcp.tool()
def list_profiles(limit: int = 200, offset: int = 0) -> dict[str, Any]:
    """Admin-level profile listing."""
    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))
    return _list("profiles", [
        Query.order_asc("displayName"),
        Query.limit(limit),
        Query.offset(offset),
    ])

@mcp.tool()
def get_task(task_id: str) -> dict[str, Any]:
    """Get any task by Appwrite document ID."""
    return _doc_to_dict(get_databases().get_document(
        database_id=get_database_id(),
        collection_id=COLLECTIONS["tasks"],
        document_id=task_id,
    ))

@mcp.tool()
def get_profile(user_id: str) -> dict[str, Any] | None:
    """Get any profile by MyDaily/Appwrite user ID."""
    result = _list("profiles", [Query.equal("userId", user_id), Query.limit(1)])
    docs = result.get("documents", [])
    return docs[0] if docs else None

@mcp.tool()
def search_users_by_name(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search MyDaily profiles by display name."""
    if not query.strip():
        return []
    result = _list("profiles", [
        Query.search("displayName", query),
        Query.is_not_null("displayName"),
        Query.limit(max(1, min(int(limit), 100))),
    ])
    return [
        {"user_id": d["userId"], "display_name": d["displayName"]}
        for d in result.get("documents", [])
        if d.get("displayName")
    ]

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
