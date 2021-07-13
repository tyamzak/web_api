import sys
sys.path.insert(0, '/usr/local/lib/python3.8/site-packages')
sys.path.insert(0, '/home/vagrant/myapp')

import os
# Change working directory so relative paths (and template lookup) work again
os.chdir(os.path.dirname(__file__))

from app import app as application