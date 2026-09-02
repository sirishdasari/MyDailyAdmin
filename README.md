# MyDaily MCP v2.1

MCP Python SDK v2 server for the existing MyDaily Appwrite schema.

## Canonical user relationship

The Appwrite Authentication user's `$id` is the canonical user ID.

It is stored as:

- `profiles.userId`
- `projects.userId`
- `tasks.userId`

Therefore:

`Appwrite Users.$id == profiles.userId == projects.userId == tasks.userId`

Tasks additionally use:

`tasks.projectId == projects.$id`

## Actual tables

### tasks

`$id, userId, projectId, sectionId, parentId, content, description, labelIds, priority, order, dayOrder, isCompleted, completedAt, dueDate, dueString, dueTimezone, dueIsRecurring, duration, durationUnit, noteCount, postponedCount, assignedByUid, responsibleUid, $createdAt, $updatedAt`

### projects

`$id, userId, name, color, icon, viewStyle, parentId, isFavorite, isArchived, order, $createdAt, $updatedAt`

### profiles

`$id, userId, displayName, avatarUrl, timezone, weekStartDay, theme, defaultProjectId, onboardingComplete, $createdAt, $updatedAt`

## Environment variables

```env
APPWRITE_ENDPOINT=https://cloud.appwrite.io/v1
APPWRITE_PROJECT_ID=your_project_id
APPWRITE_API_KEY=your_server_api_key
APPWRITE_DATABASE_ID=your_database_id

APPWRITE_TASKS_TABLE_ID=tasks
APPWRITE_PROJECTS_TABLE_ID=projects
APPWRITE_PROFILES_TABLE_ID=profiles
```

The values after `*_TABLE_ID` are your actual Appwrite table IDs. If the IDs are different from the table names, put the IDs there.

## User lookup flow

Example:

"Show Rahul's tasks"

1. `search_users("Rahul")`
2. Resolve Rahul's Appwrite Auth `$id`.
3. `list_tasks(user_id="<Auth $id>")`
4. Query `tasks.userId == <Auth $id>`.

For projects:

`projects.userId == Auth $id`

For profile:

`profiles.userId == Auth $id`

## MCP tools

### Users

- `list_users`
- `search_users`
- `get_user`

### Profiles

- `get_profile`
- `update_profile`

### Projects

- `list_projects`
- `get_project`
- `create_project`
- `update_project`
- `delete_project`

### Tasks

- `add_task`
- `list_tasks`
- `get_task`
- `update_task`
- `complete_task`
- `delete_task`

## Install

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Fill `.env`, then test:

```powershell
python test_appwrite.py
```

Run the MCP:

```powershell
python app.py
```

Endpoint:

`http://127.0.0.1:8000/mcp`

## Important

This project intentionally uses a server-side Appwrite API key and explicit `user_id`.

Do not expose the MCP publicly without considering caller authentication/authorization. The task and project service also verifies ownership before get/update/delete operations.
