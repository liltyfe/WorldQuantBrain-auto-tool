# About Combining PV and Fundamental Data

### 📋 Creating Price-Fundamental Combined Alpha

You can create more meaningful Alphas by combining PV (Price-Volume) data with fundamental data. Let's examine an Alpha that utilizes company profitability rankings by combining market capitalization (cap), one of the PV data points, with operating income, a fundamental data point.

### 🔍 Data Characteristics

These two types of data have different characteristics. Before creating an Alpha, let's review their features.

**Operating income**, a fundamental data point, has the following characteristics:

-   Updated on **quarterly/annual basis**
-   Reflects company's actual profit-generating ability
-   Measures business efficiency

**Market capitalization (cap)**, a PV data point, has these characteristics:

-   Market's valuation of company worth
-   Updated **daily**
-   Product of stock price and outstanding shares

### 💡 Alpha Ideas

**Market capitalization** shows how much value the market currently assigns to a company. Even companies with same businesses and profitability can have different market caps based on future expectations (influenced by factors like technology holdings and news-based outlooks).

**Operating income** shows the actual profit recorded by the company in that quarter. Therefore, comparing market cap with operating income allows us to examine **current company performance relative to future expectations**.

### ⚖️ Comparing Two Data Points

How can we compare these two? While there are several methods, the most common and straightforward approaches are finding the difference through subtraction or calculating the ratio through division. The appropriate method can vary by situation.

### ➖ When Subtraction is More Appropriate

For instance, when comparing analyst forecasts with actual company performance, subtraction might be more appropriate as we need to see how much they differ.

### ➗ When Division is More Appropriate

However, since market cap and operating income don't directly share the same scale, division might be more appropriate to see what percentage operating income represents relative to market cap.

Also, when using subtraction, values can differ based on company size, so it's strongly recommended to consider data scale and units.

### 💭 Another Way to Compare Data

In addition to simple subtraction or division, there are many ways to compare two data points. for example, **(y - x) / x** allows for the comparison of two data points as a ratio.

### 🔥 Let's try it out!

Let's create an Alpha using **operating income** and **market capitalization (cap)**. Try creating an Alpha using your preferred comparison method.

Initially, the signal might not be as strong as desired. But don't worry! We'll learn how to improve this in the next steps.

**✔️ Completed task:** Create an Alpha using `operating_income` and market capitalization (`cap`) with your preferred comparison method.

**Hint:** Divide `operating_income` by `cap`.

**Answer:** `operating_income/cap`