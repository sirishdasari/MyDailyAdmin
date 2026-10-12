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
    GENERAL_PRACTICE_SESSION_ID = "general-practice"

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
        self.practice_records_table_id = os.environ.get(
            "APPWRITE_GUITAR_PRACTICE_RECORDS_TABLE_ID",
            "guitarPracticeRecords",
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

    @staticmethod
    def _record_query_error_is_sort_index_issue(exc):
        """Recognize Appwrite errors where a startedAt index is unavailable."""
        message = str(exc).lower()
        return "index" in message or "startedat" in message or "order" in message

    @staticmethod
    def _validate_practice_date(practice_date):
        if practice_date in (None, ""):
            return
        try:
            parsed = datetime.strptime(practice_date, "%Y-%m-%d")
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "practice_date must be an exact date in YYYY-MM-DD format"
            ) from exc
        if parsed.strftime("%Y-%m-%d") != practice_date:
            raise ValueError(
                "practice_date must be an exact date in YYYY-MM-DD format"
            )

    @staticmethod
    def _record_session_data(session):
        """Expose curriculum details without mixing in its durations/telemetry."""
        if session is None:
            return None
        return {
            "$id": session.get("$id") or session.get("id"),
            "sessionName": session.get("sessionName"),
            "category": session.get("category"),
            "level": session.get("level"),
            "suggestedTime": session.get("suggestedTime"),
            "link": session.get("link"),
        }

    def list_practice_records(
        self, session_id=None, practice_date=None, completed=None, limit=25
    ):
        """Read actual practice records and enrich them with curriculum data.

        guitarPracticeRecords.duration is returned unchanged in seconds.
        This method is read-only and never modifies dailyPracticeTime.
        """
        row_limit = normalize_limit(limit, default=25)
        self._validate_practice_date(practice_date)

        filters = []
        if session_id not in (None, ""):
            filters.append(Query.equal("sessionId", session_id))
        if practice_date not in (None, ""):
            filters.append(Query.equal("practiceDate", practice_date))
        if completed is not None:
            filters.append(Query.equal("completed", completed))

        try:
            result = self.db.list_rows(
                database_id=self.database_id,
                table_id=self.practice_records_table_id,
                queries=[
                    *filters,
                    Query.order_desc("startedAt"),
                    Query.limit(row_limit),
                ],
                total=False,
            )
        except Exception as exc:
            if not self._record_query_error_is_sort_index_issue(exc):
                raise
            # Fallback for deployments lacking a startedAt index. This keeps the
            # query supported and locally sorts the returned page by startedAt.
            # A startedAt index is recommended to ensure globally correct paging.
            result = self.db.list_rows(
                database_id=self.database_id,
                table_id=self.practice_records_table_id,
                queries=[
                    *filters,
                    Query.order_desc("$createdAt"),
                    Query.limit(row_limit),
                ],
                total=False,
            )

        records = get_list_items(result, "rows")
        records.sort(key=lambda row: row.get("startedAt") or "", reverse=True)

        # Read each distinct curriculum row at most once per request.
        linked_ids = {
            record.get("sessionId")
            for record in records
            if record.get("sessionId")
            and record.get("sessionId") != self.GENERAL_PRACTICE_SESSION_ID
        }
        sessions_by_id = {}
        for linked_id in linked_ids:
            try:
                sessions_by_id[linked_id] = self._record_session_data(
                    self._get(linked_id)
                )
            except Exception as exc:
                if self._is_missing_row_error(exc):
                    # Preserve broken/orphaned records with session=null.
                    continue
                raise

        enriched_records = []
        for record in records:
            enriched = dict(record)
            linked_id = record.get("sessionId")
            enriched["session"] = (
                None
                if linked_id in (None, "", self.GENERAL_PRACTICE_SESSION_ID)
                else sessions_by_id.get(linked_id)
            )
            enriched_records.append(enriched)

        return {
            "documentType": "guitarPracticeRecords",
            "filters": {
                "session_id": session_id,
                "practice_date": practice_date,
                "completed": completed,
                "limit": row_limit,
            },
            "recordCount": len(enriched_records),
            "totalDurationSeconds": sum(
                record.get("duration", 0)
                for record in enriched_records
                if isinstance(record.get("duration"), (int, float))
                and not isinstance(record.get("duration"), bool)
            ),
            "records": enriched_records,
        }

    @staticmethod
    def _is_missing_row_error(exc):
        message = str(exc).lower()
        code = getattr(exc, "code", None)
        return code == 404 or "not found" in message or "row does not exist" in message

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

    def add_practice(self, session_name, completed=False, suggested_time=0, duration=0,
                     description="", category="", level="Beginner", link=""):
        self._validate_level(level)
        data = {
            "sessionName": session_name,
            "completed": completed,
            "suggestedTime": int(suggested_time),
            "duration": int(duration),
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

    def update_practice(self, practice_id, session_name="", completed=None, suggested_time=None,
                        duration=None, description="", category="", level=None, link=None):
        self._get(practice_id)
        data = {}
        values = {
            "sessionName": session_name,
            "description": description,
            "category": category,
        }
        for key, value in values.items():
            if value != "":
                data[key] = value
        if suggested_time is not None:
            data["suggestedTime"] = int(suggested_time)
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
            data["duration"] = int(duration)
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
