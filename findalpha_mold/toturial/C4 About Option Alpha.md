# About Option Alpha

### 🎯 Option Basics

#### ❓ What are Options?

**Options** are contracts within the derivatives market, which give **the right, but not the obligation**, to buy or sell an underlying security at a specific strike price. Since it's a right and not an obligation, the option holder doesn't have to buy or sell the stock when it expires. The amount paid to have this option is called the **option premium**, which can be simply understood as the **price of the option**.

Options are good indicators of market participants' psychology and can be useful in exploring Alpha signals. Let's learn some basic knowledge needed to use option data for Alpha exploration.

#### 📑 Two Types of Options

As mentioned above, there are two categories of options: the right to buy and the right to sell. The right to buy is called a **Call Option**, and the right to sell is called a **Put Option**.

**Call Option**

A **Call Option** is **the right to buy an asset at a predetermined price**.
For example, if Company A's stock is currently \$60 and you want to buy it at the same price a week later, you can pay the option premium and buy a \$60 call option expiring next week. If Company A's stock price rises to \$70 at expiration, you can buy the stock with a \$10 profit, right? In this case, as expiration approaches, the call option's price itself will rise significantly, resulting in profit.
Therefore, buying call options can **bet on asset price increases (long position)**.

**Put Option**

A **Put Option** is **the right to sell an asset at a predetermined price**.
Think of put options as the opposite of call options - buying put options can **bet on asset price decreases (short position)**.

#### 🔍 Key Terms

-   **Strike Price:** The price agreed to buy or sell in the future

-   **Breakeven Price:** The point where neither profit nor loss occurs

-   **Expiration:** The last date to exercise the right

-   **Premium:** The price of the option

-   Volatility:

     

    Indicator of stock price volatility

    -   **Historical Volatility:** Actual past price volatility
    -   **Implied Volatility:** Expected future volatility derived from option prices

#### 📏 Volatility in Options

**Volatility** affects option prices. Higher stock price volatility increases demand for options to hedge risks or bet on price movements, leading to higher option prices. Volatility can be divided into **Historical Volatility** and **Implied Volatility**.

-   **Historical Volatility** is a lagging indicator calculated from past actual price data, typically by annualizing the standard deviation of daily returns.
-   **Implied Volatility** is a leading indicator derived from current market option prices using models like Black-Scholes, reflecting market participants' future expectations. Since it's calculated from option prices, it can also be considered another indicator of option prices.

While **Historical Volatility** comes from existing stock prices, **Implied Volatility** is derived from option prices. Comparing these two volatilities can help evaluate whether options or stocks are overvalued/undervalued.

#### 🔥 Let's try it out!

In this step, let's create an Alpha using implied volatility. Implied volatility is stored in data fields named **implied_volatility\_{call/put}_{expiry}**. Here are some Alpha ideas related to implied volatility:

-   Compare implied volatility of put/call options
-   Compare differences between **implied volatility** and **historical volatility**
-   Compare implied volatility trends

**🔥Task:** Try creating an Alpha using implied volatility (`implied_volatility_`~).

**Hint:** You can access data fields by appending option type and maturity, such as `implied_volatility_call_120`, `implied_volatility_put_180`.

**Answer:** `ts_rank(implied_volatility_call_120,20)`