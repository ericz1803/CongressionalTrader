from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from collections import Counter
import datetime

from capitoltrades import CapitolTrades

import os

class Trader():
    def __init__(self, num_stocks=10, window=100):
        self.window = window
        self.num_stocks = num_stocks
        self.trades = CapitolTrades.CapitolTrades()
        self.api_key = os.environ['ALPACA_API_KEY']
        self.api_secret = os.environ['ALPACA_API_SECRET']
        self.trading_client = TradingClient(self.api_key, self.api_secret, paper=True)
        self.stocks_to_trade = []

    def get_stocks_to_trade(self):
        # get stocks to trade
        trade_values = Counter()
        today = datetime.datetime.utcnow().date()
        for trade in self.trades.data:
            if trade['asset']['assetType'] == 'stock':
                ticker = trade['asset']['assetTicker']
                value = trade['value']
                pubDate = trade['pubDate']
                txDate = datetime.datetime.strptime(trade['txDate'], '%Y-%m-%d').date()
                txType = trade['txType']
                
                days_difference = (today - txDate).days
                
                if days_difference <= self.window:
                    # print(pubDate, txDate, ticker, value, txType)
                    if txType == 'sell':
                        trade_values[ticker] -= value
                    elif txType == 'buy':
                        trade_values[ticker] += value
                    else:
                        # print("PROBLEM", trade)
                        pass
                else:
                    # print("OLD", pubDate, txDate, ticker, value, txType)
                    pass

        # get most common stocks
        for (stock_ticker, most_common) in trade_values.most_common():
            if len(self.stocks_to_trade) >= self.num_stocks or most_common <= 0:
                break
            ticker = stock_ticker[:-3]
            try:
                asset = self.trading_client.get_asset(ticker)
                if asset and asset.tradable:
                    if asset.fractionable:
                        self.stocks_to_trade.append((ticker, most_common))
                    else:
                        print(ticker, "is tradable but not fractionable.")
                else:
                    print(ticker, "is not tradable.")
            except:
                print(ticker, "not found.")

        # calculate fraction of portfolio for each stock
        total_val = sum(val for (stock, val) in self.stocks_to_trade)
        self.stocks_to_trade = [(stock, val/total_val) for (stock, val) in self.stocks_to_trade]


    def rebalance(self):
        self.get_stocks_to_trade()
        print("Target stocks distribution:", self.stocks_to_trade)

        self.trading_client.close_all_positions(True)
        account = self.trading_client.get_account()
        account_bp = round(min(float(account.buying_power), float(account.equity)) * 0.999, 2)
        print("Target buy value", account_bp)
        total_money = account_bp
        total_spent = 0
        for (stock, val) in self.stocks_to_trade:
            buy_amt = round(val * total_money, 2)
            total_spent += buy_amt
            print(f"Buying ${buy_amt:.2f} of {stock}")
            market_order_data = MarketOrderRequest(
                symbol=stock,
                notional=buy_amt,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )

            market_order = self.trading_client.submit_order(
                order_data=market_order_data
            )

        print(f"Attempted to buy ${total_spent} worth of stocks.") 

trader = Trader()
def rebalance():
    trader.rebalance()

if __name__ == '__main__':
    rebalance()
