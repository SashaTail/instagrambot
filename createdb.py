import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="username", ##edit
    passwd="password", ##edit too
    port="3306",
    database="Instagram"
    )





cursor = db.cursor()
#cursor.execute("CREATE DATABASE Instagram")
#cursor.execute("CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY, user_id INT UNIQUE, username VARCHAR(255), password VARCHAR(255), auth TINYINT(1), user_group INT)")


cursor.execute("CREATE TABLE posts (id INT AUTO_INCREMENT PRIMARY KEY, user_id INT , sessionID VARCHAR(255), timetopost DATETIME, path VARCHAR(255), description VARCHAR(255), exec VARCHAR(255))")

