#backtest.py
import os
import sys
import datetime
import backtrader as bt
import pandas as pd
import yfinance
from sqlalchemy import create_engine

DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise RuntimeError("DB_URL must be set in the environment for backtest metrics write")


#Point at project root so Python can find data_ingestion/
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(proj_root, 'data_ingestion'))

#Import ingestion function (which handles pagination, API‑key, etc.)
from ingestion import fetch_agg_bars 

# 3) Pull two years of data as a list of dicts
start_iso = '2023-01-01'
end_iso   = '2025-01-01'
raw_bars  = fetch_agg_bars('AAPL', start_iso, end_iso)

# Convert to DataFrame with a DateTimeIndex and OHLCV columns
df = pd.DataFrame(raw_bars)
df['t']   = pd.to_datetime(df['t'], unit='ms')  # Polygon uses epoch ms
df.set_index('t', inplace=True)
df.rename(columns={
    'o': 'open', 'h': 'high', 'l': 'low',
    'c': 'close','v': 'volume'
}, inplace=True)

#Feed into Backtrader
data = bt.feeds.PandasData(dataname=df)

#Define strategy
class ParamStrategy(bt.Strategy):
    params = (('maperiod', 5),)

    def __init__(self):
        self.sma = bt.indicators.SMA(self.data.close, period=self.p.maperiod)

    def next(self):
        if not self.position:
            if self.data.close[0] > self.sma[0]:
                self.buy()
        elif self.data.close[0] < self.sma[0]:
            self.sell()

class MeanReversionStrategy(bt.Strategy):
    #SMA window, stf-devs from mean to trigger
    params = (('maperiod', 5), ('devfactor', 1.0))

    def __init__(self):
        self.sma = bt.indicators.SMA(self.data.close, period=self.p.maperiod)
        self.std = bt.indicators.StandardDeviation(self.data.close, period=self.p.maperiod)

    def next(self):
        price = self.data.close[0]
        ma = self.sma[0]
        sd = self.std[0]
        zscore = (price - ma) / sd if sd else 0.0
                
        # no position → enter when price is far from mean
        if not self.position:
            if zscore >  self.p.devfactor:
                self.sell()   # short when price too high
            elif zscore < -self.p.devfactor:
                self.buy()    # long when price too low

        # in a position → exit once closer to mean
        else:
            if abs(zscore) < 0.1:  # small buffer to avoid chop
                self.close()


if __name__ == '__main__':
    start_cash = 10000
    run_id = datetime.date.today().isoformat()
    results = []

    for strat_cls in (ParamStrategy, MeanReversionStrategy):
        strat_name = strat_cls.__name__
        for maperiod in range(5, min(len(df) // 2, 250), 5):
            cerebro = bt.Cerebro()
            params = {'maperiod': maperiod}
            if strat_cls is MeanReversionStrategy:
                params['devfactor'] = 1.0

            cerebro.addstrategy(strat_cls, **params)
            data_feed = bt.feeds.PandasData(
                dataname=df,
                timeframe=bt.TimeFrame.Days,
                compression=1
            )
            cerebro.adddata(data_feed)
            cerebro.broker.setcash(start_cash)

            cerebro.addanalyzer(
                bt.analyzers.SharpeRatio,
                _name='sharpe',
                timeframe=bt.TimeFrame.Days,
                compression=1,
                riskfreerate=0.0
            )
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

            strat = cerebro.run()[0]
            end_value = cerebro.broker.getvalue()
            pnl = end_value - start_cash

            sharpe = strat.analyzers.sharpe.get_analysis().get('sharperatio', None)
            max_dd = strat.analyzers.drawdown.get_analysis()['max']['drawdown']

            results.append({
                'run_id': run_id,
                'Strategy': strat_name,
                'maperiod': maperiod,
                'PnL': (pnl / start_cash) * 100,
                'Sharpe': sharpe,
                'Max Drawdown': max_dd * 100
            })

    # Final DataFrame
    results_df = pd.DataFrame(results)

    engine = create_engine(DB_URL)

    results_df.columns = (
        results_df.columns
        .str.strip()               # remove whitespace
        .str.lower()               # everything lowercase
        .str.replace(' ', '_')     # spaces → underscores
    )
    
    results_df.to_sql(
        'backtest_metrics', 
        engine, 
        if_exists='replace', 
        index=False
    )
    print(results_df.sort_values(['strategy','sharpe'], ascending=[True, False]))