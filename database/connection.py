import psycopg

def get_connection():
    return psycopg.connect(
        dbname="geo_book",
        user="baia"
    )