import os
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from user_service import UserService
from todo_service import TodoService
from project_service import ProjectService
from profile_service import ProfileService
from guitar_service import GuitarPracticeService

mcp = MCPServer(
    "MyDailyMCP",
    version="2.2.0",
    instructions=(
        "MyDaily MCP uses Appwrite Auth Users.$id as the canonical user ID. "
        "The profiles, projects, tasks and guitarPractice tables store this value in userId. "
        "Tasks additionally reference projects through projectId."
    ),
)

_services = {}


def services():
    if not _services:
        _services["users"] = UserService()
        _services["tasks"] = TodoService()
        _services["projects"] = ProjectService()
        _services["profiles"] = ProfileService()
        _services["guitar"] = GuitarPracticeService()
    return _services


# ---------------- Users ----------------

@mcp.tool()
def list_users(limit: int = 25):
    """List Appwrite Auth users. id is the Appwrite Users.$id."""
    return services()["users"].list_users(limit)


@mcp.tool()
def search_users(query: str, limit: int = 25):
    """Search Appwrite Auth users by name/email."""
    return services()["users"].search_users(query, limit)


@mcp.tool()
def get_user(user_id: str):
    """Get an Appwrite Auth user by $id."""
    return services()["users"].get_user(user_id)


# ---------------- Profiles ----------------

@mcp.tool()
def get_profile(user_id: str):
    """Get the profile where profiles.userId equals the Appwrite Auth $id."""
    return services()["profiles"].get_profile(user_id)


@mcp.tool()
def update_profile(
    user_id: str,
    display_name: str = "",
    avatar_url: str = "",
    timezone: str = "",
    week_start_day: int | None = None,
    theme: str = "",
    default_project_id: str = "",
    onboarding_complete: bool | None = None,
):
    """Update a user's profile."""
    return services()["profiles"].update_profile(
        user_id, display_name, avatar_url, timezone,
        week_start_day, theme, default_project_id, onboarding_complete
    )


# ---------------- Projects ----------------

@mcp.tool()
def list_projects(
    user_id: str,
    include_archived: bool = False,
    limit: int = 100,
):
    """List projects belonging to an Appwrite Auth user."""
    return services()["projects"].list_projects(
        user_id, include_archived, limit
    )


@mcp.tool()
def get_project(user_id: str, project_id: str):
    """Get a project owned by the supplied Appwrite Auth user."""
    return services()["projects"].get_project(user_id, project_id)


@mcp.tool()
def create_project(
    user_id: str,
    name: str,
    color: str = "",
    icon: str = "",
    view_style: str = "",
    parent_id: str = "",
    is_favorite: bool = False,
    is_archived: bool = False,
    order: float = 0,
):
    """Create a project. projects.userId is set to the Appwrite Auth $id."""
    return services()["projects"].create_project(
        user_id, name, color, icon, view_style, parent_id,
        is_favorite, is_archived, order
    )


@mcp.tool()
def update_project(
    user_id: str,
    project_id: str,
    name: str = "",
    color: str = "",
    icon: str = "",
    view_style: str = "",
    parent_id: str = "",
    is_favorite: bool | None = None,
    is_archived: bool | None = None,
    order: float | None = None,
):
    """Update a project owned by the supplied Appwrite Auth user."""
    return services()["projects"].update_project(
        user_id, project_id, name, color, icon, view_style,
        parent_id, is_favorite, is_archived, order
    )


@mcp.tool()
def delete_project(user_id: str, project_id: str):
    """Delete a project owned by the supplied Appwrite Auth user."""
    return services()["projects"].delete_project(user_id, project_id)


# ---------------- Tasks ----------------

@mcp.tool()
def add_task(
    user_id: str,
    content: str,
    project_id: str = "",
    section_id: str = "",
    parent_id: str = "",
    description: str = "",
    label_ids: list[str] | None = None,
    priority: int = 4,
    order: float = 0,
    day_order: float = 0,
    due_date: str = "",
    due_string: str = "",
    due_timezone: str = "",
    due_is_recurring: bool = False,
    duration: int | None = None,
    duration_unit: str = "",
    assigned_by_uid: str = "",
    responsible_uid: str = "",
):
    """Create a task. tasks.userId is set to the Appwrite Auth $id."""
    return services()["tasks"].add_task(
        user_id, content, project_id, section_id, parent_id, description,
        label_ids, priority, order, day_order, due_date, due_string,
        due_timezone, due_is_recurring, duration, duration_unit,
        assigned_by_uid, responsible_uid
    )


@mcp.tool()
def list_tasks(
    user_id: str,
    project_id: str = "",
    section_id: str = "",
    is_completed: bool | None = None,
    priority: int | None = None,
    due_date: str = "",
    limit: int = 100,
):
    """Return one document containing up to `limit` tasks for a user.

    The response is a single object with a `tasks` array. Use the default limit
    of 100 unless the caller explicitly asks for fewer tasks.
    """
    return services()["tasks"].list_tasks(
        user_id, project_id, section_id, is_completed,
        priority, due_date, limit
    )


