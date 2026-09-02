import os
from dotenv import load_dotenv
from appwrite.client import Client
from appwrite.services.tables_db import TablesDB
from appwrite.id import ID
from appwrite.query import Query
from appwrite_compat import flatten_row, get_list_items, normalize_limit

load_dotenv()


class TodoService:
    """tasks table.

    tasks.userId == Appwrite Authentication Users.$id
    tasks.projectId == projects.$id
    """

    def __init__(self):
        client = Client()
        client.set_endpoint(os.environ["APPWRITE_ENDPOINT"])
        client.set_project(os.environ["APPWRITE_PROJECT_ID"])
        client.set_key(os.environ["APPWRITE_API_KEY"])
        self.db = TablesDB(client)
        self.database_id = os.environ["APPWRITE_DATABASE_ID"]
        self.table_id = os.environ["APPWRITE_TASKS_TABLE_ID"]

    def add_task(
        self, user_id, content, project_id="", section_id="", parent_id="",
        description="", label_ids=None, priority=4, order=0, day_order=0,
        due_date="", due_string="", due_timezone="", due_is_recurring=False,
        duration=None, duration_unit="", assigned_by_uid="", responsible_uid=""
    ):
        data = {
            "userId": user_id,
            "content": content,
            "labelIds": label_ids or [],
            "priority": priority,
            "order": order,
            "dayOrder": day_order,
            "isCompleted": False,
            "dueIsRecurring": due_is_recurring,
        }

        optional = {
            "projectId": project_id,
            "sectionId": section_id,
            "parentId": parent_id,
            "description": description,
            "dueDate": due_date,
            "dueString": due_string,
            "dueTimezone": due_timezone,
            "duration": duration,
            "durationUnit": duration_unit,
            "assignedByUid": assigned_by_uid,
            "responsibleUid": responsible_uid,
        }
        for key, value in optional.items():
            if value not in ("", None):
                data[key] = value

        return flatten_row(self.db.create_row(
            database_id=self.database_id,
            table_id=self.table_id,
            row_id=ID.unique(),
            data=data,
        ))

    def list_tasks(
        self, user_id, project_id="", section_id="",
        is_completed=None, priority=None, due_date="", limit=100
    ):
        row_limit = normalize_limit(limit, default=100)
        queries = [Query.equal("userId", user_id), Query.limit(row_limit)]

        if project_id:
            queries.append(Query.equal("projectId", project_id))
        if section_id:
            queries.append(Query.equal("sectionId", section_id))
        if is_completed is not None:
            queries.append(Query.equal("isCompleted", is_completed))
        if priority is not None:
            queries.append(Query.equal("priority", priority))
        if due_date:
            queries.append(Query.equal("dueDate", due_date))

        result = self.db.list_rows(
            database_id=self.database_id,
            table_id=self.table_id,
            queries=queries,
            total=False,
        )
        return get_list_items(result, "rows")

    def list_tasks_by_projects(
        self, user_id, project_ids, is_completed=None, limit_per_project=100
    ):
        return {
            project_id: self.list_tasks(
                user_id=user_id,
                project_id=project_id,
                is_completed=is_completed,
                limit=limit_per_project,
            )
            for project_id in project_ids
        }

    def _owned(self, user_id, task_id):
        task = flatten_row(self.db.get_row(
            database_id=self.database_id,
            table_id=self.table_id,
            row_id=task_id,
        ))
        if task.get("userId") != user_id:
            raise PermissionError("Task does not belong to the supplied Auth user $id.")
        return task

    def get_task(self, user_id, task_id):
        return self._owned(user_id, task_id)

    def update_task(
        self, user_id, task_id, content="", description="",
        project_id="", section_id="", parent_id="", label_ids=None,
        priority=None, order=None, day_order=None, due_date="",
        due_string="", due_timezone="", due_is_recurring=None,
        duration=None, duration_unit="", assigned_by_uid="",
        responsible_uid="", is_completed=None
    ):
        self._owned(user_id, task_id)
        data = {}

        values = {
            "content": content,
            "description": description,
            "projectId": project_id,
            "sectionId": section_id,
            "parentId": parent_id,
            "dueDate": due_date,
            "dueString": due_string,
            "dueTimezone": due_timezone,
            "durationUnit": duration_unit,
            "assignedByUid": assigned_by_uid,
            "responsibleUid": responsible_uid,
        }
        for key, value in values.items():
            if value:
                data[key] = value

        if label_ids is not None: data["labelIds"] = label_ids
        if priority is not None: data["priority"] = priority
        if order is not None: data["order"] = order
        if day_order is not None: data["dayOrder"] = day_order
        if due_is_recurring is not None: data["dueIsRecurring"] = due_is_recurring
        if duration is not None: data["duration"] = duration
        if is_completed is not None:
            data["isCompleted"] = is_completed
            if is_completed:
                data["completedAt"] = __import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc
                ).isoformat()

        if not data:
            return self.get_task(user_id, task_id)

        return flatten_row(self.db.update_row(
            database_id=self.database_id,
            table_id=self.table_id,
            row_id=task_id,
            data=data,
        ))

    def complete_task(self, user_id, task_id):
        self._owned(user_id, task_id)
        from datetime import datetime, timezone
        return flatten_row(self.db.update_row(
            database_id=self.database_id,
            table_id=self.table_id,
            row_id=task_id,
            data={
                "isCompleted": True,
                "completedAt": datetime.now(timezone.utc).isoformat(),
            },
        ))

    def delete_task(self, user_id, task_id):
        self._owned(user_id, task_id)
        self.db.delete_row(
            database_id=self.database_id,
            table_id=self.table_id,
            row_id=task_id,
        )
        return {"success": True, "task_id": task_id}
