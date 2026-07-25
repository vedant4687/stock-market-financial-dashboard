import yfinance as yf
import pandas as pd

# 75 stocks across 12 sectors
stocks = {
    'Indian Banking & Finance': [
        'HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 
        'AXISBANK.NS', 'BAJFINANCE.NS', 'KOTAKBANK.NS', 'INDUSINDBK.NS'
    ],
    'Indian IT': [
        'TCS.NS', 'INFY.NS', 'WIPRO.NS', 'HCLTECH.NS', 
        'TECHM.NS', 'MPHASIS.NS', 'PERSISTENT.NS'
    ],
    'Indian Industry & Conglomerates': [
        'RELIANCE.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 
        'ADANIENT.NS', 'MARUTI.NS', 'ULTRACEMCO.NS'
    ],
    'Indian Pharma': [
        'SUNPHARMA.NS', 'DRREDDY.NS', 'CIPLA.NS', 
        'DIVISLAB.NS', 'AUROPHARMA.NS'
    ],
    'Indian Telecom & Consumer': [
        'BHARTIARTL.NS', 'HINDUNILVR.NS', 'NESTLEIND.NS', 
        'TITAN.NS', 'DMART.NS'
    ],
    'US Tech': [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 
        'NVDA', 'META', 'TSLA', 'AMD'
    ],
    'US Finance': [
        'JPM', 'GS', 'BAC', 'V', 'MA'
    ],
    'US Healthcare': [
        'JNJ', 'PFE', 'ABBV', 'MRK', 'UNH'
    ],
    'Energy': [
        'ONGC.NS', 'POWERGRID.NS', 'NTPC.NS', 'XOM', 'CVX', 'BP'
    ],
    'Aviation & Travel': [
        'INDIGO.NS', 'DAL', 'UAL', 'MAR'
    ],
    'Real Estate': [
        'DLF.NS', 'GODREJPROP.NS', 'PLD', 'AMT'
    ],
    'Global Mixed': [
        'NFLX', 'BABA', 'TSM', 'ASML', 'SAP', 'TM', 'BHP'
    ]
}

# Flatten stocks list with sector mapping
ticker_sector = {}
all_tickers = []
for sector, tickers in stocks.items():
    for ticker in tickers:
        ticker_sector[ticker] = sector
        all_tickers.append(ticker)

print(f"Fetching data for {len(all_tickers)} stocks from 2016 to 2026...")

# Download all at once
raw = yf.download(all_tickers, start='2016-01-01', end='2026-01-01', group_by='ticker', auto_adjust=True)

# Reshape to flat format
all_data = []
failed = []

for ticker in all_tickers:
    try:
        temp = raw[ticker].copy()
        temp['Ticker'] = ticker
        temp['Company'] = ticker.replace('.NS', '')
        temp['Sector'] = ticker_sector[ticker]
        temp.reset_index(inplace=True)
        all_data.append(temp)
        print(f"OK: {ticker} — {len(temp)} rows")
    except Exception as e:
        print(f"FAILED: {ticker} — {e}")
        failed.append(ticker)

# Combine all
final_df = pd.concat(all_data, ignore_index=True)

# Add calculated columns
print("\nCalculating metrics...")
final_df = final_df.sort_values(['Ticker', 'Date'])

final_df['Daily_Return_%'] = final_df.groupby('Ticker')['Close'].pct_change() * 100

# Forward fill missing Close values per ticker
final_df['Close'] = final_df.groupby('Ticker')['Close'].transform(lambda x: x.ffill())

final_df['MA_20'] = final_df.groupby('Ticker')['Close'].transform(
    lambda x: x.rolling(window=20, min_periods=20).mean()
)
final_df['MA_50'] = final_df.groupby('Ticker')['Close'].transform(
    lambda x: x.rolling(window=50, min_periods=50).mean()
)
final_df['MA_200'] = final_df.groupby('Ticker')['Close'].transform(
    lambda x: x.rolling(window=200, min_periods=200).mean()
)
final_df['Cumulative_Return_%'] = final_df.groupby('Ticker')['Close'].transform(lambda x: (x / x.iloc[0] - 1) * 100)
final_df['Volatility_20d'] = final_df.groupby('Ticker')['Daily_Return_%'].transform(lambda x: x.rolling(20).std())

# Round
final_df = final_df.round(2)

# Save
output_file = 'stock_data.xlsx'
final_df.to_excel(output_file, index=False)

print(f"\n Done!")
print(f"Total rows: {len(final_df)}")
print(f"Columns: {list(final_df.columns)}")
print(f"Failed tickers: {failed if failed else 'None'}")
print(f"Saved to: {output_file}")
print(final_df['Ticker'].value_counts())