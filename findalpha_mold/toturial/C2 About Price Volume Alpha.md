# About Price Volume Alpha

### ✒️Alpha Using PV Data

Great job getting familiar with the platform! 👏 Now let's look at what kinds of Alphas we can create. 😁

**PV data** has information related to price and volume. Since it includes price itself, which is essential for predicting stock prices, it's one of the most useful data types when first creating Alphas.

### 💸 Price data

**PV data** includes stock prices – open, high, low, close- and other trading related information like volume of shares traded and market capitalization. These values are well represented in candlestick charts.



![Navigator_PV_data.png](https://api.worldquantbrain.com/content/images/4_k4-3qVP9igbW3C5HVB3HloNvs=/384/original/Navigator_PV_data.png)

-   **Open** is the first traded price when the stock market opens for the day.
-   **Close** is the last traded price when the stock market ends for the day.
-   **High** is the highest price traded during the day.
-   **Low** is the lowest price traded during the day.

### 📦 Volume

**Volume** indicates the number of shares investors transacted that day.

You can use the **adv20** data field to access the 20-day average volume. If you want to calculate the average for a different number of days, you can use **ts_mean(volume,N)**.

### 📋 VWAP (Volume-Weighted Average Price)

Additionally, **VWAP** can represent a day's stock price, which is the volume-weighted average price. Since low-volume trades might give a false picture of other price indicators like closing price, **VWAP** can be a better measure of that day's price. Let's look at this table:

| Price | Volume |
| :---: | :----: |
|  10   |  100   |
|  11   |  120   |
|  12   |   80   |
|  13   |   10   |
| VWAP  |   11   |

Here, the VWAP is 11, resulting from dividing the sum of price times volume by the total volume sum. In formula terms, it's **sum(price\*volume)/sum(volume)**.

💡 Alpha Ideas

Most Alphas using PV data come from these two main ideas:

-   Momentum

    -Assume that stocks which have performed well in the past will continue to perform well, while stocks that have performed poorly will continue to do so.

    -   **Momentum effect** typically appears over longer periods (several months or more).

-   Reversion

    -The hypothesis is that if something increases today, it will fall tomorrow. And if something decreases today, it will increase tomorrow. This something can be anything: price, volume, correlation between two things or the other indicators/variables that you can think of while developing your alpha.

    -   **Reversion effect** appears over shorter periods (days or weeks).

The **rank(-returns)** we created first is a simple example of implementing the reversion effect.

### 🔥 Let's try it out!

Shall we try implementing a **reversion Alpha** using **VWAP**? VWAP is the average price weighted by volume for the day, while closing price is the last traded price. By comparing VWAP and closing price, we can understand how the last traded price compares to the day's average. For example, if the closing price is much higher than VWAP, we can interpret that the price rose near market close. The opposite tend to be true as well.

Since **reversion** theory assumes prices return to their mean, we can implement an Alpha using the formula "**vwap/close**". This takes long positions when closing prices fall below VWAP, and short positions when they rise above it.

When you simulate this, you'll notice that while the Sharpe ratio is high, the turnover is excessive. According to submission criteria, turnover should be below 70% for submission. You can adjust turnover by applying operators (ex. trade_when) or changing settings (ex. Decay).

**✔️ Completed task:** Try simulating an Alpha that includes `vwap/close` and has a turnover below 70%.

**Hint:** Simulate an alpha that includes `vwap/close`.
You can control alpha's turnover through various methods like Decay, `trade_when`, etc.

**Answer:** `# DECAY 10vwap/close`