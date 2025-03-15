import os
import yfinance as yf
import pandas as pd
import boto3
import botocore


# Helper function to get S&P 500 tickers from an official dataset on GitHub
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
PREFIX = 'data/1h/'  # Files will be saved under s3://stocks-streamlit/data/1h/

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


def update_symbol_hourly(symbol, period, interval):
    key = f"{PREFIX}{symbol}.csv"  # S3 object key, e.g., data/1h/AAPL.csv
    local_filename = f"{symbol}.csv"

    # Check if the CSV exists in S3; if yes, download it.
    if file_exists_in_s3(BUCKET_NAME, key):
        s3.download_file(BUCKET_NAME, key, local_filename)
        df_existing = pd.read_csv(local_filename)
        df_existing['Datetime'] = pd.to_datetime(df_existing['Datetime'])
        df_existing = df_existing.reset_index(drop=True)
    else:
        df_existing = None

    df_new = yf.download(tickers=symbol, period=period, interval=interval).reset_index()

    if df_new.empty:
        print(f"No new data available for {symbol}")
        return

    if isinstance(df_new.columns, pd.MultiIndex):
        df_new.columns = df_new.columns.get_level_values(0)

    df_new['Datetime'] = pd.to_datetime(df_new['Datetime'])
    df_new = df_new.reset_index(drop=True)

    # Update the CSV if new data is found
    if df_existing is not None:
        updated_df = pd.concat([df_existing, df_new], ignore_index=True)
        updated_df = updated_df.drop_duplicates(subset=['Datetime'])
        updated_df = updated_df.sort_values(by='Datetime')
        updated_df.to_csv(local_filename, index=False)
        s3.upload_file(local_filename, BUCKET_NAME, key)
        print(f"Updated {symbol} hourly CSV with new data.")

    else:
        # Create a new CSV file if it doesn't exist
        df_new.to_csv(local_filename, index=False)
        s3.upload_file(local_filename, BUCKET_NAME, key)
        print(f"Created new hourly CSV for {symbol} with data.")


# Retrieve all S&P 500 tickers
symbols = get_sp500_tickers()
print(f"Total tickers: {len(symbols)}")

interval,period = "60m", "1mo"
# Update each symbol
for symbol in symbols:
    try:
        update_symbol_hourly(symbol=symbol,
                             period=period,
                             interval=interval)
    except Exception as e:
        print(f"Error updating {symbol}: {e}")
