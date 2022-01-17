#!C:\Users\quanbro\AppData\Local\Programs\Python\Python37-32\python.exe
#-*- coding: utf-8 -*-
#處理stdio輸出編碼，以避免亂碼
import codecs, sys 
sys.stdout = codecs.getwriter('utf8')(sys.stdout.buffer)
import cgi

#連線DB
from dbConfig import conn, cur
#先印出http 表頭
print("Content-Type: text/html; charset=utf-8\n")
print("""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>範例1</title>
</head>
""")

#查詢
form = cgi.FieldStorage()
inp=form.getvalue('myData')
sql=f"select stuID, Name, Class, Birthday from student where Name like %s;"
cur.execute(sql,(inp+'%',))
records = cur.fetchall()
for (id,cName,cl, birth) in records:
    print(f"{id}: {cName} {cl} {birth}<br>")

print("</body></html>")

