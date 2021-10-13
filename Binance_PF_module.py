import Binance_API_Module as bn
import pandas as pd
import json

pd.set_option('display.max_columns', 100)

def get_spot_bal():
    df = bn.get_spotWallet_bal()
    return df

def set_weights(symbols, weights):
    for i, x in enumerate(symbols):
        symbols[i] = x.upper()

    weight_dict = dict(zip(symbols, weights))
    with open('weights.json', 'w') as fp:
        json.dump(weight_dict, fp)

def view_portfolio(whichpf, when):

    # get spot wallet
    bal = bn.get_spotWallet_bal()
    wal1 = pd.DataFrame.from_dict(bal, orient='index')

    # get savings
    savings = bn.get_savings()
    wal2 = pd.DataFrame.from_dict(savings, orient='index')

    # combine savings and spot wallet
    wal1 = wal1.append(wal2)
    overview = wal1
    overview.columns = ['balance']

    # calculate overall assets
    market = 'spot'
    if when == 'now':
        timeframe = '1m'
    elif when == '-1hr':
        timeframe = '1h'

    lim = 10
    for i in overview.index:
        balance = overview.at[i, 'balance']
        if i == 'USDT':
            btcohlcv = bn.get_ohlcv(market, f'BTCUSDT', timeframe, lim)
            btcprice = btcohlcv.at[len(btcohlcv) - 2, 'close']

            overview.at[i, 'usdt_value'] = balance
            overview.at[i, 'btc_value'] = balance / float(btcprice)
            overview.at[i, 'usdt_price'] = 1

        else:
            usdtohlcv = bn.get_ohlcv(market, f'{i}USDT', timeframe, lim)
            usdtprice = usdtohlcv.at[len(usdtohlcv) - 2, 'close']
            if i == 'BTC':
                overview.at[i, 'btc_value'] = balance
                overview.at[i, 'usdt_value'] = balance * float(usdtprice)
                overview.at[i, 'usdt_price'] = float(usdtprice)

            else:
                btcohlcv = bn.get_ohlcv(market, f'{i}BTC', timeframe, lim)
                btcprice = btcohlcv.at[len(btcohlcv) - 2, 'close']

                overview.at[i, 'usdt_value'] = balance * float(usdtprice)
                overview.at[i, 'btc_value'] = balance * float(btcprice)
                overview.at[i, 'usdt_price'] = float(usdtprice)

    # create total asset overview
    all_overview = overview
    all_overview = all_overview.reset_index()
    overview = overview.reset_index()

    # combine savings and spot wallet
    for x in overview.index:
        tmp = overview[x+1:]
        for y in tmp.index:
            if x == y:
                overview.at[x, 'balance'] += tmp.at[y, 'balance']
                overview = overview.drop(index=y)


    # get rid of assets with tiny balances
    for x in overview.index:
        if overview.at[x, 'usdt_value'] < 1:
            overview = overview.drop(index=x)

    # get weighting of each asset
    total = overview['usdt_value'].sum()

    for x in overview.index:
        overview.at[x, 'current_weight'] = overview.at[x, 'usdt_value'] / total * 100

    with open('weights.json', 'r') as fp:
        target = json.load(fp)
    target_weight_df = pd.DataFrame.from_dict(target, columns=['target_weight'], orient='index')
    target_weight_df = target_weight_df.reset_index()
    overview = overview.merge(target_weight_df, on='index')
    overview = overview.fillna(0) # when there is enough balance this should be removed

    # rename columns to coin
    overview = overview.rename(columns={'index': 'coin'})

    # target usdt value
    total = overview['usdt_value'].sum()
    tweight = overview['target_weight']
    overview['target_usdt_value'] = total * tweight/100

    # target weight and current weight difference
    overview['weight_diff'] = overview['target_weight'] - overview['current_weight']

    # action required
    overview['action_usdt'] = overview['target_usdt_value'] - overview['usdt_value']
    overview['action_coin'] = overview['action_usdt'] / overview['usdt_price']

    ###########################################
    # Final df processing
    overview = overview.sort_values(by='coin')
    overview = overview.reset_index(drop=True)
    final_overview = overview.rename(columns={'current_weight': 'cur_weight', 'target_usdt_value': 'target_usdt'})
    final_overview = final_overview.loc[:, ['coin', 'balance', 'usdt_value', 'usdt_price', 'cur_weight', 'target_weight', 'target_usdt', 'weight_diff', 'action_usdt', 'action_coin']]
    all_overview = all_overview.rename(columns={'index':'coin'})
    all_overview = all_overview.sort_values(by='coin')
    all_overview = all_overview.reset_index(drop=True)

    # summary
    summary = {}
    summary['total_value_USD'] = overview['usdt_value'].sum()
    summary['total_value_BTC'] = overview['btc_value'].sum()

    # all summary
    all_summary = {}
    all_summary['total_value_USD'] = all_overview['usdt_value'].sum()

    if whichpf == 'pf':
        print(f'Portfolio summary:\n{summary}\n')
        return final_overview

    elif whichpf == 'totalpf':
        print(f'Total asset summary:\n{all_summary}\n')
        return all_overview

def rebalance(df):
    # Rebalancing Execution
    global quantity, result
    is_rebalanced = True
    base = "https://api.binance.com"  # spot

    with open('base.json', 'r') as fp:
        base_dict = json.load(fp)

    if len(df) > 1:
        for x in df.index:
            symbol = f'{df.at[x, "coin"]}USDT'
            typ = 'market'
            price = 0

            if symbol == 'USDTUSDT':
                break

            elif df.at[x, 'action_usdt'] < -10:
                side = 'sell'
                quantity = round(-df.at[x, 'action_coin'], base_dict[f'{df.at[x, "coin"]}USDT'])
                result = bn.create_order(base, symbol, side, typ, price, quantity)

                #print(f'symbol:{symbol}\nside:{side}\ntype:{typ}\nqty:{quantity}\namt:{df.at[x, "action_usdt"]}\n')
                #print(result)

            elif df.at[x, 'action_usdt'] > 10:
                side = 'buy'
                quantity = round(df.at[x, 'action_coin'], base_dict[f'{df.at[x, "coin"]}USDT'])
                result = bn.create_order(base, symbol, side, typ, price, quantity)
                #print(f'symbol:{symbol}\nside:{side}\ntype:{typ}\nqty:{quantity}\namt:{df.at[x, "action_usdt"]}\n')
                #print(result)
            else:
                is_rebalanced = False
    return is_rebalanced