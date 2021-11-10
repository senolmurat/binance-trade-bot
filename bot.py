from datetime import time

from binance import Client
import pandas as pd
import ta
import sys
#import config


def getData(symbol, interval, lookback):
    if interval != None:
        frame = pd.DataFrame(client.get_historical_klines(symbol, interval, lookback + "min ago UTC"))
    else:
        frame = pd.DataFrame(client.get_historical_klines(symbol, "1m", "40m UTC"))
    frame = frame.iloc[:,:6]
    frame.columns = ["Time" , "Open" , "High" , "Low" , "Close" , "Volume"]
    frame = frame.set_index("Time")
    frame.index = pd.to_datetime(frame.index , unit='ms')
    frame = frame.astype(float)
    return frame


def getTopSymbol():
    all_pairs = pd.DataFrame(client.get_ticker())
    all_pairs['priceChangePercent'] = all_pairs['priceChangePercent'].astype(float)
    filtered_pairs = all_pairs[all_pairs.symbol.str.contains('USDT')]
    filtered_pairs = filtered_pairs[~((filtered_pairs.symbol.str.contains('UP')) | (filtered_pairs.symbol.str.contains('DOWN')))]
    top_symbol = filtered_pairs[filtered_pairs.priceChangePercent == filtered_pairs.priceChangePercent.max()]
    top_symbol = top_symbol.symbol.values[0]
    return top_symbol


def trading_macd(symbol , qty , open_position = False):
    while True:
        df = getData(symbol)
        if not open_position:
            if ta.trend.macd_diff(df.Close).iloc[-1] > 0 and ta.trend.macd_diff(df.Close).iloc[-2] < 0:
                order = client.create_order(symbol=symbol , side="BUY", type="MARKET", quantity = qty)
                print(order)
                open_position=True
                buyprice = float(order['fills'][0]['price'])
                break
        if open_position:
            while True:
                df = getData(symbol)
                if ta.trend.macd_diff(df.Close).iloc[-1] < 0 and ta.trend.macd_diff(df.Close).iloc[-2] > 0:
                    order = client.create_order(symbol=symbol, side="SELL", type="MARKET", quantity=qty)
                    sellprice = float(order['fills'][0]['price'])
                    #print(f'profit = {(sellprice - buyprice) / buyprice}')
                    open_position = False
                    break


def trading_altcoin(buy_amt , SL = 0.985 , Target = 1.02 , open_position=False):
    try:
        asset = getTopSymbol()
        df = getData(asset , '1m' , '120')
    except:
        time.sleep(61)
        asset = getTopSymbol()
        df = getData(asset, '1m', '120')

    qty = round(buy_amt/df.Close.iloc[-1])
    if ((df.Close.pct_change() + 1).cumprod()).iloc[-1] > 1:
        order = client.create_order(symbol = asset , side="BUY" , type="MARKET", quantity=qty)

        print(order)
        buyprice = float(order['fills'][0]['price'])
        open_position=True
        while open_position:
            try:
                df = getData(asset, '1m', '2')
            except:
                print("ERROR LOG - SCRIPT WILL WAIT 1M")
                time.sleep(61)
                df = getData(asset, '1m', '2')

            print(f'CURRENT --- CLOSE: {str(df.Close[-1])} TARGET: {str(buyprice*Target)} STOP: {str(buyprice*SL)}')
            if df.Close[-1] <= buyprice*SL or df.Close[-1] >= buyprice*Target:
                order = client.create_order(symbol=asset, side="SELL", type="MARKET", quantity=qty)
                print(order)
                break


if len(sys.argv) > 1:
    try:
        api_key = str(sys.argv[1])
        api_secret = str(sys.argv[2])
    except:
        print("ARGUMENT ERROR")
    client = Client(api_key, api_secret)
    while True:
        trading_altcoin(15)
else:
    print("ERROR --- Must run the script with arguments \n python bot.py 'api_key' 'api_secret'")
