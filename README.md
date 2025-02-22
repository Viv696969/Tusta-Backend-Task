# Trading Strategy and Logger

## Overview

This project provides a simple trading strategy implementation using the **Relative Strength Index (RSI)** indicator.It fetches stock data from Yahoo Finance using `yfinance`, analyzes it with `pandas_ta`, and logs trade actions based on RSI thresholds. These thresholds can be dynamically differ from each user.Designed for high scalability, allowing more indicators to be added in the future.

## Setup Instructions

### Prerequisites

```bash
pip install yfinance pandas pandas-ta
# to run the application
python main.py
```
### Folder Structure
```bash
|_
  app
    │   main.py
    |   trading.py
    |   config.json
│   README.md
│   sample-backtested-trade-logs.txt
```

## Code Structure
### `main.User` Class

- Manages user-related data, including indicators.
- Allows setting and retrieving indicators dynamically.
- `def setIndicator()` Many indicators can be inserted for each user and each indicator settings can be configured dynamically.
- A very simple structure to focus more on indicator trading.
- Many other fields can be added based on requirements.

### `trading.TradingStrategy` Class

- Contains a predefined list of companies which further can be dynamic using apis or database.
- `def getStockData()` Fetches stock data from Yahoo Finance and performs some preprocessing.
- `def tradeRSI()` Implements **RSI-based** trading strategy and logic based on dynamic values such as `period`,`buyThreshold`,`sellThreshold` given per user.
- `def tradeMACD()` and `def tradeROC()` are Placeholder methods for **MACD** and **ROC** strategies which can be Implemented further. This indicated the scalability and modularity of the code.

### `trading.TradeLogger` Class

- Logs trade actions into text files for RSI and other future indicators.
- Makes use of 🟢 for **entry** and 🔴 for **exit** in the log file.

## Key Features
- High modularity ensuring Loose coupling between different indicators.
- Scalable user parameters allowing them to add n number of indicators in future.
- Dynamic Data extracting based on number of days and interval in minutes.(default is 5 days and 1 minute interval).
- Getters and Setters for each field per class leading to better encapsulation.
