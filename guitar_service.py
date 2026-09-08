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
    """guitarPractice table.

    guitarPractice.userId == Appwrite Authentication Users.$id

    Mirrors the existing mcpappwrite guitar service while applying
    MyDaily's explicit user ownership model.
    """

    def __init__(self):
        client = Client()
        client.set_endpoint(os.environ["APPWRITE_ENDPOINT"])
        client.set_project(os.environ["APPWRITE_PROJECT_ID"])
        client.set_key(os.environ["APPWRITE_API_KEY"])

        self.db = TablesDB(client)
        self.database_id = os.environ["APPWRITE_DATABASE_ID"]
        self.table_id = os.environ.get(
            "APPWRITE_GUITAR_PRACTICE_TABLE_ID",
            "guitarPractice",
        )

    def _query_practice(self, user_id, completed=None, limit=25):
        row_limit = normalize_limit(limit, default=25)

        queries = [
            Query.equal("userId", user_id),
            Query.order_desc("$createdAt"),
            Query.limit(row_limit),
        ]

        if completed is not None:
            queries.insert(1, Query.equal("completed", completed))

        result = self.db.list_rows(
            database_id=self.database_id,
            table_id=self.table_id,
            queries=queries,
            total=False,
        )

        return get_list_items(result, "rows")

    def _owned(self, user_id, practice_id):
        practice = flatten_row(
            self.db.get_row(
                database_id=self.database_id,
                table_id=self.table_id,
                row_id=practice_id,
            )
        )

        if practice.get("userId") != user_id:
            raise PermissionError(
                "Guitar practice does not belong to the supplied Auth user $id."
            )

        return practice

    def add_practice(
        self,
        user_id,
        session_name,
        completed=False,
        suggested_time="",
        duration=0,
        description="",
        daily_practice_time=0,
    ):
        data = {
            "userId": user_id,
            "sessionName": session_name,
            "completed": completed,
            "suggestedTime": suggested_time or "",
            "duration": duration,
            "description": description or "",
            "dailyPracticeTime": daily_practice_time,
        }

        row = self.db.create_row(
            database_id=self.database_id,
            table_id=self.table_id,
            row_id=ID.unique(),
            data=data,
        )

        return flatten_row(row)

    def list_practice(self, user_id, completed=None, limit=25):
        practices = self._query_practice(
            user_id=user_id,
            completed=completed,
            limit=limit,
        )

        return {
            "documentType": "guitarPractice",
            "userId": user_id,
            "filters": {
                "completed": completed,
                "limit": normalize_limit(limit, default=25),
            },
            "practiceCount": len(practices),
            "practices": practices,
        }

    def get_practice(self, user_id, practice_id):
        return self._owned(user_id, practice_id)

    def update_practice(
        self,
        user_id,
        practice_id,
        session_name="",
        completed=None,
        suggested_time="",
        duration=None,
        description="",
        daily_practice_time=None,
    ):
        self._owned(user_id, practice_id)
        data = {}

        values = {
            "sessionName": session_name,
            "suggestedTime": suggested_time,
            "description": description,
        }

        for key, value in values.items():
            if value != "":
                data[key] = value

        if completed is not None:
            data["completed"] = completed
            if completed:
                data["completedAt"] = datetime.now(timezone.utc).isoformat()

        if duration is not None:
            data["duration"] = duration

        if daily_practice_time is not None:
            data["dailyPracticeTime"] = daily_practice_time

        if not data:
            return self.get_practice(user_id, practice_id)

        row = self.db.update_row(
            database_id=self.database_id,
            table_id=self.table_id,
            row_id=practice_id,
            data=data,
        )

        return flatten_row(row)

    def complete_practice(self, user_id, practice_id):
        self._owned(user_id, practice_id)

        row = self.db.update_row(
            database_id=self.database_id,
            table_id=self.table_id,
            row_id=practice_id,
            data={
                "completed": True,
                "completedAt": datetime.now(timezone.utc).isoformat(),
            },
        )

        return flatten_row(row)

    def delete_practice(self, user_id, practice_id):
        self._owned(user_id, practice_id)

        self.db.delete_row(
            database_id=self.database_id,
            table_id=self.table_id,
            row_id=practice_id,
        )

        return {
            "success": True,
            "practice_id": practice_id,
        }
