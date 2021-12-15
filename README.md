# Getting Profit and Loss Make Easy From Binance

I have been in Binance Automated Trading for some time and have generated a lot of transaction records, so I want to see my historical profit and loss records (for each cryptocurrency). But Binance does not provide this information.

After searching for a period of time, various useful code sections were integrated, and then presented graphically with Poltly.

The usage is very simple, just follow the following operations to get the total profit and loss in historical.

# Requirement

python-binance

```
pip install python-binance
```

plotly

```
pip install plotly==4.14.3
```

jupyter-dash

```
pip install jupyter-dash
```

# Usage

```
from calcuation import profit_loss
from chart import RealizedProfitLoss
from binance.client import Client
import pandas as pd

key = 'Your API Key'
secret = 'Yout Secert Key'

client = Client(key, secret)
```

#### Get the profit and loss of BTCUSDT from 2020-01-01 to 2021-12-21

```
pnl = profit_loss(market='BNB-USDT', client=client, showlog=True)
```

![output](/output.PNG)

#### Get the profit and loss chart of [crypto pair] every 30 days from 2020-01 to 2021-12

```
from datetime import datetime

dates_df = pd.DataFrame(index=[datetime(2020,1,1), datetime(2021,12,31)])
dates = dates_df.resample('d').first().index[::30]
profilio = []
for s in ['BTC-USDT', 'BNB-USDT', 'LINK-USDT', 'ADA-USDT', 'CAKE-USDT', 'UNI-USDT', 'ETH-USDT']:        
    for start_date, end_date in zip(dates[:], dates[1:]):        
        pnl = profit_loss(market=s, start_date=start_date.strftime("%Y-%m-%d"), end_date=end_date.strftime("%Y-%m-%d"), client=client)
        profilio.append({'date': end_date, 'symbol':s, 'pnl':pnl['total_profit(quote)']})    
    
profilio_df = pd.DataFrame(profilio)
profilio_df = profilio_df.rename({'symbol':'stock_id'}, axis='columns')    
RealizedProfitLoss(profilio_df).run_dash()
```

![Pnl DashBoard](/dashboard.png)
