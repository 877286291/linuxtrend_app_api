import datetime
import pymysql
import os
import time


def exec_sql(sql):
    try:
        db = pymysql.connect("39.108.180.201", "root", "123456", "linuxtrend")
        cursor = db.cursor()
        cursor.execute(sql)
        db.commit()
        db.close()
    except Exception as e:
        print(e)


while True:
    if os.path.exists('monitor_data_{}'.format(datetime.datetime.now().strftime("%Y-%m-%d"))):
        with open('monitor_data_{}'.format(datetime.datetime.now().strftime("%Y-%m-%d")), 'r') as f:
            data = f.readlines()
            os.remove('monitor_data_{}'.format(datetime.datetime.now().strftime("%Y-%m-%d")))
        for line in data:
            tmp = line.split('|')
            if len(tmp) == 33:
                sql = '''
                    insert into monitor_data values (\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},\'{}\',\'{}\',{},{},{},{},\'{}\',{},\'{}\',\'{}\',{})
                '''.format(tmp[0], tmp[1], tmp[2], tmp[3], tmp[4], tmp[5], tmp[6], tmp[7], tmp[8], tmp[9], tmp[10],
                           tmp[11],
                           tmp[12], tmp[13], tmp[14], tmp[15], tmp[16], tmp[17], tmp[18], tmp[19], tmp[20], tmp[21],
                           tmp[22],
                           tmp[23], tmp[24], tmp[25], tmp[26], tmp[27], tmp[28], tmp[29], tmp[30], tmp[31], tmp[32],
                           tmp[33])
            else:
                sql = '''
                            insert into monitor_data values (\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},\'{}\',\'{}\',{},{},{},{},\'{}\',{},\'{}\',\'{}\',{})
                '''.format(tmp[0], tmp[1], tmp[2], tmp[3], tmp[4], tmp[5], tmp[6], tmp[7], tmp[8], tmp[9], tmp[10],
                           tmp[11],
                           tmp[12], tmp[13], tmp[14], tmp[15], tmp[16], tmp[17], tmp[18], tmp[19], tmp[20], tmp[21],
                           tmp[22],
                           tmp[23], tmp[24], tmp[25], tmp[26], tmp[27], tmp[28], tmp[29], tmp[30], tmp[31], tmp[32],
                           'null')
            exec_sql(sql)
    else:
        pass
    time.sleep(15)
