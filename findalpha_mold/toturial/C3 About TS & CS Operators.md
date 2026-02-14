# About TS & CS Operators

📚 Types of Operators: Time Series & Cross-Sectional

Earlier, we saw that there are several types of operators. In this step, we'll look at two ways of examining specific values: **Time Series** and **Cross-Sectional** approaches.

⏰ Time Series Operators

Let's imagine a student who scored 80 points on a test. There are two main ways to evaluate this score: **comparing it with their own past scores** or **comparing it with other students' scores on this test**.

If the student usually scored 70 points but reached 80 for the first time, that tend to be considered a good achievement. **Time Series operators** resemble this method of comparing with past scores. **Time Series operators** include operators that calculate averages (**ts_mean**) or changes (**ts_delta**) using past values.

Here are some representative **Time Series operators**:

-   **ts_rank(x,d):** Ranks x values for each stock over the past d days and distributes them on a 0-1 scale, similar to rank()
-   **ts_zscore(x,d):** Shows how far today's x is from the d-day average in standard deviation units (**Z-score**)
-   **ts_mean(x, d):** Returns the average of x values over the past d days

🌐 Cross-Sectional Operators

Let's imagine that the student's classmates scored around 90 points on this test. From a comparative perspective, it might be hard to say they achieved an excellent score.

Similarly, **Cross-Sectional operators** resemble this second method of comparing with other students' current test scores.

Here are some representative Cross-Sectional operators:

-   **rank(x):** Returns a uniformly distributed value between 0.0 and 1.0 based on ranking among all stocks
-   **zscore(x):** Shows how far an instrument's x value is from the mean in standard deviation units (**Z-score**)
-   **winsorize(x, std=4):** Limits extreme values so all x values fall between upper and lower bounds set by standard deviation multiples

📋 Understanding through Visualization

The following diagram illustrates this concept. For calculations based on Company1 on January 10, 2020, the red-marked area represents the data used for time series calculations, while the green-marked area represents the data used for cross-sectional calculations.

![Navigator_TS_Table.png](https://api.worldquantbrain.com/content/images/I8FALeZ0jaZzo-yzk-FL6MH_l3s=/393/original/Navigator_TS_Table.png)

🎯 Choosing the Right Operator

**The appropriate operator can vary depending on the situation.** Time Series operators might be more appropriate when companies have different scales making cross-sectional comparison difficult. However, for model data where company metrics are already adjusted, **Cross-sectional operators might be more suitable**.

Usually, **Time Series operators work better** since stock prices often change based on a company's changes from past to present. However, this isn't always the case depending on the data, so it's recommended to explore which comparison method is more appropriate through repeated simulations.

🔥 Let's try it out!

In earlier step, we looked at comparing **operating_income** and **cap**. A common way to compare these two metrics is division, and **dividing operating income by cap** is widely used as **Operating Earnings Yield (OEY)** to evaluate company profitability.

This **OEY** metric tends to perform better with time series operators. Try checking the results using **ts_rank(oey,N_DAYS)**. Since **operating_income** updates quarterly, it's recommended to **use medium to long-term values for N_DAYS like half a year (125) or one year (250)**.

**🔥Task:** Create and simulate an Alpha comparing OEY using `ts_rank()`.

**Hint:** Apply `ts_rank()` to OEY.

**Answer:** `ts_rank(operating_income/cap,250)`



