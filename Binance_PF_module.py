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

def view_portfolio():
    # get spot wallet
    bal = bn.get_spotWallet_bal()
    wal1 = pd.DataFrame.from_dict(bal, orient='index')
    # print(wal1)

    # get savings
    savings = bn.get_savings()
    wal2 = pd.DataFrame.from_dict(savings, orient='index')
    # print(wal2)

    # combine savings and spot wallet
    wal1 = wal1.append(wal2)
    overview = wal1
    overview.columns = ['balance']

    # reset index and rename the index column coin.
    overview = overview.reset_index()
    overview = overview.rename(columns={'index': 'coin'})

    # combine savings and spot wallet
    overview = overview.groupby(['coin'], as_index=False).sum()

    # calculate overall assets
    market = 'spot'
    timeframe = '1m'

    lim = 10
    for i in overview.index:
        coin = overview.at[i, "coin"]
        balance = overview.at[i, 'balance']
        if coin == 'USDT':
            btcohlcv = bn.get_ohlcv(market, f'BTCUSDT', timeframe, lim)
            btcprice = btcohlcv.at[len(btcohlcv) - 2, 'close']

            overview.at[i, 'usdt_value'] = balance
            overview.at[i, 'btc_value'] = balance / float(btcprice)
            overview.at[i, 'usdt_price'] = 1

        else:
            usdtohlcv = bn.get_ohlcv(market, f'{coin}USDT', timeframe, lim)
            usdtprice = usdtohlcv.at[len(usdtohlcv) - 2, 'close']
            if coin == 'BTC':
                overview.at[i, 'btc_value'] = balance
                overview.at[i, 'usdt_value'] = balance * float(usdtprice)
                overview.at[i, 'usdt_price'] = float(usdtprice)

            else:
                # print(coin)
                btcohlcv = bn.get_ohlcv(market, f'{coin}BTC', timeframe, lim)
                btcprice = btcohlcv.at[len(btcohlcv) - 2, 'close']

                overview.at[i, 'usdt_value'] = balance * float(usdtprice)
                overview.at[i, 'btc_value'] = balance * float(btcprice)
                overview.at[i, 'usdt_price'] = float(usdtprice)
    # print(overview)

    # get rid of assets with tiny balances and lockedup ETH
    for x in overview.index:
        if overview.at[x, 'usdt_value'] < 1:
            overview = overview.drop(index=x)
        #elif overview.at[x, 'index'] == 'BETH':
        #    overview = overview.drop(index=x)

    # get weighting of each asset
    total = overview['usdt_value'].sum()
    for x in overview.index:
        overview.at[x, 'current_weight'] = overview.at[x, 'usdt_value'] / total * 100
    # print(overview)
    with open('weights.json', 'r') as fp:
        target = json.load(fp)
    target_weight_df = pd.DataFrame.from_dict(target, columns=['target_weight'], orient='index')
    target_weight_df = target_weight_df.reset_index()
    target_weight_df = target_weight_df.rename(columns={'index': 'coin'})

    # overview['target_weight'] = [x for x in range(len(overview))]
    overview['target_weight'] = 0
    for i in overview.index:
        coin = overview.at[i, 'coin']
        idx = overview[overview['coin'] == coin].index.values[0]
        if(coin in list(target_weight_df['coin'])):
            idx2 = target_weight_df[target_weight_df['coin'] == coin].index.values[0]
            overview.at[idx, 'target_weight'] = target_weight_df.at[idx2, 'target_weight']
            # print(overview)
            # overview.at[i, 'target_weight'] = target_weight_df.at[i, 'target_weight']
    # print(overview)
    # print(target_weight_df)
    # merge two df
    # overview = overview.merge(target_weight_df, on='coin')
    # overview = overview.fillna(0) # when there is enough balance this should be removed


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
    # all_overview = all_overview.rename(columns={'index':'coin'})
    # all_overview = all_overview.sort_values(by='coin')
    # all_overview = all_overview.reset_index(drop=True)

    # summary
    summary = {}
    summary['total_value_USD'] = overview['usdt_value'].sum()
    summary['total_value_BTC'] = overview['btc_value'].sum()

    # all summary
    # all_summary = {}
    # all_summary['total_value_USD'] = all_overview['usdt_value'].sum()
    # all_summary['total_value_BTC'] = all_overview['btc_value'].sum()

    print(f'Portfolio summary:\n{summary}\n')
    return final_overview
    # if whichpf == 'pf':
    #     #print(f'Portfolio overview:\n{overview}')
    #     print(f'Portfolio summary:\n{summary}\n')
    #     return final_overview

    # elif whichpf == 'totalpf':
    #     #print(f'Total asset overview:\n{all_overview}')
    #     print(f'Total asset summary:\n{all_summary}\n')
    #     return all_overview


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