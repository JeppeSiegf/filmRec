import os
import ipaddress
from flask import request, abort
from api import create_app, create_db

SECRET = os.environ.get('API_SECRET')
TRUSTED_RANGES = [
    ipaddress.ip_network(r) for r in os.getenv('TRUSTED_RANGES', '').split(',') if r
]



app = create_app()
create_db(app)


@app.before_request
def guard():
    ip = ipaddress.ip_address(request.remote_addr)
    print(f"REMOTE ADDR: {request.remote_addr}", flush=True)
    if any(ip in net for net in TRUSTED_RANGES):
        return
    if request.headers.get('x-secret') != SECRET:
        abort(403)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False, threaded=True)
