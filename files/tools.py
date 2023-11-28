import pandas as pd
import math

def ccf(prices, perc):
    coef = 0
    
    if len(prices.index) >= 100:
        prices = prices.tail(100)
    
    for i in range (1, 1001):
        result_list = (prices['High'] > (prices['EMA']*(1+i*0.001))) | (prices['Low'] < (prices['EMA']*(1-i*0.001)))
        ratio = (result_list.sum())/(len(result_list.index))
        if ratio < (1-perc):
            coef = round(i*0.001, 3)
            break
            
    return coef

def szsdf(lows, coef, look_back):
    if len(lows.index) < look_back:
        diff_list = lows.diff().tolist()
        negatives = [x for x in diff_list if x < 0]
        if len(negatives) == 0:
            return 0
        else:
            return round(-((sum(negatives) / len(negatives)) * coef), 2)
    else:
        prices = lows.tail(look_back + 1)
        diff_list = lows.tail(look_back).diff().tolist()
        negatives = [x for x in diff_list if x < 0]
        if len(negatives) == 0:
            return 0
        else:
            return round(-((sum(negatives) / len(negatives)) * coef), 2)

def no_of_shares(portfolio, risk, risk_per_share, close):
    shares = math.floor((portfolio*risk)/risk_per_share)
    if (shares * close) < portfolio:
        return shares
    else:
        return math.floor((0.9*portfolio)/close)
    
def plus_ev(data, val):
    positive = data[data >= val].dropna()
    return round((len(positive)*100)/len(data.index), 3)

def pnl(prices, initial_portfolio):
    prices['pnl'] = prices['strat'] - initial_portfolio
    mean_pnl = (prices[prices['pnl'] != 0].dropna())['pnl'].mean()
    return round((mean_pnl*100)/initial_portfolio, 3)

def entry_price(prices, col, ratio):
    if len(prices.index) >= 21:
        prices = prices.tail(21)
        
    prices['pens'] = prices[col] - prices['Low']
    pen_list = prices[prices['pens'] > 0]['pens'].dropna().tolist()
    if len(pen_list) == 0:
        return 0
    else:
        average_pen = (sum(pen_list)/len(pen_list))
        return round(prices[col].iloc[-1] - average_pen/ratio, 2)

def entry_price2(prices, col, ratio):
    if len(prices.index) >= 20:
        prices = prices.tail(20)
    prices['pens'] = prices[col] - prices['Low']
    pen_list = prices[prices['pens'] > 0]['pens'].dropna().tolist()
    if len(pen_list) == 0:
        return 0
    else:
        average_pen = (sum(pen_list)/len(pen_list))
        return round((2*prices[col].iloc[-1] - prices[col].iloc[-2] - average_pen/ratio), 2)