from instagrapi import Client
import mysql.connector
import sys
 #!/home/aleksandr/instagrambot/bin/python3 

db = mysql.connector.connect(
    host="localhost",
    user="username", ## edit
    passwd="password", ## edit too
    port="3306",
    database="Instagram"
    )

cursor = db.cursor()

sql="SELECT sessionID,path,description FROM posts WHERE id = %s LIMIT 1"
val=sys.argv[1]
cursor.execute(sql,(val,))
auth= cursor.fetchone()
print(auth)
print(auth[2])

cl = Client()## create object - session 
cl.login_by_sessionid(auth[0]) ## authorization 
cl.photo_upload("/home/aleksandr/instagrambot/" + auth[1],auth[2]) # upload photo