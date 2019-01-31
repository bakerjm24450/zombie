"""Global variables for zombie prop
"""

from threading import Timer
import requests

def dummy():
    """Dummy function just so we can create global timer
    """
    pass

# global timer used to turn off magnets
magnetTimer = None

# session for  talking to web server
session = requests.Session()