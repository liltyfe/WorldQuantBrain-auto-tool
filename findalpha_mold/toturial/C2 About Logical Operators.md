# About Logical Operators

### ⚡ Using Conditions in Alpha

When creating Alpha, you can fine-tune Alpha positions using conditions, using operators like **if_else()** or **trade_when()**.

### 🎨 Creating Conditions

You can create conditions using common logical operators (**>, <, >=, <=, ==**, etc.). For example, if you want to change positions only when the volume is higher than usual (20-day average), you can set the condition as **volume > adv20**. Here are some conditions to consider, though you can create any condition you want. Note that setting overly restrictive conditions may reduce the number of data points and increase the risk of overfitting.

These are the examples of conditions you can use when creating Alphas.

-   Change positions only when volume is higher than usual
-   Liquidate positions in extreme situations
-   Limit changing positions during high volatility periods

### 🔀 if_else(condition, if_true, if_false)

When implementing Alpha, sometimes you need to return different values based on specific conditions. The if_else operator is a basic yet powerful operator that enables you to implement conditional logic simply.

You can also use **if_else** in the form of **condition? if_true:if_false**. For example, **ts_sum(returns>0? 1:0, 250)** uses this format.

### 🎯 trade_when(entry_condition, Alpha, exit_condition)

Using the **trade_when** operator, you can decide when to change values within Alpha. The **trade_when** operator changes Alpha values only under specific conditions and maintains earlier positions otherwise.

trade_when takes three inputs: **entry condition, Alpha expression, and exit condition**.

-   When the **entry condition is true**, it **updates the Alpha expression value daily**.
-   When the **exit condition is true,** it **liquidates the position** (NaN).
-   When **both are false**, it **maintains the last Alpha value** from when the entry condition was true.

If the exit condition is **–1**, no position liquidation occurs.

### 💡 Applying trade_when to Momentum Alpha

Earlier, we looked at **ts_sum(returns>0? 1:0, 250)** which counts the number of positive return days over a year for momentum Alpha. You can store the formula as **positive_days = ts_sum(returns>0? 1:0, 250);** and use it as the second input in **trade_when**.

Let's set entry conditions. Based on the hypothesis that momentum works when **volume** surges, we can detect **volume** increases using these methods:

-   **volume > adv20** #adv20: 20-day average volume
-   **volume > ts_mean(volume, N_DAYS)**
-   **volume \* vwap > ts_mean(volume \* vwap, N_DAYS)**

You can test different values for **N_DAYS**.

Since momentum is a long-term effect, it's effective to set the **exit condition to –1** to keep positions longer once established. Or you can set your own exit condition which you think is effective.
Also, since momentum effects tend to occur across industries rather than within them, it's better to **set Neutralization options to avoid overly detailed grouping** **such as Market or Sector**.

**✔️ Completed task:** Try creating an Alpha using `trade_when` and positive_days.

**Hint:** Positive days work better with conditions. Try adding a volume-related condition.

**Answer:** `positive_days=ts_sum(returns>0? 1:0, 250);trade_when(volume>adv20,positive_days,-1)`