import time
import hashlib
import requests
import hmac
from urllib.parse import urlencode

global api_key
global secret_key

api_key = 'YOUR API KEY'
secret_key = 'YOUR SECRET KEY'

def _sign(params={}):
    data = params.copy()
    ts = str(int(1000 * time.time()))
    data.update({"timestamp": ts})
    h = urlencode(data)
    hh = h.replace("%40", "@")
    print(hh)
    b = bytearray()
    b.extend(secret_key.encode())
    signature = hmac.new(b, msg=h.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()
    sig = {"signature": signature}
    print(signature)
    return data, sig


def post(path, params={}):
    sign = _sign(params)
    query = urlencode(sign[0]) + "&" + urlencode(sign[1])
    url = "%s?%s" % (path, query)
    print(url)
    header = {"X-MBX-APIKEY": api_key}
    print(header)
    p = requests.post(url, headers=header, timeout=30, verify=True)
    return p


def get(path, params={}):
    sign = _sign(params)
    query = urlencode(sign[0]) + "&" + urlencode(sign[1])
    url = "%s?%s" % (path, query)
    print(url)
    header = {"X-MBX-APIKEY": api_key}
    p = requests.get(url, headers=header, timeout=30, verify=True)
    return p