@mcp.tool()
def list_project_tasks(
    user_id: str,
    include_archived_projects: bool = False,
    is_completed: bool | None = None,
    limit_per_project: int = 100,
):
    """Return one document containing projects and matching tasks for each project.

    Use this when the user asks for tasks grouped by project. The response is a
    single object with a `projects` array, and each project contains a `tasks`
    array with up to `limit_per_project` tasks.
    """
    projects = services()["projects"].list_projects(
        user_id=user_id,
        include_archived=include_archived_projects,
        limit=100,
    )
    project_ids = [project.get("$id") or project.get("id") for project in projects]
    tasks_by_project = services()["tasks"].list_tasks_by_projects(
        user_id=user_id,
        project_ids=[project_id for project_id in project_ids if project_id],
        is_completed=is_completed,
        limit_per_project=limit_per_project,
    )

    project_documents = [
        {
            **project,
            "tasks": tasks_by_project.get(project.get("$id") or project.get("id"), []),
        }
        for project in projects
    ]

    return {
        "documentType": "projectTasks",
        "userId": user_id,
        "filters": {
            "includeArchivedProjects": include_archived_projects,
            "isCompleted": is_completed,
            "limitPerProject": limit_per_project,
        },
        "projectCount": len(project_documents),
        "taskCount": sum(len(project["tasks"]) for project in project_documents),
        "projects": project_documents,
    }


@mcp.tool()
def get_task(user_id: str, task_id: str):
    """Get a task only if tasks.userId matches the supplied Auth $id."""
    return services()["tasks"].get_task(user_id, task_id)


@mcp.tool()
def update_task(
    user_id: str,
    task_id: str,
    content: str = "",
    description: str = "",
    project_id: str = "",
    section_id: str = "",
    parent_id: str = "",
    label_ids: list[str] | None = None,
    priority: int | None = None,
    order: float | None = None,
    day_order: float | None = None,
    due_date: str = "",
    due_string: str = "",
    due_timezone: str = "",
    due_is_recurring: bool | None = None,
    duration: int | None = None,
    duration_unit: str = "",
    assigned_by_uid: str = "",
    responsible_uid: str = "",
    is_completed: bool | None = None,
):
    """Update a task owned by the supplied Appwrite Auth user."""
    return services()["tasks"].update_task(
        user_id, task_id, content, description, project_id, section_id,
        parent_id, label_ids, priority, order, day_order, due_date,
        due_string, due_timezone, due_is_recurring, duration,
        duration_unit, assigned_by_uid, responsible_uid, is_completed
    )


@mcp.tool()
def complete_task(user_id: str, task_id: str):
    """Mark a task complete."""
    return services()["tasks"].complete_task(user_id, task_id)


@mcp.tool()
def delete_task(user_id: str, task_id: str):
    """Delete a task owned by the supplied Appwrite Auth user."""
    return services()["tasks"].delete_task(user_id, task_id)



# ---------------- Guitar Practice ----------------

@mcp.tool()
def add_guitar_practice(
    user_id: str,
    session_name: str,
    completed: bool = False,
    suggested_time: str = "",
    duration: int = 0,
    description: str = "",
    daily_practice_time: int = 0,
):
    """Create a guitar practice session for an Appwrite Auth user."""
    return services()["guitar"].add_practice(
        user_id=user_id,
        session_name=session_name,
        completed=completed,
        suggested_time=suggested_time,
        duration=duration,
        description=description,
        daily_practice_time=daily_practice_time,
    )


@mcp.tool()
def list_guitar_practice(
    user_id: str,
    completed: bool | None = None,
    limit: int = 25,
):
    """List guitar practice sessions belonging to an Appwrite Auth user."""
    return services()["guitar"].list_practice(
        user_id=user_id,
        completed=completed,
        limit=limit,
    )


@mcp.tool()
def get_guitar_practice(user_id: str, practice_id: str):
    """Get a guitar practice session owned by the supplied Auth user."""
    return services()["guitar"].get_practice(user_id, practice_id)


@mcp.tool()
def update_guitar_practice(
    user_id: str,
    practice_id: str,
    session_name: str = "",
    completed: bool | None = None,
    suggested_time: str = "",
    duration: int | None = None,
    description: str = "",
    daily_practice_time: int | None = None,
):
    """Update a guitar practice session owned by the supplied Auth user."""
    return services()["guitar"].update_practice(
        user_id=user_id,
        practice_id=practice_id,
        session_name=session_name,
        completed=completed,
        suggested_time=suggested_time,
        duration=duration,
        description=description,
        daily_practice_time=daily_practice_time,
    )


@mcp.tool()
def complete_guitar_practice(user_id: str, practice_id: str):
    """Mark a guitar practice session complete."""
    return services()["guitar"].complete_practice(user_id, practice_id)


@mcp.tool()
def delete_guitar_practice(user_id: str, practice_id: str):
    """Delete a guitar practice session owned by the supplied Auth user."""
    return services()["guitar"].delete_practice(user_id, practice_id)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))

    allowed_hosts = [
        x.strip() for x in os.environ.get("MCP_ALLOWED_HOSTS", "").split(",")
        if x.strip()
    ]
    allowed_origins = [
        x.strip() for x in os.environ.get("MCP_ALLOWED_ORIGINS", "").split(",")
        if x.strip()
    ]

    kwargs = {
        "transport": "streamable-http",
        "host": "0.0.0.0",
        "port": port,
        "streamable_http_path": "/mcp",
        "stateless_http": True,
        "json_response": True,
    }

    if allowed_hosts or allowed_origins:
        kwargs["transport_security"] = TransportSecuritySettings(
            allowed_hosts=allowed_hosts or None,
            allowed_origins=allowed_origins or None,
        )

    mcp.run(**kwargs)
