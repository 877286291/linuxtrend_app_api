import datetime
import json
from flask import request, jsonify, Blueprint
from .db import mysql_conn, redis_conn

blue = Blueprint('blue', __name__)

r = None


def init_blue(app):
    app.register_blueprint(blue)


@blue.before_request
def init():
    global r
    r = redis_conn.init()


@blue.route('/get_linux_cpu_stack', methods=['POST'])
def get_linux_cpu_stack():
    hosts = []
    linux = request.form.get('linux')
    period = int(request.form.get('period'))
    if r.get('get_linux_cpu_stack_{}_{}'.format(linux, period)):
        return jsonify(json.loads(r.get('get_linux_cpu_stack_{}_{}'.format(linux, period))))
    else:
        last_time = datetime.datetime.now()
        start_time = last_time - datetime.timedelta(hours=period)
        time_series = {last_time.strftime("%Y-%m-%d-%H-%M"): {}}
        while last_time - datetime.timedelta(minutes=5) != start_time:
            time_series.update({(last_time - datetime.timedelta(minutes=5)).strftime("%Y-%m-%d-%H-%M"): {}})
            last_time = last_time - datetime.timedelta(minutes=5)
        result = mysql_conn.exec_sql('''
                    select sn,hn from linuxone_lpar where linuxone_lpar.one=\'{linux}\';
    '''.format(linux=linux))
        for res in result:
            hosts.append(res[1])
            for t in time_series:
                time_series[t].update({res[1]: 0})
        for res in result:
            tmp = mysql_conn.exec_sql(
                '''select sn,hn,pcusenum,rq,sj from monitor_data where sn= \'{sn}\' and hn = \'{hn}\'and rq>=\'{start_rq}\' ORDER BY sj '''.format(
                    sn=res[0], hn=res[1], start_rq=start_time.strftime('%Y-%m-%d')))
            for i in tmp:
                try:
                    time_series[
                        i[3].strftime("%Y-%m-%d") + '-' + i[4].split(':')[0] + '-' + i[4].split(':')[1]][res[1]] = i[2]
                except KeyError:
                    pass
        r.set('get_linux_cpu_stack_{}_{}'.format(linux, period), json.dumps(time_series), ex=300)
        return jsonify(time_series)


@blue.route('/get_linux_list', methods=['GET'])
def get_linux_list():
    response = {'南中心': [], 'IDC': []}
    for area in ['南中心', 'IDC']:
        result = mysql_conn.exec_sql('''
        select DISTINCT one,hmc FROM linuxone_lpar where area=\'{}\' order by one;
    '''.format(area))
        for r in result:
            response[area].append(r[0] + ' ' + r[1])
    return jsonify(response)


@blue.route('/get_host_list', methods=['POST'])
def get_host_list():
    response = {'response': []}
    linux = request.form.get('linux')
    result = mysql_conn.exec_sql('''
        select hn from linuxone_lpar where one=\'{linux}\' order by hn
    '''.format(linux=linux))
    for res in result:
        response['response'].append(res[0])
    return jsonify(response)


