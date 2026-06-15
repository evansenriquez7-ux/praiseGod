import os
os.environ["DATABASE_URL"] = "postgresql://localhost/ccmed"

import urllib.request
import main
from flask import Request
from werkzeug.test import create_environ

environ = create_environ(path='/api/parent/config')
req = Request(environ)

try:
    resp = main.api(req)
    print("STATUS:", resp.status)
    print("BODY:", resp.get_data(as_text=True))
except Exception as e:
    import traceback
    traceback.print_exc()
