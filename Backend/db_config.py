import os
import mysql.connector

db = mysql.connector.connect(
    host=os.getenv("MYSQLHOST", "localhost"),
    port=int(os.getenv("MYSQLPORT", "3306")),
    user=os.getenv("MYSQLUSER", "root"),
    password=os.getenv("MYSQLPASSWORD", "admin123"),
    database=os.getenv("MYSQLDATABASE", "event_management")
)

cursor = db.cursor()