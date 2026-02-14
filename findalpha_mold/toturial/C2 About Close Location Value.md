# About Close Location Value

### 🔍 Understanding Technical Analysis

**Technical Analysis** is an analysis method that seeks to predict future price movements based on historical price and volume data. It's based on the assumption that market participants' psychology and behavior patterns repeat, using various indicators such as chart patterns, price trends, momentum indicators, and moving averages. Here are some representative indicators you can use in Alpha exploration:

-   **RSI (Relative Strength Index):** A momentum indicator showing the degree of price increase/decrease
-   **Bollinger Bands:** Sets upper/lower bands using standard deviation around a moving average
-   **MACD (Moving Average Convergence Divergence):** A trend indicator using the difference between short-term and long-term moving averages

### 🧐 Alpha Using CLV

One of the technical indicators that can be easily used when creating Alphas is **CLV**.

**CLV (Close Location Value)** is an indicator that shows the closing price's position within the day's price range. Like the earlier vwap/close, this indicator can help understand market psychology at the last moment of the day's price movement.

### 🎯 How to Calculate CLV

**CLV = ((Close - Low) - (High - Close)) / (High - Low)**

The **CLV** value ranges from **1 to -1**, with these characteristics:

-   CLV close to 1 means closing price is near the high
-   CLV close to -1 means closing price is near the low

### 💡 Alpha Ideas

**CLV** is an indicator that captures price changes over a day (short-term period). Therefore, it might be more suitable for creating reversion Alphas among the two main branches of PV Alpha (momentum and reversion). Thus, the following idea might be effective:

**When CLV is low (close to -1) → Buy position**
**When CLV is high (close to 1) → Sell position**

### 🔍 Combining CLV with Volume

Using **CLV** together with **volume** can create more meaningful signals:

**✔️ Completed task:** Create an Alpha with a Sharpe ratio above 1.4 using all four data fields: `high, low, close, volume`.

**Hint:** The CLV expression has a range of -1 to 1.
Write an alpha that allocates more positions to stocks with higher volume.

**Answer:** `DECAY 4clv = ((close-low)-(high-close))/(high-low);-clv * rank(volume)`