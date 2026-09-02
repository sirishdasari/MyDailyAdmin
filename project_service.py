import os
from dotenv import load_dotenv
from appwrite.client import Client
from appwrite.services.tables_db import TablesDB
from appwrite.id import ID
from appwrite.query import Query
from appwrite_compat import flatten_row, get_list_items, normalize_limit

load_dotenv()


class ProjectService:
    """projects table.

    projects.userId == Appwrite Authentication Users.$id
    """

    def __init__(self):
        client = Client()
        client.set_endpoint(os.environ["APPWRITE_ENDPOINT"])
        client.set_project(os.environ["APPWRITE_PROJECT_ID"])
        client.set_key(os.environ["APPWRITE_API_KEY"])
        self.db = TablesDB(client)
        self.database_id = os.environ["APPWRITE_DATABASE_ID"]
        self.table_id = os.environ["APPWRITE_PROJECTS_TABLE_ID"]

    def list_projects(self, user_id, include_archived=False, limit=100):
        row_limit = normalize_limit(limit, default=100)
        queries = [Query.equal("userId", user_id), Query.limit(row_limit)]
        if not include_archived:
            queries.append(Query.equal("isArchived", False))

        result = self.db.list_rows(
            database_id=self.database_id,
            table_id=self.table_id,
            queries=queries,
            total=False,
        )
        return get_list_items(result, "rows")

    def _owned(self, user_id, project_id):
        project = flatten_row(self.db.get_row(
            database_id=self.database_id,
            table_id=self.table_id,
            row_id=project_id,
        ))
        if project.get("userId") != user_id:
            raise PermissionError("Project does not belong to the supplied Auth user $id.")
        return project

    def get_project(self, user_id, project_id):
        return self._owned(user_id, project_id)

    def create_project(
        self, user_id, name, color="", icon="", view_style="",
        parent_id="", is_favorite=False, is_archived=False, order=0
    ):
        data = {
            "userId": user_id,
            "name": name,
            "isFavorite": is_favorite,
            "isArchived": is_archived,
            "order": order,
        }
        if color: data["color"] = color
        if icon: data["icon"] = icon
        if view_style: data["viewStyle"] = view_style
        if parent_id: data["parentId"] = parent_id

        return flatten_row(self.db.create_row(
            database_id=self.database_id,
            table_id=self.table_id,
            row_id=ID.unique(),
            data=data,
        ))

    def update_project(
        self, user_id, project_id, name="", color="", icon="",
        view_style="", parent_id="", is_favorite=None,
        is_archived=None, order=None
    ):
        self._owned(user_id, project_id)
        data = {}

        if name: data["name"] = name
        if color: data["color"] = color
        if icon: data["icon"] = icon
        if view_style: data["viewStyle"] = view_style
        if parent_id: data["parentId"] = parent_id
        if is_favorite is not None: data["isFavorite"] = is_favorite
        if is_archived is not None: data["isArchived"] = is_archived
        if order is not None: data["order"] = order

        if not data:
            return self.get_project(user_id, project_id)

        return flatten_row(self.db.update_row(
            database_id=self.database_id,
            table_id=self.table_id,
            row_id=project_id,
            data=data,
        ))

    def delete_project(self, user_id, project_id):
        self._owned(user_id, project_id)
        self.db.delete_row(
            database_id=self.database_id,
            table_id=self.table_id,
            row_id=project_id,
        )
        return {"success": True, "project_id": project_id}
