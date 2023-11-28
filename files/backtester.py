import pandas as pd
import backtrader as bt
import backtrader.indicators as btind
import datetime
import math

import tools

%matplotlib inline

class ForceIndex(bt.Indicator):
    lines = ('fi', )
    params = (('ema', 2), )
    
    def __init__(self):
        self.lines.fi = btind.EMA(((self.data.close(0) - self.data.close(-1))*self.data.volume), period=self.params.ema)
        
class TenDayMARule(bt.Indicator):
    lines = ('hcl_ma', 'upper', 'lower')
    params = (('period', 10),)
    
    def __init__(self):
        self.l.hcl_ma = btind.SMA((self.data.low + self.data.close + self.data.high)/3, period=self.p.period)
        self.hl_range = btind.SMA((self.data.high - self.data.low), period=self.p.period)
        
    def next(self):
        self.l.upper[0] = self.l.hcl_ma[0] + self.hl_range[0]
        self.l.lower[0] = self.l.hcl_ma[0] - self.hl_range[0]

class DivergenceIndex(bt.Indicator):
    lines = ('di', 'upper', 'lower')
    params = (
        ('ma_1', 40), 
        ('ma_2', 10), 
        ('mom', 1),
        ('factor', 1.0)
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        
        self.ma1 = btind.SMA(self.data, period=self.p.ma_1)
        self.ma2 = btind.SMA(self.data, period=self.p.ma_2)
        self.momentum = btind.Momentum(self.data, period=self.p.mom)
        
        self.stdev = btind.StdDev(self.momentum, period=self.p.ma_1)
    
    def next(self):
        if self.stdev[0] != 0:
            self.l.di[0] = (self.ma2[0] - self.ma1[0])/self.stdev[0]
        else: 
            self.l.di[0] = 0.0
        self.l.upper[0] = self.p.factor*self.stdev[0]
        self.l.lower[0] = -self.p.factor*self.stdev[0]
        
class Ten_Day_MA_Rule(bt.Strategy):
    params = (
        ('period', 10),
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.TDMAR = TenDayMARule(self.data, period=self.p.period)
        
    def next(self):
        if not self.position:
            if self.data.high[0] > self.TDMAR.l.upper[0]:
                self.position_size = math.floor((self.broker.get_value()/self.dataclose[0])*0.99)
                self.order = self.buy(size=self.position_size)
        else:
            if self.data.low[0] < self.TDMAR.l.lower[0]:
                self.order = self.sell(size=self.position_size)
                
class CombinationStrategy(bt.Strategy):
    
    params = (
        ('w_ema', 7),
        ('d_ema', 22),
        ('szsdf_coeff', 1),
        ('risk_per_trade', 0.02),
        ('channel_coeff', 0.99),
        ('lb', 33),
        ('rsi_period', 13)
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        
        self.daily_ema = btind.EMA(self.data, period=self.p.d_ema)
        self.forceindex = ForceIndex()
        self.rsi = btind.RSI_EMA(self.data, period=self.p.rsi_period)
        
        self.weekly_ema = btind.EMA(self.datas[1], period=self.p.w_ema)
        self.weekly_macd = btind.MACDHistogram(self.datas[1])
        
        self.prices_df = pd.DataFrame(columns=['High', 'Low', 'EMA'])
        
    def next(self):
        self.prices_df = self.prices_df.append({'High':self.datas[0].high[0],'Low':self.datas[0].low[0],'EMA':self.daily_ema[0]}, ignore_index=True)
        
        if not self.position:
            if self.weekly_ema[0] > self.weekly_ema[-1] and self.weekly_macd[0] > self.weekly_macd[-1]:
                if self.forceindex[0] < 0 and self.rsi[0] < 80:
                    self.rps = sak.szsdf(self.prices_df['Low'], self.p.szsdf_coeff, self.p.lb)
                    if self.rps != 0:
                        self.coeff = sak.ccf(self.prices_df, self.p.channel_coeff)
                        self.ratio = (self.coeff*self.daily_ema[0])/self.rps
                        if self.ratio > 2:                             
                            self.order_size = sak.no_of_shares(self.broker.getvalue(), self.p.risk_per_trade, self.rps, self.dataclose[0])
                            self.order = self.buy(size=self.order_size)
                            self.stop_price = self.dataclose[0] - self.rps
        else:
            if self.datas[0].low < self.stop_price:
                self.order = self.sell(size=self.order_size)
            elif self.datas[0].high > self.daily_ema[0]*(1+self.coeff):
                self.order = self.sell(size=self.order_size)

class MACrossover(bt.Strategy):
    params = (
        ('w_ema', 13),
        ('d_ema1', 22),
        ('d_ema2', 11),
        ('szsdf_coeff', 1),
        ('risk_per_trade', 0.02),
        ('channel_coeff', 0.99),
        ('lb', 33)
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        
        self.daily_ema1 = btind.EMA(self.data, period=self.p.d_ema1)
        self.daily_ema2 = btind.EMA(self.data, period=self.p.d_ema2)
        
        self.weekly_ema = btind.EMA(self.datas[1], period=self.p.w_ema)
        self.macd = btind.MACDHistogram(self.datas[1])
        
        self.prices_df = pd.DataFrame(columns=['High', 'Low', 'EMA'])
        
    def next(self):
        self.prices_df = self.prices_df.append({'High':self.datas[0].high[0],'Low':self.datas[0].low[0],'EMA':self.daily_ema1[0]}, ignore_index=True)
        
        if not self.position:
            if self.weekly_ema[0] > self.weekly_ema[-1] and self.macd[0] > self.macd[-1]:
                if self.daily_ema1[0] < self.daily_ema2[0] and self.daily_ema1[-1] > self.daily_ema2[-1]: 
                    self.rps = sak.szsdf(self.prices_df['Low'], self.p.szsdf_coeff, self.p.lb)
                    if self.rps != 0:
                        self.coeff = sak.ccf(self.prices_df, self.p.channel_coeff)
                        self.ratio = (self.coeff*self.daily_ema1[0])/self.rps
                        if self.ratio > 2:                             
                            self.order_size = sak.no_of_shares(self.broker.getvalue(), self.p.risk_per_trade, self.rps, self.dataclose[0])
                            self.order = self.buy(size=self.order_size)
                            self.stop_price = self.dataclose[0] - self.rps
        else:
            if self.datas[0].low < self.stop_price:
                self.order = self.sell(size=self.order_size)
            elif self.datas[0].high > self.daily_ema1[0]*(1+self.coeff):
                self.order = self.sell(size=self.order_size)

class Simple_Momentum(bt.Strategy):
    params = (
        ('period', 12),
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.mom = btind.Momentum(self.data, period=self.p.period)
    
    def next(self):
        if not self.position:
            if self.mom[0] > 0:
                self.position_size = math.floor((self.broker.get_value()/self.dataclose[0])*0.99)
                self.order = self.buy(size=self.position_size)   
        else:
            if self.mom[0] < 0:
                self.order = self.sell(size=self.position_size)
                
class Volatility_System(bt.Strategy):
    params = (
        ('period', 14),
        ('coefficient', 3),
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        
        self.average_true_range = btind.ATR(self.data, period=self.p.period)
    
    def next(self):
        if not self.position:
            if (self.dataclose[0]-self.dataclose[-1]) > (self.p.coefficient*self.average_true_range[-1]):
                self.position_size = math.floor((self.broker.get_value()/self.dataclose[0]) * 0.99)
                self.order = self.buy(size=self.position_size)
        else:
            if (self.dataclose[-1]-self.dataclose[0]) > (self.p.coefficient*self.average_true_range[-1]):
                self.order = self.sell(size=self.position_size)
                
class TRIX_Strategy(bt.Strategy):
    params = (
        ('period', 15),
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.trix = btind.TRIX(self.data, period=self.p.period)
    
    def next(self):
        if not self.position:
            if self.trix[0] > self.trix[-1] and self.trix[-1] > self.trix[-2]:
                self.position_size = math.floor((self.broker.get_value()/self.dataclose[0]) * 0.99)
                self.order = self.buy(size=self.position_size)
        else:
            if self.trix[0] < self.trix[-1] and self.trix[-1] < self.trix[-2]:
                self.order = self.sell(size=self.position_size)
                
class MovingAverageOscillator(bt.Indicator):
    lines = ('oscillator', )
    params = (('ma_1', 22), ('ma_2', 11))
    
    def __init__(self):
        self.ma1 = btind.SMA(self.data, period=self.p.ma_1)
        self.ma2 = btind.SMA(self.data, period=self.p.ma_2)
    
    def next(self):
        self.l.oscillator[0] = self.ma2[0] - self.ma1[0]
        
class Raschke_First_Cross_System(bt.Strategy):
    params = (
        ('trend_period', 4),
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        
        self.osc = MovingAverageOscillator()
        self.trend = btind.SMA(self.osc, period=self.p.trend_period)
    
    def next(self):
        if not self.position:
            if self.osc[-1] > self.trend and self.osc[0] <= self.trend:
                if self.datas[0].low[-1] < self.datas[0].low[0]:
                    self.position_size = math.floor((self.broker.get_value()/self.dataclose[0]) * 0.99)
                    self.order = self.buy(size=self.position_size)
        
        else:
            if self.dataclose[-1] > self.dataclose[-2] and self.dataclose[0] < self.dataclose[-1]:
                self.order = self.sell(size=self.position_size)
class Two_MA(bt.Strategy):
    params = (
        ('ma_1', 22),
        ('ma_2', 11)
    )
    def __init__(self):
        self.dataclose = self.datas[0].close
        
        self.ma1 = btind.SMA(self.data, period=self.p.ma_1)
        self.ma2 = btind.SMA(self.data, period=self.p.ma_2)
        
    def next(self):   
        if not self.position:
            if self.dataclose[0] > self.ma1[0] and self.dataclose[0] > self.ma2[0]:
                self.position_size = math.floor((self.broker.get_value()/self.dataclose[0]) * 0.99)
                self.order = self.buy(size=self.position_size)
                
        else:
            if self.dataclose[0] < self.ma1[0] or self.dataclose[0] < self.ma2[0]:
                self.order = self.sell(size=self.position_size)
                
class Donchian_MA_System(bt.Strategy):
    params = (
        ('ma_1', 5),
        ('ma_2', 20)
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        
        self.ma1 = btind.SMA(self.data, period=self.p.ma_1)
        self.ma2 = btind.SMA(self.data, period=self.p.ma_2)
        self.atr = btind.ATR(self.data, period=self.p.ma_2)
        
    def next(self):
        if not self.position:
            if self.dataclose[0] > self.ma1[-1] and (self.dataclose[0] > (self.ma2[-1] + self.atr[-1])):
                self.position_size = math.floor((self.broker.get_value()/self.dataclose[0]) * 0.99)
                self.order = self.buy(size=self.position_size)
                
        else:
            if (self.dataclose[0] < (self.ma1[-1] - self.atr[-1])) or (self.dataclose[0] < (self.ma2[-1] - self.atr[-1])):
                self.order = self.sell(size=self.position_size)
                
class Divergence_Index(bt.Strategy):
    params = (('ma', 22),)
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        
        self.ma = btind.SMA(self.data, period=self.p.ma)
        self.DI = DivergenceIndex()
    
    def next(self):
        if not self.position:
            if self.DI.l.di[0] != 0:
                if self.ma[0] > self.ma[-1] and self.DI.l.di[0] < self.DI.l.lower[0]:
                    self.position_size = math.floor((self.broker.get_value()/self.dataclose[0]) * 0.99)
                    self.order = self.buy(size=self.position_size)
        else:
            if self.DI.l.di[0] > 0 and self.DI.l.di[-1] < 0:
                self.order = self.sell(size=self.position_size)
                
if __name__ == "__main__":
    #insert path names to read ticker list and data from
    #path1 = 
    #path2 = 

    start = datetime.datetime(2009,1,1)
    end = datetime.date.today()
    
    fd = open(path2, 'a')
    fd.write('TIDM,strat\n')
    fd.close()

    tickers = pd.read_csv(path1)
    
    for i in tickers.index:
    try:
        symbol = tickers.TIDM[i]
        #insert path to write results file to
        path3 = '' % symbol
        data = pd.read_csv(path3, index_col=0, parse_dates=True)

        first = pd.Timestamp(data.index.values[0])

        if first > start and first <= end.replace(year=end.year - 1):
            data = data.loc[first:end]      
        elif first < start:
            data = data.loc[start:end]

        ticks_feed = bt.feeds.PandasData(dataname=data)

        cerebro = bt.Cerebro(stdstats=False)
        cerebro.addstrategy(Combo_Strategy)
        cerebro.broker.setcash(100000.0)

        cerebro.adddata(ticks_feed)
        cerebro.resampledata(ticks_feed, timeframe=bt.TimeFrame.Weeks)

        cerebro.run()

        fd = open(path2, 'a')
        fd.write(f'{symbol},{round(cerebro.broker.getvalue(), 2)}\n')
        fd.close()

        if ((i+1) % 100) == 0:  
            print(f'###### Done {i+1}')
    except Exception as ex:
        pass
    
    results = pd.read_csv(path2)
    results = results[results.strat != 100000.0].dropna()
    positive = results[results['strat'] > 100000.0]
    ratio = round(len(positive.index)/len(results.index), 4)
    print(ratio)
    results['growth'] = (results['strat'] - 100000.0) / 100000.0
    mean_growth = round(results['growth'].sum()/len(results.index), 2)
    print(mean_growth)