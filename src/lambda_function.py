from main import Trader

trader = Trader()

def lambda_handler(event, context):
    trader.rebalance()