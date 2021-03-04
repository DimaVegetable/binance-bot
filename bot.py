from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from binance.websockets import BinanceSocketManager
from time import sleep
from binance.enums import *
from collections import deque
import os
from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

print(os.getenv('API_KEY'))
print(os.getenv('API_SECRET'))
print(os.getenv('API_URL'))
price = {'BTCUSDT': None, 'error': False}
moving_average = {'MA': None, 'error': False}
client = Client(api_key=os.getenv('API_KEY'),
                api_secret=os.getenv('API_SECRET'))
client.API_URL = 'https://testnet.binance.vision/api'
candles_price = deque([])
print(client.get_asset_balance(asset='BTC'))
print(client.get_asset_balance(asset='USDT'))
bsm = BinanceSocketManager(client)


def btc_pairs_trade(msg):
    if msg['e'] != 'error':
        price['BTCUSDT'] = float(msg['c'])
    else:
        price['error']: True


def candles(msg):
    ma = float()
    if msg['e'] != 'error':
        if len(candles_price) < 9:
            candles_price.append(msg['k']['c'])
        else:
            candles_price.popleft()
            candles_price.append(msg['k']['c'])
            for average in candles_price:
                ma += float(average)
            moving_average['MA'] = float(ma / 9)
            buy_sell()
    else:
        moving_average['error']: True


conn_kline = bsm.start_kline_socket(symbol='BTCUSDT', callback=candles, interval=KLINE_INTERVAL_5MINUTE)
conn_btc = bsm.start_symbol_ticker_socket(symbol='BTCUSDT', callback=btc_pairs_trade)


def buy_sell():
    while not price['BTCUSDT']:
        sleep(0.1)

    while True:
        if price['error'] or moving_average['error']:
            bsm.stop_socket(conn_btc)
            bsm.stop_socket(conn_kline)
            bsm.start()
            price['error'] = False
        else:
            print(price['BTCUSDT'], moving_average['MA'])
            if price['BTCUSDT'] < moving_average['MA']:
                try:
                    client.order_market_buy(symbol='BTCUSDT', quantity=0.002)
                except BinanceAPIException as e:
                    print(e)
                except BinanceOrderException as e:
                    print(e)
            elif price['BTCUSDT'] > moving_average['MA']:
                try:
                    client.order_market_sell(symbol='BTCUSDT', quantity=0.002)
                except BinanceAPIException as e:
                    print(e)
                except BinanceOrderException as e:
                    print(e)
            else:
                bsm.stop_socket(conn_kline)
                bsm.stop_socket(conn_btc)
                bsm.close()
            print(client.get_asset_balance(asset='BTC'))
            print(client.get_asset_balance(asset='USDT'))
        sleep(0.1)


def main():
    bsm.start()


if __name__ == '__main__':
    main()