import binance_api_base as bn
import requests
import pandas as pd
from binance.client import Client

api_key = 'YOUR API KEY'
secret_key = 'YOUR SECRET KEY'
client = Client(api_key, secret_key)


def check_spotserver_time():
    result = client.get_server_time()
    result = result['serverTime']

    return result

def get_spotWallet_bal():
    base = "https://api.binance.com"
    path = f'{base}/sapi/v1/capital/config/getall'
    st = check_spotserver_time()

    params = {'timestamp': st}
    result = bn.get(path, params=params)
    result = result.json()

    myWallet = {}
    for item in result:
        if item['free'] != str(0):
            myWallet[f'{item["coin"]}'] = float(item['free'])
    return myWallet

def get_ohlcv(market, symbol, interval='1h', limit=500):
    if market == 'coin_future':
        coin_future = "https://dapi.binance.com"
        url = f'{coin_future}/dapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}'  # max limit = 1500
        data = requests.get(url).json()
        temp = pd.DataFrame(data)
        temp = temp[[0, 1, 2, 3, 4, 5]]
        temp.columns = ['time', 'open', 'high', 'low', 'close', 'volume']
        temp['time'] = pd.to_datetime(temp['time'], unit='ms')
        return temp

    elif market == 'usdt_future':
        usdt_future = "https://fapi.binance.com"
        url = f'{usdt_future}/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}'  # max limit = 1500
        data = requests.get(url).json()
        temp = pd.DataFrame(data)
        temp = temp[[0, 1, 2, 3, 4, 5]]
        temp.columns = ['time', 'open', 'high', 'low', 'close', 'volume']
        temp['time'] = pd.to_datetime(temp['time'], unit='ms')
        return temp

    elif market == 'spot':
        spot = "https://api.binance.com"
        url = f'{spot}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'  # max limit = 1000
        data = requests.get(url).json()
        temp = pd.DataFrame(data)
        temp = temp[[0, 1, 2, 3, 4, 5]]
        temp.columns = ['time', 'open', 'high', 'low', 'close', 'volume']
        temp['time'] = pd.to_datetime(temp['time'], unit='ms')
        return temp

def create_order(base, symbol, side, typ, price, quantity):
    path = f'{base}/api/v3/order'
    if typ == 'LIMIT' or typ == 'limit':
        params = {'symbol': symbol,
                  'side': side,
                  'type': 'LIMIT',  # LIMIT
                  'price': price,
                  'quantity': quantity,
                  'timeInForce': 'GTC'}

    elif typ == 'MARKET' or typ == 'market':
        params = {'symbol': symbol,
                  'side': side,
                  'quantity': quantity,
                  'type': 'MARKET'  # MARKET
                  }

    result = bn.post(path, params=params)
    result = result.json()

    return result
