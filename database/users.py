from database.connection import get_connection
import bcrypt


def create_user(username, email, password):


    password_hash = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users
                (username, email, password_hash)
                VALUES (%s, %s, %s)
                """,
                (username, email, password_hash)
            )


