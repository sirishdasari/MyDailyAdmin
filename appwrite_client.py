import os
from appwrite.client import Client
from appwrite.services.databases import Databases
from dotenv import load_dotenv

load_dotenv()

COLLECTIONS = {
    "profiles": "profiles",
    "projects": "projects",
    "sections": "sections",
    "labels": "labels",
    "lists": "lists",
    "tasks": "tasks",
    "comments": "comments",
}

_client = None
_databases = None
_database_id = None

def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

def get_database_id() -> str:
    global _database_id
    if _database_id is None:
        _database_id = _require_env("APPWRITE_DATABASE_ID")
    return _database_id

def get_databases() -> Databases:
    global _client, _databases
    if _databases is None:
        _client = Client()
        _client.set_endpoint(_require_env("APPWRITE_ENDPOINT"))
        _client.set_project(_require_env("APPWRITE_PROJECT_ID"))
        _client.set_key(_require_env("APPWRITE_API_KEY"))
        _databases = Databases(_client)
    return _databases
