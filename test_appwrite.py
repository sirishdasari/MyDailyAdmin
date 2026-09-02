import os
from dotenv import load_dotenv
from user_service import UserService
from todo_service import TodoService
from project_service import ProjectService
from profile_service import ProfileService

load_dotenv()

def main():
    print("=== AUTH USERS ===")
    users = UserService().list_users(10)
    for u in users:
        print(u)

    user_id = os.getenv("TEST_USER_ID")
    if not user_id:
        print("\nSet TEST_USER_ID in .env to test related tables.")
        return

    print("\n=== PROFILE ===")
    try:
        print(ProfileService().get_profile(user_id))
    except Exception as e:
        print("Profile:", e)

    print("\n=== PROJECTS ===")
    print(ProjectService().list_projects(user_id))

    print("\n=== TASKS ===")
    print(TodoService().list_tasks(user_id))

if __name__ == "__main__":
    main()
