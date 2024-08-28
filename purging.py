from gdmisc import parser
import mysql.connector
import os


def connect():
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

    return db


db = connect()
cursor = db.cursor()

cursor.execute("SELECT level_id FROM requests_table")
results = cursor.fetchall()

counter = 0

for id in results:
    level_parsed = parser.get_parsed_level_data(id)
    if level_parsed[0] == "Level Search":
        cursor.execute("DELETE FROM requests_tabel WHERE level_id = %s", (id,))
        counter += 1

print(f"Удалено {counter} уровней")
