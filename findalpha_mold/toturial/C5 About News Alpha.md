# About News Alpha

### 📰 News Dataset Overview

In BRAIN, News data provides the latest financial news driving market movements. News data is from various sources:

-   **Financial reports** (earnings, investments, dividends)
-   **Analysts' recommendations** (expectations, ratings, opinions)
-   **Company products** (new products, approvals)
-   **Legal events** (investigations, bankruptcies)

Combining news and stock prices provides more comprehensive insight.

### ⏰ Trading Sessions

USA stock market has three sessions:

1.  **Pre** session: 4:00 am to 9:30 am
2.  **Main** session: 9:30 am to 4:00 pm
3.  **Post** session: 4:00 pm to 8:00 pm

News is usually released during the pre- and post sessions.

### 🔠 Vector data fields

Vector Data are data fields without fixed size, where the number of events per day per instrument varies. **Unlike matrix data** with one value per day per instrument, **vector data can store many values**, like news data with different numbers of events per instrument. This allows for capturing more detailed information.

When writing an Alpha expression, the result is a matrix of Alpha values representing market positions. Platform operators are designed for matrix input, so **use vec_~ operators to convert vector data to matrix form before applying matrix operators.** This is done by aggregating vector data for each day and instrument into a single value, as illustrated in the figure below.

![Navigator_Vector.png](https://api.worldquantbrain.com/content/images/hH2qGvfDkTE-A-NZVpUrRE5t80g=/383/original/Navigator_Vector.png)

### 💡 Alpha Ideas

**nws12_afterhsz_sl** data field indicates whether a long or short position would be more beneficial following each news release. This information is stored in a vector-type field, as a company may have multiple news releases. Stocks with more 'long position advantage' news events might exhibit strong momentum, while companies with fewer such events could exhibit a potential reversion.

In brief, this approach combines momentum and reversion Alpha idea. Under specific conditions (more 'long position advantage' news events), the Alpha applies a momentum effect; otherwise, it uses a reversion signal. The expression of this idea might look like this:

**<condition: more 'long position advantage' news events>? <momentum signal (long position)> : <reversion signal (short position)>**

### 👨‍🏫Implementation

Let's begin by identifying stocks with more 'long position advantage' news events. Since nws12_afterhsz_sl has multiple daily values per company, we'll aggregate these into a single representative value using the **vec_avg** operator.

**vec_avg(nws12_afterhsz_sl)** indicates whether the overall news sentiment for a company is positive or negative.

To reduce noise in this daily data and extract a clearer signal, apply time series operators like ts_sum or ts_mean with an appropriate period.

-   Apply **time series operators** with a suitable period to reduce noise in this daily data. **ts_sum** or **ts_mean** work well for this purpose.
-   **Rank** the data and set a threshold. For example, to classify half the stocks as True and the rest as False, use a condition like **rank(X) > 0.5**.

After establishing your condition, set up your momentum and reversion signals as you learned in the PV alphas section. Keep in mind:

-   The conditions based on **vec_avg(nws12_afterhsz_sl)** already incorporate momentum. For stocks meeting the condition, simply taking a long position (using a constant **1**) can represent the momentum signal.
-   Carefully balance the scale of your momentum signal and reversion signal to ensure your implementation aligns with your intended strategy.

### 🔥 Let's try it out!

**nws12_afterhsz_sl** indicates whether a long or short position would be more beneficial following each news release. This information is stored in a **vector-type field**, as a company may have multiple news releases. Stocks with more 'long position advantage' news events might exhibit momentum, while companies with fewer such events could exhibit a potential reversion.

**🔥Task:** Use `vec_avg(nws12_afterhsz_sl)` to calculate the average sentiment from news data for each company.
Use `ts_sum` or `ts_mean` (ts operator) and rank to set proper condition.
Use `if_else` or form of `?:` to implement the Alpha idea.

**Hint:** Rank the sum of news sentiment (`nws12_afterhsz_sl`) over time.
\- High ranked stocks ? +1 (momentum)
\- Low ranked stocks ? short position based on recent returns (reversion)

**Answer:** `rank(ts_sum(vec_avg(nws12_afterhsz_sl),60)) > 0.5 ? 1: rank(-ts_delta(close, 2))`





