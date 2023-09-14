import mysql.connector
import os
from dotenv import load_dotenv
import gd
import asyncio

load_dotenv()

try:
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
except Exception as e:
    print(e)

cursor = db.cursor()

cursor.execute("SELECT * FROM requests_table")
for x in cursor:
    print(list(x))

client = gd.Client()

async def get_level(id: int) -> None:
    level = await client.get_level(id)
    print(level.rating)
    print(level.requested_stars)

asyncio.create_task(get_level)

