import mysql.connector

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="CProot",
)

my_cursor = mydb.cursor()

# my_cursor.execute("CREATE DATABASE new_users")
my_cursor.execute("SHOW DATABASES")

for db in my_cursor:
    print(db)
