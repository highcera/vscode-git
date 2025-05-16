import pymysql

conn = pymysql.connect(host='localhost', user='root', password='dark##2993', db='soloDB', charset='utf8')
# 127.0.0.1 or localhost, *utf8: 한글이 문제 없도록 utf8을 사용

cur = conn.cursor()

cur.execute("CREATE TABLE userTable (id char(4), userName char(15), email char(20), birthYear int)")
cur.execute("INSERT INTO userTABLE VALUES('hong', '홍지윤', 'hong@naver.com', 1996)")
cur.execute("INSERT INTO userTABLE VALUES('kim', '김태연', 'kim@daum.net', 2011)")
cur.execute("INSERT INTO userTABLE VALUES('star', '별사랑', 'star@paran.com', 1990)")
cur.execute("INSERT INTO userTABLE VALUES('yang', '홍지윤', 'yang@gmail.com', 1993)")

conn.commit()
conn.close()