@blue.route('/get_cpu_top', methods=['GET'])
def get_cpu_top():
    response = {'res': []}
    date, last_sj = (datetime.datetime.now() - datetime.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M").split(' ')
    now = datetime.datetime.now().strftime("%H:%M")
    result = mysql_conn.exec_sql(
        '''select hn,max(cpuus+0) as cpuus from monitor_data WHERE rq = \'{date}\' and sj > \'{sj}\' and sj < \'{now}\' group by ip,hn order by cpuus desc limit 10'''.format(
            date=date, sj=last_sj,
            now=now))
    for res in result:
        response['res'].append({res[0]: res[1]})
    return jsonify(response)


@blue.route('/get_host_info', methods=['POST'])
def get_host_info():
    response = {}
    host = request.form.get('host')
    if request.form.get('type') == 'cpu':
        result = mysql_conn.exec_sql('''
            select sj,cpuus from monitor_data where rq=\'{rq}\' and hn=\'{host}\'
        '''.format(rq=datetime.datetime.now().strftime("%Y-%m-%d"), host=host))
        for res in result:
            response.update({res[0]: int(res[1])})
    elif request.form.get('type') == 'memory':
        response = {'res': {}, 'total': 0}
        result = mysql_conn.exec_sql('''
                    select memgb,memgb*(memus/100) as memus,memgb-memgb*(memus/100) as available,memgb*(memfreegb/100) as cache from monitor_data where rq=\'{rq}\' and hn=\'{host}\' order by sj desc limit 1;
                '''.format(rq=datetime.datetime.now().strftime("%Y-%m-%d"), host=host))
        for res in result:
            response['res'].update(
                {'Used': round(float(res[1]), 2), 'Available': round(float(res[2]), 2),
                 'Buffer/Cache': round(float(res[3]), 2)})
            response['total'] = round(float(res[0]), 2)
    elif request.form.get('type') == 'net':
        response = {'in': {}, 'out': {}}
        result = mysql_conn.exec_sql('''
                            select sj,netinkb1,netoutkb1 from monitor_data where rq=\'{rq}\' and hn=\'{host}\' order by sj;
                        '''.format(rq=datetime.datetime.now().strftime("%Y-%m-%d"), host=host))
        for res in result:
            response['in'].update({res[0]: int(res[1])})
            response['out'].update({res[0]: int(res[2])})
    elif request.form.get('type') == 'disk':
        response = {'read': {}, 'write': {}}
        result = mysql_conn.exec_sql('''
                                    select sj,ioreadmb,iowritmb from monitor_data where rq=\'{rq}\' and hn=\'{host}\' order by sj;
                                '''.format(rq=datetime.datetime.now().strftime("%Y-%m-%d"), host=host))
        for res in result:
            response['read'].update({res[0]: int(res[1])})
            response['write'].update({res[0]: int(res[2])})
    return jsonify(response)


@blue.route('/post_monitor_data', methods=['POST'])
def post_monitor_data():
    try:
        monitor_data = request.files.get('data')
        monitor_data = monitor_data.read().decode('utf-8')
        with open('monitor_data_{}'.format(datetime.datetime.now().strftime("%Y-%m-%d")), 'a+') as f:
            f.write(monitor_data)
        for line in monitor_data.split('\n')[:-1]:
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
            mysql_conn.exec_sql(sql)
    except Exception as e:
        print(e)
    return 'success'


@blue.route('/post_inspection_data', methods=['POST'])
def post_inspection_data():
    inspection_data = request.files.get('inspection').read().decode('utf-8')
    with open('inspection_data_{}'.format(datetime.datetime.now().strftime("%Y-%m-%d")), 'w') as f:
        f.write(inspection_data)
    print(inspection_data)
    for line in inspection_data.split('\n')[:-1]:
        tmp = line.split('\t')
        mysql_conn.exec_sql('''
            insert into inspection_data(linux,issue,datetime,type) values (\'{}\',\'{}\',\'{}\',\'{}\');
        '''.format(tmp[0], tmp[1], datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), tmp[2]))
    return 'success'


@blue.route('/get_inspection_data', methods=['GET'])
def get_inspection_data():
    response = {'1': [], '2': [], '3': []}
    result = mysql_conn.exec_sql('''
        select linux,issue,type from inspection_data where date_format(datetime, '%Y-%m-%d %H')=\'{}\'
    '''.format(datetime.datetime.now().strftime("%Y-%m-%d %H")))
    filter_key = set()
    for res in result:
        if res[2] == 1:
            response['1'].append({res[0]: res[1]})
            filter_key.add('1')
        elif res[2] == 2:
            response['2'].append({res[0]: res[1]})
            filter_key.add('2')
        elif res[2] == 3:
            response['3'].append({res[0]: res[1]})
            filter_key.add('3')
    for i in (list(set(['1', '2', '3']) - filter_key)):
        response.pop(i)
    return jsonify(response)
