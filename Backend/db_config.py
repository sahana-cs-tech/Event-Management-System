import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="admin123",
    database="event_management"
)

cursor = db.cursor()  