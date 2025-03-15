import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.title("S&P 500 Candlestick Dashboard")

# List of S&P 500 symbols
symbols = ['AAPL', 'MSFT', 'AMZN']

data_dict = {}

# Download 1 year of daily data for each symbol
for symbol in symbols:
    df = yf.download(tickers=symbol, period='1y', interval='1d')
    # Flatten the multi-index columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    data_dict[symbol] = df

# Build a single Plotly figure with a dropdown menu for the symbols
fig = go.Figure()

# Add a candlestick trace for each symbol (only one visible at a time)
for i, symbol in enumerate(symbols):
    df = data_dict[symbol]
    df = df.reset_index()
    if not df.empty:
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                increasing_line_color='green',  # Green when close > open
                decreasing_line_color='red',      # Red when close < open
                name=symbol,
                visible=True if i == 0 else False  # Only the first symbol is visible initially
            )
        )
    else:
        st.write(f"No data for {symbol}")

# Create dropdown buttons to switch between symbols
dropdown_buttons = []
for i, symbol in enumerate(symbols):
    visibility = [False] * len(symbols)
    visibility[i] = True
    dropdown_buttons.append(
        dict(
            label=symbol,
            method="update",
            args=[{"visible": visibility},
                  {"title": f"Candlestick Chart for {symbol} - 1 Year of Daily Data"}]
        )
    )

fig.update_layout(
    updatemenus=[dict(
        active=0,
        buttons=dropdown_buttons,
        direction="down",
        x=1.1,
        y=0.8,
        showactive=True,
    )],
    title=f"Candlestick Chart for {symbols[0]} - 1 Year of Daily Data",
    xaxis_title="Datetime",
    yaxis_title="Price",
    xaxis_rangeslider_visible=False,
    template="plotly_white",
    height=700  # Adjust the height of the chart as needed
)

# Remove the gap between trading days (example for US markets trading from 09:30 to 16:00)
fig.update_xaxes(rangebreaks=[dict(bounds=["16:00", "09:30"])])

# Display the figure in the Streamlit app
st.plotly_chart(fig)
