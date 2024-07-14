import backtrader as bt
import pandas as pd
import os

# Create a Stratey
class MovingAverage(bt.Strategy):
    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        print('init')
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = {d: d.close for d in self.datas}

        # To keep track of pending orders and buy price/commission
        self.orders = {d: None for d in self.datas}
        self.buyprice = None
        self.buycomm = None

        # Add a MovingAverageSimple indicator
        self.smaSmall = bt.indicators.ExponentialMovingAverage(
            self.datas[0], period=50)
        
        self.smaLarge = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=200)
        
        self.Highest = {d: bt.indicators.Highest(d, period=100) for d in self.datas}
        self.HighestLarge = {d: bt.indicators.Highest(d, period=200) for d in self.datas}
        # self.will = bt.indicators.WilliamsR(self.datas[0], period=100)
        # self.Rsi = bt.indicators.RelativeStrengthIndex()
        # self.Trix = bt.indicators.Trix()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                print('On ', order.data.datetime.date(0), ' Bought: ', order.size, 'shares of ', order.data._name, ' at ', order.executed.price, ' - total: ', order.executed.price * order.executed.size)
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                print('remaining cash2: ', self.broker.get_cash())
            else:
                print('On ', order.data.datetime.date(0), ' Sold: ', order.size, 'shares of ', order.data._name, ' at ', order.executed.price, ' - total: ', order.executed.price * order.executed.size)
            self.bar_executed = len(self)
        
        # Write down: no pending order
        self.orders[order.data] = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f, ON %s' %
                 (trade.pnl, trade.pnlcomm, trade.tradeid))

    def next(self):
        for data in self.datas:
          # Check if an order is pending ... if yes, we cannot send a 2nd one
          if self.orders[data]:
              return
          
          cash = self.broker.get_cash()
          size = 1000 / data.close[0]
          # print(self.positions[data])
          # Check if we are in the market
          if not self.positions[data]:
              # Not yet ... we MIGHT BUY if ...
              if self.dataclose[data] <= self.Highest[data] * .75 and cash > 2000:
                  # Keep track of the created order to avoid a 2nd order
                  self.orders[data] = self.buy(size=size, data=data)
                  print('remaining cash: ', self.broker.get_cash())
          else:
              if self.dataclose[data] > self.positions[data].price and (self.dataclose[data] >= self.HighestLarge[data]*.95 or self.dataclose[data] > 2*self.positions[data].price):
                  # Keep track of the created order to avoid a 2nd order
                  self.orders[data] = self.sell(size=self.positions[data].size, data=data)

# daily = pd.read_csv("AAPL_2.csv", index_col=0, parse_dates=True)
# data = bt.feeds.PandasData(
#     dataname=
#     daily.sort_index()
#     )

cerebro = bt.Cerebro()
cerebro.broker.setcash(100000.0)
cerebro.addsizer(bt.sizers.FixedSize, stake=1000)
cerebro.broker.setcommission(commission=0.001)

i = 0
for filename in os.listdir('stock_list_1yr'):
    i+=1
    # if i < 5: continue
    daily =pd.read_csv("stock_list_1yr/"+filename, index_col=0, parse_dates=True)
    if daily.index[0] > pd.Timestamp('2016-01-01'): 
        continue
    data = bt.feeds.PandasData(dataname = daily.sort_index(), name=filename)
    
    cerebro.adddata(data)
    # if i > 10: break
# cerebro.adddata(data)
cerebro.addstrategy(MovingAverage)


print("Starting Portfolio Value: %.2f" % cerebro.broker.getvalue())

cerebro.run()


print("Final Portfolio Value: %.2f" % cerebro.broker.getvalue())
# cerebro.plot()
