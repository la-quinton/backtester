import pandas as pd
import yfinance as yf

#tickers = pd.read_csv('')
start_date = '2009-01-01'

for i in tickers.index:
    try:  
        symbol = tickers.TIDM[i]
        data = yf.download(symbol, start=start_date, progress=False, auto_adjust=True)
        #data.to_csv('' % symbol, encoding='utf-8')

        if (i+1) % 100 == 0:
            print(f'##### Done {i+1}')
            
    except Exception as ex:
        print(f"Something else went wrong with {symbol}: {ex}")