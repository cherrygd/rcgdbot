import mysql.connector
import os
from dotenv import load_dotenv
import pandas
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

cursor.execute("""SELECT
                    staff.user_discord AS admin_discord,
                    COUNT(requests_logs.req_id) AS request_count
                FROM
                    staff
                LEFT JOIN
                    requests_logs
                ON
                    staff.id = requests_logs.reviewer_id
                WHERE
                    staff.user_role = 2
                GROUP BY
                    staff.user_discord
                ORDER BY
                    request_count DESC
            """)
d = cursor.fetchall()
print(d)