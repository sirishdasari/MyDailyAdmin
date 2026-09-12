import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from appwrite.client import Client
from appwrite.services.tables_db import TablesDB
from appwrite.id import ID
from appwrite.query import Query

from appwrite_compat import flatten_row, get_list_items, normalize_limit

load_dotenv()


class GuitarPracticeService:
    """Shared/open guitar practice tables.

    Guitar practice is intentionally independent from MyDaily user data.
    It uses the public Appwrite client configuration below and does not
    require an Appwrite API key or user ID.

    dailyPracticeTime is action-owned practice telemetry and is never written
    or changed by the MCP CRUD operations.
    """

    ALLOWED_LEVELS = {"Beginner", "Intermediate", "Advanced"}

    def __init__(self):
        client = Client()
        client.set_endpoint(
            os.environ.get(
                "APPWRITE_GUITAR_ENDPOINT",
                "https://fra.cloud.appwrite.io/v1",
            )
        )
        client.set_project(
            os.environ.get("APPWRITE_GUITAR_PROJECT_ID", "6a9e3d930019d4da40b4")
        )

        # Guitar tables are public/open. Do not use the server API key here.
        self.db = TablesDB(client)
        self.database_id = os.environ.get(
            "APPWRITE_GUITAR_DATABASE_ID",
            "6aa4ebf0000a4f853d1b",
        )
        self.table_id = os.environ.get(
            "APPWRITE_GUITAR_PRACTICE_TABLE_ID",
            "guitarpractice",
        )

    def _query_practice(self, completed=None, limit=25):
        row_limit = normalize_limit(limit, default=25)
        queries = [Query.order_desc("$createdAt"), Query.limit(row_limit)]
        if completed is not None:
            queries.insert(1, Query.equal("completed", completed))
        result = self.db.list_rows(
            database_id=self.database_id,
            table_id=self.table_id,
            queries=queries,
            total=False,
        )
        return get_list_items(result, "rows")

    def _get(self, practice_id):
        return flatten_row(self.db.get_row(
            database_id=self.database_id,
            table_id=self.table_id,
            row_id=practice_id,
        ))

    def _validate_level(self, level):
        if level not in self.ALLOWED_LEVELS:
            raise ValueError("level must be one of: Beginner, Intermediate, Advanced")

    def _create_row(self, data):
        """Create a row with diagnostics so deployment failures are visible."""
        print(
            "[guitar] create_practice: "
            f"endpoint={os.environ.get('APPWRITE_GUITAR_ENDPOINT', 'default')} "
            f"project={os.environ.get('APPWRITE_GUITAR_PROJECT_ID', 'default')} "
            f"database={self.database_id} table={self.table_id}"
        )
        print(f"[guitar] create_practice data={data}")
        try:
            row = self.db.create_row(
                database_id=self.database_id,
                table_id=self.table_id,
                row_id=ID.unique(),
                data=data,
            )
            print("[guitar] create_practice: Appwrite create_row succeeded")
            return row
        except Exception as exc:
            print(
                "[guitar] create_practice FAILED: "
                f"{type(exc).__name__}: {exc}"
            )
            raise

    def add_practice(self, session_name, completed=False, suggested_time="", duration=0,
                     description="", category="", level="Beginner", link=""):
        self._validate_level(level)
        data = {
            "sessionName": session_name,
            "completed": completed,
            "suggestedTime": suggested_time or "",
            "duration": duration,
            "description": description or "",
            "category": category or "",
            "level": level,
            "link": link or "",
        }
        # dailyPracticeTime is intentionally omitted. Appwrite keeps its
        # default value (0), and practice actions are responsible for updating it.
        return flatten_row(self._create_row(data))

    def list_practice(self, completed=None, limit=25):
        practices = self._query_practice(completed=completed, limit=limit)
        return {
            "documentType": "guitarPractice",
            "filters": {"completed": completed, "limit": normalize_limit(limit, default=25)},
            "practiceCount": len(practices),
            "practices": practices,
        }

    def get_practice(self, practice_id):
        return self._get(practice_id)

    def update_practice(self, practice_id, session_name="", completed=None, suggested_time="",
                        duration=None, description="", category="", level=None, link=None):
        self._get(practice_id)
        data = {}
        values = {
            "sessionName": session_name,
            "suggestedTime": suggested_time,
            "description": description,
            "category": category,
        }
        for key, value in values.items():
            if value != "":
                data[key] = value
        if level is not None:
            self._validate_level(level)
            data["level"] = level
        if link is not None:
            data["link"] = link
        if completed is not None:
            data["completed"] = completed
            if completed:
                data["completedAt"] = datetime.now(timezone.utc).isoformat()
        if duration is not None:
            data["duration"] = duration
        # dailyPracticeTime is intentionally never included in update data.
        if not data:
            return self.get_practice(practice_id)
        row = self.db.update_row(
            database_id=self.database_id,
            table_id=self.table_id,
            row_id=practice_id,
            data=data,
        )
        return flatten_row(row)

    def complete_practice(self, practice_id):
        self._get(practice_id)
        row = self.db.update_row(
            database_id=self.database_id,
            table_id=self.table_id,
            row_id=practice_id,
            data={"completed": True, "completedAt": datetime.now(timezone.utc).isoformat()},
        )
        return flatten_row(row)

    def delete_practice(self, practice_id):
        self._get(practice_id)
        self.db.delete_row(
            database_id=self.database_id,
            table_id=self.table_id,
            row_id=practice_id,
        )
        return {"success": True, "practice_id": practice_id}
