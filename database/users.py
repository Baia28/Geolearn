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

# additionally

def get_all_users():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, username FROM users ORDER BY user_id ASC")
            rows = cur.fetchall()
            # Turn rows into a list of clean dictionaries
            return [{"id": row[0], "username":row[1]} for row in rows]
        

# Verify PASSWORD on LogIn
def verify_user(username, password):
    with get_connection() as conn:
        with conn.cursor() as cur:
            
            cur.execute("SELECT user_id, password_hash FROM users WHERE username = %s", (username,))
            row = cur.fetchone()

            if row:
                user_id, stored_hash = row[0], row[1]
                # Check if entered password matches the stored hash
                if bcrypt.checkpw(password.encode(), stored_hash.encode()):
                    return {"id": user_id, "username": username}
            return None

