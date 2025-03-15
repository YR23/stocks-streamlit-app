import os
import yfinance as yf
import pandas as pd
import boto3
import botocore

# Use an official source for S&P 500 tickers (from the datasets repo)
def get_sp500_tickers():
    url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
    df = pd.read_csv(url)
    tickers = df["Symbol"].tolist()
    # Replace dots with dashes (e.g., BRK.B becomes BRK-B) for yfinance compatibility
    tickers = [ticker.replace('.', '-') for ticker in tickers]
    return tickers

# AWS S3 configuration: retrieve credentials from environment variables
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_KEY")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "stocks-streamlit")
# For daily data, we use a subfolder "data/1d/"
PREFIX = 'data/1d/'

# Initialize the S3 client
s3 = boto3.client('s3',
                  aws_access_key_id=AWS_ACCESS_KEY,
                  aws_secret_access_key=AWS_SECRET_KEY)

def file_exists_in_s3(bucket, key):
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            return False
        else:
            raise

def update_symbol_daily(symbol):
    key = f"{PREFIX}{symbol}.csv"  # e.g., data/1d/AAPL.csv
    local_filename = f"{symbol}.csv"

    # Check if the CSV exists on S3; if so, download it.
    if file_exists_in_s3(BUCKET_NAME, key):
        s3.download_file(BUCKET_NAME, key, local_filename)
        df_existing = pd.read_csv(local_filename, parse_dates=["Datetime"])
    else:
        df_existing = None

    # Fetch the last 2 years of daily data
    df_new = yf.download(tickers=symbol, period="2y", interval="1d")
    if df_new.empty:
        print(f"No new data available for {symbol}")
        return

    # Extract the latest row and its timestamp
    latest_row = df_new.iloc[-1]
    timestamp = df_new.index[-1]

    # Create a DataFrame from the latest row; reset index so timestamp becomes a column.
    latest_df = pd.DataFrame(latest_row).T
    latest_df.index.name = "Datetime"
    latest_df = latest_df.reset_index()

    # Update the CSV if new data is found
    if df_existing is not None:
        if (df_existing["Datetime"] == timestamp).any():
            print(f"No new daily data for {symbol} (timestamp {timestamp} already exists).")
        else:
            updated_df = pd.concat([df_existing, latest_df], ignore_index=True)
            updated_df.to_csv(local_filename, index=False)
            s3.upload_file(local_filename, BUCKET_NAME, key)
            print(f"Updated {symbol} daily CSV with new data at {timestamp}.")
    else:
        latest_df.to_csv(local_filename, index=False)
        s3.upload_file(local_filename, BUCKET_NAME, key)
        print(f"Created new daily CSV for {symbol} with data at {timestamp}.")

# Retrieve all S&P 500 tickers
symbols = get_sp500_tickers()
print(f"Total tickers: {len(symbols)}")

# Update each symbol
for symbol in symbols:
    try:
        update_symbol_daily(symbol)
    except Exception as e:
        print(f"Error updating {symbol}: {e}")
