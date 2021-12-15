import time
import calendar
import pandas as pd
from binance.client import Client

def profit_loss(market='BTC-USDT', start_date = '2020-01-01', end_date='2021-12-31', client=Client(), showlog=False):

    import numpy as np

    np.seterr(invalid='ignore')

    try:
        asset_base = market.split("-")[0]
        asset_quote = market.split("-")[1]
    except IndexError:
        raise Exception(f"!!! Warning: Use dash '-' to split base and quote assets for {market}!")

    symbol = asset_base + asset_quote

    # Connect to Binance
    try:
        trades = client.get_my_trades(symbol = symbol)        
    except:
        raise Exception(f"!!! Warning: Can't get orders for {symbol}! Read message above.")    

    # Create DataFrame 
    df = pd.DataFrame(trades, columns = ['time', 'symbol', 'isBuyer', 'price', 'qty', 'quoteQty', 'commission', 'commissionAsset'])
    qty_base = 'qty_' + asset_base
    qty_quote = 'qty_' + asset_quote
    df.columns = ['time', 'symbol', 'side', 'price', qty_base, qty_quote, 'fee', 'fee_coin']
    df.side = df.side.replace([True, False], [1, -1])
    df = df.astype({'price': 'float', qty_base: 'float', qty_quote: 'float', 'fee': 'float'})

    # Start from time
    time_format = '%Y-%m-%d'
    start_date_ms = int(calendar.timegm(time.strptime(start_date, time_format)) * 1000)
    end_date_ms = int((calendar.timegm(time.strptime(end_date, time_format)) + 86400) * 1000)
    df = df[(df.time >= start_date_ms) & (df.time <= end_date_ms)]
    df.time = pd.to_datetime(df.time, unit='ms')

    # Find time for getting market prices
    time_now = time.gmtime(time.time())
    day_now_ms = calendar.timegm((time_now.tm_year, time_now.tm_mon, time_now.tm_mday, 0, 0, 0, 0, 0, 0)) * 1000
    prices_time = min(day_now_ms, end_date_ms)

    # Get symbol price
    try:
        symbol_price = float(client.get_klines(symbol = symbol, interval = '1m', startTime=prices_time, limit = 1)[0][4])        
    except:
        print(f"Something wrong with request of {symbol} price. Please try again.")

    # Get quote-USD price
    if asset_quote == 'USDC' or asset_quote == 'USDT' or asset_quote == 'BUSD':
        usd_price = 1
    else:
        try:
            usd_price = float(client.get_klines(symbol = asset_quote + 'USDT', interval = '1m', startTime=prices_time,  limit = 1)[0][4])
        except:
            print(f"Something wrong with the request of {asset_quote}USDT price. Please try again.")

    # Get BNB-quote price
    if asset_quote == 'BNB':
        bnb_price = 1
    else:
        try:
            bnb_price = float(client.get_klines(symbol = 'BNB' + asset_quote, interval = '1m', startTime = prices_time, limit = 1)[0][4])            
        except:
            print(f"Something wrong with the request of BNB{asset_quote} price. Please try again.")
    
    # Summary
    days = int((prices_time - start_date_ms)/(1000 * 86400))
    average_buy = df[df.side == 1][qty_quote].sum()/df[df.side == 1][qty_base].sum()
    average_sell = df[df.side == -1][qty_quote].sum()/df[df.side == -1][qty_base].sum()
    total_volume = df[qty_quote].sum()

    # Delta
    delta_base = (df[qty_base] * -df.side).sum()
    delta_quote = (df[qty_quote] * -df.side).sum()

    # Fees
    fee_bnb = df[df.fee_coin == 'BNB'].fee.sum()    
    fee_quote = -df.fee.sum()
    fee_base  = -(df.fee / df.price).sum()
    
    # Totals
    total_percent = ((df[qty_quote][df.side == -1].sum() / (df[qty_quote][df.side == 1].sum())) - 1) * 100
    total_base = (delta_base + delta_base * 0.002)
    total_quote = (total_base * symbol_price)
    
    prices_time_utc = time.strftime('%Y-%m-%d %H:%M', time.gmtime(prices_time/1000))
    df.side = df.side.replace([1, -1], ['BUY', 'SELL'])
    df.reset_index(drop=True, inplace=True)


    if showlog :
        if df.empty:
            print(f"No trades found for {symbol} from {start_date} till {end_date}")
        else: 
            print(f"\nTrades gathered for {symbol}:")

        print(f"Summary for {symbol} for period [{start_date} - {end_date}]:")
        print(f"   Days: {days}")
        print(f"   Trades executed: {df.time.count()}")
        print(f"   Total volume traded ({asset_quote}): {round(total_volume, 8)}")
        print(f"   Average buy price: {round(average_buy, 8)}")
        print(f"   Average sell price: {round(average_sell, 8)}")
        print(f"\nTrading delta:")
        print(f"   Delta {asset_base}: {round(delta_base, 8)}")
        print(f"   Delta {asset_quote}: {round(delta_quote, 8)}")
        print(f"\nFees:")
        print(f"   Fees {asset_base}: {round(fee_base, 8)}")
        print(f"   Fees {asset_quote}: {round(fee_quote, 8)}")
        print(f"   Fees BNB: {round(fee_bnb, 8)}")
        print(f"\nPrices at the end of the period [{prices_time_utc}]:")
        print(f"   Price {symbol}: {symbol_price}")
        print(f"   Price {asset_quote}USDT: {usd_price}")
        print(f"   Price BNB{asset_quote}: {bnb_price}")
        print(f"\nTotal profit:")
        print(f"   Total profit ({asset_base}): {round(total_base, 8)}, , {round(total_percent, 2)}%")
        print(f"   Total profit ({asset_quote}): {round(total_quote, 8)}")

    time.sleep(1)
    
    return  {
        'days':days,
        'trades_executed':df.time.count(),
        'average_buy_price': round(average_buy, 8),
        'average_sell_price': round(average_sell, 8),
        'delta_asset_base': round(delta_base, 8),
        'delta_asset_quote': round(delta_quote, 8),
        'fees_asset_base': round(fee_base, 8),
        'fees_asset_quote': round(fee_quote, 8),
        'fees_bnb': round(fee_bnb, 8),
        'base_price_end_of_period': symbol_price,
        'quote_price_end_of_period': usd_price,
        'bnb_price_end_of_period':bnb_price,
        'total_profit(quote)': round(total_quote, 8),
        'total_profit(base)' : round(total_base, 8),
        'total_volume_traded': round(total_volume, 8),
        'trades':df,
    }