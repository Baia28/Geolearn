from database.users import create_user

create_user(
    "testuser1",
    "test1@example.com",
    "password123"
)

print("User 1 created!")