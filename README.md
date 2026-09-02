# MyDaily MCP — Admin Data Access

This version intentionally does NOT authenticate a ChatGPT user and does NOT
derive a user from the MCP session.

It uses one server-side Appwrite API key and exposes read-oriented admin tools
that can query data across the MyDaily database.

## Included tools

- `list_tasks` — all tasks by default; optional `user_id`, project and completion filters
- `list_projects` — all projects by default; optional filters
- `list_profiles` — all profiles
- `get_task` — any task by document ID
- `get_profile` — any profile by MyDaily/Appwrite user ID
- `search_users_by_name` — profile search

## Environment variables

Set these in Render or your local environment:

APPWRITE_ENDPOINT=https://fra.cloud.appwrite.io/v1
APPWRITE_PROJECT_ID=6a7a2ab20015ba95285e
APPWRITE_DATABASE_ID=<your database id>
APPWRITE_API_KEY=<your server API key>

Do NOT commit `.env` or the API key to GitHub.

## Run locally

pip install -r requirements.txt
python app.py

The server uses Streamable HTTP.

## Important security note

This is deliberately admin-level access. Anyone who can call this MCP can
potentially read data from all users that the API key can read. Do not expose
this endpoint publicly without authentication/authorization if the data is
private.

This package does not implement ChatGPT OAuth because you explicitly requested
an admin/API-key model rather than per-user authentication.
