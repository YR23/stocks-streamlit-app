import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.title("Candlestick, 50 EMA, RSI, MACD & Fibonacci Levels")


# Functions to compute RSI and MACD
def compute_RSI(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_MACD(series, span_short=12, span_long=26, span_signal=9):
    ema_short = series.ewm(span=span_short, adjust=False).mean()
    ema_long = series.ewm(span=span_long, adjust=False).mean()
    macd = ema_short - ema_long
    signal = macd.ewm(span=span_signal, adjust=False).mean()
    return macd, signal


# List of S&P 500 symbols
symbols = ['AAPL', 'MSFT', 'AMZN']
data_dict = {}
shapes_dict = {}

# Download one year of daily data for each symbol, compute indicators, and calculate Fibonacci retracement levels
for symbol in symbols:
    df = yf.download(tickers=symbol, period='1y', interval='1d')
    # Flatten multi-index columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    # Compute RSI, MACD, and the 50 EMA
    df['RSI'] = compute_RSI(df['Close'])
    df['MACD'], df['MACD_Signal'] = compute_MACD(df['Close'])
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

    # --- Calculate Fibonacci Retracement Levels ---
    overall_high = df['High'].max()
    overall_low = df['Low'].min()
    diff = overall_high - overall_low
    fib_levels = {
        "0%": overall_high,
        "23.6%": overall_high - 0.236 * diff,
        "38.2%": overall_high - 0.382 * diff,
        "50%": overall_high - 0.5 * diff,
        "61.8%": overall_high - 0.618 * diff,
        "100%": overall_low,
    }

    # Define x-range for the horizontal lines (using the data's date range)
    x0 = df.index.min()
    x1 = df.index.max()

    # Create a list of shapes (horizontal lines) for the Fibonacci levels.
    shapes = []
    for level_name, level_value in fib_levels.items():
        shapes.append(dict(
            type='line',
            xref='x',
            yref='y',
            x0=x0,
            x1=x1,
            y0=level_value,
            y1=level_value,
            line=dict(
                color='grey',
                width=1,
                dash='dash'
            )
        ))
    shapes_dict[symbol] = shapes
    data_dict[symbol] = df

# Create a figure with 3 rows:
# Row 1: Candlestick chart with the 50 EMA and Fibonacci levels,
# Row 2: RSI, and
# Row 3: MACD and MACD Signal.
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.02,
                    row_heights=[0.6, 0.2, 0.2])

# We will add 5 traces per symbol:
# 1. Candlestick (row 1)
# 2. 50 EMA (row 1)
# 3. RSI (row 2)
# 4. MACD (row 3)
# 5. MACD Signal (row 3)
num_traces_per_symbol = 5

for i, symbol in enumerate(symbols):
    df = data_dict[symbol].reset_index()  # Reset index to have a 'Date' column
    # Candlestick trace
    fig.add_trace(
        go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            increasing_line_color='green',
            decreasing_line_color='red',
            name=symbol,
            visible=True if i == 0 else False
        ),
        row=1, col=1
    )
    # 50 EMA trace
    fig.add_trace(
        go.Scatter(
            x=df['Date'],
            y=df['EMA50'],
            mode='lines',
            line=dict(color='magenta', width=2),
            name=f"{symbol} 50 EMA",
            visible=True if i == 0 else False
        ),
        row=1, col=1
    )
    # RSI trace
    fig.add_trace(
        go.Scatter(
            x=df['Date'],
            y=df['RSI'],
            mode='lines',
            line=dict(color='blue'),
            name=f"{symbol} RSI",
            visible=True if i == 0 else False
        ),
        row=2, col=1
    )
    # MACD trace
    fig.add_trace(
        go.Scatter(
            x=df['Date'],
            y=df['MACD'],
            mode='lines',
            line=dict(color='orange'),
            name=f"{symbol} MACD",
            visible=True if i == 0 else False
        ),
        row=3, col=1
    )
    # MACD Signal trace
    fig.add_trace(
        go.Scatter(
            x=df['Date'],
            y=df['MACD_Signal'],
            mode='lines',
            line=dict(color='purple'),
            name=f"{symbol} MACD Signal",
            visible=True if i == 0 else False
        ),
        row=3, col=1
    )

# Total number of traces = number of symbols * num_traces_per_symbol
total_traces = len(symbols) * num_traces_per_symbol

# Create dropdown buttons to switch between symbols.
# Each button updates the visible traces and also updates the layout shapes (the Fibonacci retracement lines).
dropdown_buttons = []
for i, symbol in enumerate(symbols):
    visibility = [False] * total_traces
    start_index = i * num_traces_per_symbol
    for j in range(num_traces_per_symbol):
        visibility[start_index + j] = True
    dropdown_buttons.append(
        dict(
            label=symbol,
            method="update",
            args=[{"visible": visibility},
                  {"title": f"Candlestick, 50 EMA, RSI, MACD & Fibonacci Levels for {symbol} - 1 Year of Daily Data",
                   "shapes": shapes_dict[symbol]
                   }]
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
    title=f"Candlestick, 50 EMA, RSI, MACD & Fibonacci Levels for {symbols[0]} - 1 Year of Daily Data",
    xaxis_title="Date",
    yaxis_title="Price",
    xaxis_rangeslider_visible=False,
    template="plotly_white",
    height=800  # Adjust the height as needed
)

# Optionally, update the x-axis to remove weekend gaps (for daily data)
fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])

# --- Add Horizontal RSI Lines at 70 and 30 to the RSI subplot (row 2) ---
# Using yref "y2" so they appear only in the RSI subplot.
rsi_x0 = data_dict[symbols[0]].index.min()
rsi_x1 = data_dict[symbols[0]].index.max()
fig.add_shape(
    type="line",
    xref="x",
    yref="y2",
    x0=rsi_x0,
    x1=rsi_x1,
    y0=70,
    y1=70,
    line=dict(color="black", dash="dot", width=1)
)
fig.add_shape(
    type="line",
    xref="x",
    yref="y2",
    x0=rsi_x0,
    x1=rsi_x1,
    y0=30,
    y1=30,
    line=dict(color="black", dash="dot", width=1)
)

# Display the Plotly chart in Streamlit
st.plotly_chart(fig, use_container_width=True)
