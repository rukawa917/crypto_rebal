import binance_api_base as bn
import requests
import pandas as pd
from binance.client import Client

api_key = 'YOUR API KEY'
secret_key = 'YOUR SECRET KEY'
client = Client(api_key, secret_key)

def check_server_time():
    base = 'https://sapi.binance.com'
    path = f'{base}/sapi/v1/time'

    params = {}
    result = bn.get(path, params)
    result = result.json()

    return result

def check_spotserver_time():
    result = client.get_server_time()
    result = result['serverTime']
    print(result)

    return result


def get_spotWallet_bal():
    base = "https://api.binance.com"
    path = f'{base}/sapi/v1/capital/config/getall'
    st = check_spotserver_time()

    params = {'timestamp': st}
    result = bn.get(path, params=params)
    result = result.json()
    #print(result)

    myWallet = {}
    for item in result:
        if item['free'] != str(0) and item['trading'] == True:
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


def get_ticker(market):
    if market == 'coin_future':
        coin_future = "https://dapi.binance.com"
        url = f'{coin_future}/dapi/v1/ticker/price'
        result = requests.get(url).json()
        lst = []
        for a in result:
            lst.append(a)
        return lst
    elif market == 'usdt_future':
        usdt_future = "https://fapi.binance.com"
        url = f'{usdt_future}/fapi/v1/ticker/price'
        result = requests.get(url).json()
        lst = []
        for a in result:
            lst.append(a)
        return lst
    elif market == 'spot':
        spot = "https://api.binance.com"
        url = f'{spot}/api/v3/ticker/price'
        result = requests.get(url).json()
        lst = []
        for a in result:
            lst.append(a)
        return lst


def get_savings():
    base = "https://api.binance.com"
    '''
    path1 = f'{base}/sapi/v1/lending/daily/product/list'
    st = check_spotserver_time()
    params = {"status": "ALL",
              "size": 100,
              "timestamp": st}
    products = bn.get(path1, params)
    products = products.json()
    alst = []
    for x in products:
        alst.append(x['asset'])
    '''
    path2 = f'{base}/sapi/v1/lending/daily/token/position'
    st = check_spotserver_time()
    with open('asset.json', 'r') as fp:
        assets_dict = json.load(fp)
    my_assets = assets_dict['assets']
    mySavings = {}
    for asset in my_assets:
        try:
            params = {'asset': f"{asset}",
                      'timestamp': st}
            result = bn.get(path2, params=params)
            result = result.json()
            if len(result) > 0:
                mySavings[asset] = float(result[0]['totalAmount'])
        except:
            continue
    return mySavings

base = "https://api.binance.com"
path1 = f'{base}/sapi/v1/lending/daily/product/list'
st = check_spotserver_time()
params = {"status": "ALL",
          "size": 100,
          "timestamp": st}
products = bn.get(path1, params)
products = products.json()
#alst = []
for x in products:
    print(x)
    #alst.append(x['asset'])

def redeem_savings(base, asset, amt):
    path = f'{base}/sapi/v1/lending/daily/redeem'
    params = {
        'productId': f'{asset}001',
        'amount': amt,
        'type': 'FAST'
    }
    result = bn.post(path, params=params)
    print(result.json())


def put_savings(base, asset, amt):
    path = f'{base}/sapi/v1/lending/daily/purchase'
    params = {
        'productId': f'{asset}001',
        'amount': amt
    }
    result = bn.post(path, params=params)
    print(result.json())


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
