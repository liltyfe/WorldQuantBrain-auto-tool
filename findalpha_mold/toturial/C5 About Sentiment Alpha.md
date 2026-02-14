# About Sentiment Alpha

## 原文

### ❤️ Sentiment Alpha

**Sentiment data** quantifies the **emotions of the masses towards a stock or market in general**. This is based on data collected from various online platforms including newspapers, news websites, social media (Facebook, Twitter), blogs, and discussion forums.

This investor psychology can be a leading indicator of stock price movements.

BRAIN provides **sentiment** and **social media data**, which are data fields that quantify whether mentions of companies across various sources or SNS are negative/positive through natural language processing analysis.

### 🔊 Volume-Based Sentiment Alpha

You can find effective signals by utilizing the relationship between volume and sentiment. Abnormally frequent mentions of a particular stock in internet spaces, compared to its trading volume, might be a signal of future price movements. This hypothesis is based on the insight that excessive attention can often be a signal of overheating/undervaluation.

### 🧮 ts_regression(y, x, lookback_days, rettype=0) Operator

Given a set of two variables’ values (**X: the independent variable**, **Y: the dependent variable**) over a course of lookback_days, an approximating linear function can be defined, such that sum of squared errors on this set assumes minimal value. Through this operation, you can determine the level of Y in relation to X, considering the trend over the lookback_days. By setting the **rettype** (the default is 0), you can use other parameters related to linear regression in addition to the Error Term.

### 🔥 Let's try it out!

**scl12_buzz** is a data field that quantifies the amount of sentiment. It represents how frequently each stock is being mentioned on the internet. While there can be various ways to compare how much sentiment exists compared to **transaction** **volume (volume)** over the lookback_days, as we've seen before, in this case, using **ts_regression(y, x, lookback_days)** is the most effective method. Try comparing these two data fields using **ts_regression**. If the direction is different from what you expected, you can flip the PnL shape by adding a - in front of the Alpha.

### Task

 **🔥Task:** Try simulating an Alpha comparing the two data fields `scl12_buzz` and `volume` using `ts_regression`.

**Hint:** To understand the relative size of `scl12_buzz` compared to `volume`, in `ts_regression(y,x,lookback_days)`, `scl12_buzz` should be y and volume should be x.

**Answer:** `ts_regression(-scl12_buzz,volume,250)`





