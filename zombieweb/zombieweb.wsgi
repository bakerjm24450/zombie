activate_this = '/var/www/zombieweb/venv/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

import sys
sys.path.insert(0, '/var/www/zombieweb/')

from zombieweb import create_app
application = create_app()
