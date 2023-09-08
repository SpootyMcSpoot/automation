import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# Fetch the list of S&P 500 stock symbols from Wikipedia
table = pd.read_html(
    'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
df = table[0]
symbols = df['Symbol'].tolist()

# Define the start and end date for the past year
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

# Number of symbols
total_symbols = len(symbols)

# Create chunks of 10 symbols each
symbol_chunks = [symbols[i:i + 10] for i in range(0, len(symbols), 10)]

for chunk_index, symbol_chunk in enumerate(symbol_chunks, start=1):

    fig, ax = plt.subplots(figsize=(20, 10))

    for idx, symbol in enumerate(symbol_chunk, start=1):
        # Fetch the data from Yahoo Finance
        data = yf.download(symbol, start=start_date, end=end_date)

        # Skip this symbol if there's no data
        if data.empty:
            continue

        # Prepare the data for linear regression
        data['Date'] = data.index

        # Fit a line to the data
        slope, intercept = np.polyfit(data['Date'].map(
            datetime.toordinal), data['Close'], 1)

        # Make predictions for the next month
        future_dates = [end_date + timedelta(days=i) for i in range(30)]
        future_dates_ord = [date.toordinal() for date in future_dates]
        predictions = intercept + slope * np.array(future_dates_ord)

        # Convert ordinal dates back to datetime for plotting
        plot_dates = [datetime.fromordinal(date) for date in future_dates_ord]

        # Visualize the data and the predictions
        ax.plot(data['Date'], data['Close'], label=symbol +
                ' Actual')  # Plot the actual data
        ax.plot(plot_dates, predictions, label=symbol +
                ' Predicted')  # Plot the prediction

        # Print percentage completion
        percentage_complete = ((chunk_index-1)*10 + idx) / total_symbols * 100
        print(f"Percentage complete: {percentage_complete:.2f}%")

    # Format the x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%Y'))

    plt.title('Stock Price Predictions for Next Month')
    plt.xlabel('Date')
    plt.ylabel('Stock Price')
    plt.legend()

    # Save the figure to a file
    plt.savefig(f"stock_price_predictions_{chunk_index}.png")

    # Close the figure to free up memory
    plt.close(fig)
