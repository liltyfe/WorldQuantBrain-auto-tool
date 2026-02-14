# About Momentum Effect

### 🔍 Understanding the Momentum Effect

The momentum effect is a common phenomenon in financial markets where assets that have recently risen tend to continue rising, and assets that have fallen tend to continue falling. Various academic studies have confirmed this effect.

### ⏰ Characteristics of Momentum Effect

Momentum effect manifests differently depending on the time perspective:

-   **Short-term** (less than 1 month): Reversion effect is stronger
-   **Medium-term** (quarter to year): Traditional momentum effect is most pronounced
-   **Long-term** (over 12 months): Effect tends to gradually weaken

### 👨‍💻 Implementing Momentum Effect in BRAIN

The momentum effect can be implemented in various ways. The simplest method is calculating recent price increases. Shall we calculate an asset's price increase over one year? Since BRAIN only considers business days, a year's length is typically represented as 250 days (the number of business days in a year). We can measure the change in x over a year using the time series operator **ts_delta(close,250)/ts_delay(close,250)**.

However, using this formula alone doesn't produce good Alpha results. One-year returns are significantly influenced by recent period returns, incorporating short-term reversion effects. To implement the momentum effect as an Alpha in BRAIN, we need to use different methods or add conditions.

### 💫 Various Methods to Implement Momentum Effect in BRAIN

Therefore, to see the momentum effect more clearly, we can use the following methods:

-   Apply delay to one-year returns to mitigate short-term reversion effects.
    -   **ts_delay(ts_delta(close,250)/ts_delay(close,250),10)**
-   Count the number of days with price increases over one year.
    -   **ts_sum(returns>0? 1:0, 250)** *

\* **\<condition>? <if_true>:<if_false>** returns if_true value when the condition is true, and if_false value when it's not. **if_else(\<condition>,<if_true>,<if_false>)** means the same thing.

**✔️ Completed task:** Try using the count of days with price increases over a year in your Alpha.

**Hint:** Follow the instructions step by step to create positive days.

**Answer:** `ts_sum(if_else(greater(returns,0),1,0),250)`