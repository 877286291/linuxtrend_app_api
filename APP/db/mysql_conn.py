import pymysql


def exec_sql(sql, params=None):
    db = pymysql.connect("39.108.180.201", "root", "123456", "linuxtrend")
    cursor = db.cursor()
    cursor.execute(sql)
    results = cursor.fetchall()
    db.close()
    return results

# from pymysqlpool.pool import Pool
#
# pool = None
#
#
# def init():
#     global pool
#     pool = Pool(host='39.108.180.201', port=3306, user='root', password='123456', db='linuxtrend')
#     pool.init()
#
#
# def exec_sql(sql, params=None):
#     connection = pool.get_conn()
#     cur = connection.cursor()
#     cur.execute(sql, params)
#     pool.release(connection)
#     return cur.fetchall()
