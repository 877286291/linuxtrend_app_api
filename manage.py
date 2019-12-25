import os
from flask_script import Manager

from APP import create_app

env = os.environ.get('FLASK_ENV', 'development')
app = create_app(env)
manager = Manager(app)
if __name__ == '__main__':
    manager.run()
