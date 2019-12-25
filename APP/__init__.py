from flask import Flask
from APP.settings import envs
from APP.db import mysql_conn
from APP.views import init_blue


def create_app(env):
    app = Flask(__name__)
    app.config.from_object(envs.get(env))
    # 初始化数据库
    # mysql_conn.init()
    # 初始化路由
    init_blue(app)
    return app
