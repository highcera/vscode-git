import pymysql

# 전역변수 선언부
conn, cur = None, None
data1, data2, data3, data4 = "", "", "", ""
sql=""

# 메인 코드
conn = pymysql.connect(host='127.0.0.1', user='root', password='dark##2993', db='hanbitDB', charset='utf8')
cur = conn.cursor()
sql = "CREATE TABLE IF NOT EXISTS userTable (id char(4), userName char(15), email char(20), birthYear int)"
cur.execute(sql)

while (True) :
    data1 = input("사용자 ID ==> ")
    if data1 == "" :
        break;
    data2 = input("사용자 이름 ==> ")
    data3 = input("사용자 이메일 ==> ")
    data4 = input("사용자 출생연도 ==> ")
    sql = "INSERT INTO userTable VALUES('" + data1 + "','" + data2 + "','" + data3 + "'," + data4 + ")"
    cur.execute(sql)

conn.commit()
conn.close()
