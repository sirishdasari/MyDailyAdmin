import os
from dotenv import load_dotenv
from appwrite.client import Client
from appwrite.services.tables_db import TablesDB
from appwrite.query import Query
from appwrite_compat import flatten_row, get_list_items

load_dotenv()


class ProfileService:
    """profiles table.

    profiles.userId == Appwrite Authentication Users.$id
    """

    def __init__(self):
        client = Client()
        client.set_endpoint(os.environ["APPWRITE_ENDPOINT"])
        client.set_project(os.environ["APPWRITE_PROJECT_ID"])
        client.set_key(os.environ["APPWRITE_API_KEY"])
        self.db = TablesDB(client)
        self.database_id = os.environ["APPWRITE_DATABASE_ID"]
        self.table_id = os.environ["APPWRITE_PROFILES_TABLE_ID"]

    def _find(self, user_id):
        result = self.db.list_rows(
            database_id=self.database_id,
            table_id=self.table_id,
            queries=[Query.equal("userId", user_id)],
            total=False,
        )
        rows = get_list_items(result, "rows")
        if not rows:
            raise ValueError("Profile not found for Appwrite Auth user $id.")
        return rows[0]

    def get_profile(self, user_id):
        return self._find(user_id)

    def update_profile(
        self, user_id, display_name="", avatar_url="", timezone="",
        week_start_day=None, theme="", default_project_id="",
        onboarding_complete=None
    ):
        profile = self._find(user_id)
        data = {}

        if display_name: data["displayName"] = display_name
        if avatar_url: data["avatarUrl"] = avatar_url
        if timezone: data["timezone"] = timezone
        if week_start_day is not None: data["weekStartDay"] = week_start_day
        if theme: data["theme"] = theme
        if default_project_id: data["defaultProjectId"] = default_project_id
        if onboarding_complete is not None:
            data["onboardingComplete"] = onboarding_complete

        if not data:
            return profile

        return flatten_row(self.db.update_row(
            database_id=self.database_id,
            table_id=self.table_id,
            row_id=profile["$id"],
            data=data,
        ))
