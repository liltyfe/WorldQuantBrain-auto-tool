# About Option Alpha (2)

🎯 Characteristics of the Options Market

Option trading requires a more careful, information-based approach because it involves high leverage and complex factors including directionality, volatility, and time value. Therefore, **option traders are known to have more information than stock market participants**. Thus, if there's a difference in demand between call and put options, this can help forecast future stock price direction.

The implied volatility of put and call options reflects the price of each option.

🎭 Put-Call Implied Volatility Difference Analysis

As we saw earlier, **option implied volatility is an indicator reflecting option price, or demand**. When option prices are high, implied volatility increases, and when prices are low, implied volatility decreases. Therefore, by examining the difference in implied volatility between put and call options, we can gauge the difference in demand for each option.

-   **When call option implied volatility is higher than put option:** Option traders expect stock price to rise
-   **When put option implied volatility is higher than call option:** Option traders expect stock price to fall

🤔 Comparing Put-Call Implied Volatility

What's the best way to compare put and call option implied volatility? Implied volatility is basically calculated on the same scale for all stocks. Since the scale of implied volatility doesn't differ based on whether it's a put or call, using **subtraction(-)** might be most intuitive. However, depending on the situation, you can also try other calculation methods like division(/) or (y - x) / x.

🔥 Let's try it out!

This time, let's create an Alpha using the difference in implied volatility between put and call options. Create an Alpha that includes the difference between these two values.

You can also assign and use variables like:
**iv_difference = {comparison_operator}(implied_volatility_call\_{expiry},implied_volatility_put_{expiry});**

**🔥Task:** Create an Alpha comparing call option implied volatility (`implied_volatility_call_{expiry}`) and put option implied volatility (`implied_volatility_put_{expiry}`).

**Hint:** Comparing options with the same maturity, like `implied_volatility_call_120 - implied_volatility_put_120`, provides more accurate comparisons.

**Answer:** `implied_volatility_call_120 - implied_volatility_put_120` or `implied_volatility_call_120 / implied_volatility_put_120`