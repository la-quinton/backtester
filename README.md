# Trading Strategy Backtester
Quinton La

Built with: Python, specifically using the pandas and backtrader libraries

# Folders
files: contains the code developed
  - data_miner.py: given a start and end date, this code takes a list of tickers and downloads the pricing data 
  - backtester.py: the main code that handles the logic for each strategy and tests each strategy over a given timeframe and share list. Also handles the calculation of the results.
  - tools.py: miscellaneous tools that are used within the backtester.py file to calculate parameters such as entry points and trade volume sizes.
