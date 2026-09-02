import os
from dotenv import load_dotenv
from appwrite.client import Client
from appwrite.services.users import Users
from appwrite.query import Query
from appwrite_compat import get_list_items, normalize_limit, to_plain

load_dotenv()


class UserService:
    """Appwrite Authentication Users service.

    The returned id is Users.$id and is the canonical user ID
    stored in profiles.userId, projects.userId and tasks.userId.
    """

    def __init__(self):
        client = Client()
        client.set_endpoint(os.environ["APPWRITE_ENDPOINT"])
        client.set_project(os.environ["APPWRITE_PROJECT_ID"])
        client.set_key(os.environ["APPWRITE_API_KEY"])
        self.users = Users(client)

    @staticmethod
    def public_user(user):
        user = to_plain(user)
        return {
            "id": user.get("$id"),
            "name": user.get("name", ""),
            "email": user.get("email", ""),
        }

    def list_users(self, limit=25):
        result = self.users.list(queries=[Query.limit(normalize_limit(limit))])
        return [self.public_user(x) for x in get_list_items(result, "users")]

    def search_users(self, query, limit=25):
        result = self.users.list(
            queries=[Query.limit(normalize_limit(limit))],
            search=query,
        )
        return [self.public_user(x) for x in get_list_items(result, "users")]

    def get_user(self, user_id):
        return self.public_user(self.users.get(user_id))
