# What's going on in the platform? (2)

### ⚖️ Market Neutralization

#### 🐂 long-only portfolio

![Navigator_Long_Only_Graph.png](https://api.worldquantbrain.com/content/images/e2ZT88-qqY3YkJ1GjxR5Kvumi-4=/387/original/Navigator_Long_Only_Graph.png)

You can see that even when running **rank(returns)**, which is opposite to the earlier simulation results, it shows a similar pattern. This means that a portfolio consisting of only long positions struggles to escape market risk influence.

That's why BRAIN allows users to construct a long-short portfolio where half the positions are long positions and half are short positions. This setup helps minimize market risk influence and retain only pure signal effects.

#### ⚖️ long-short portfolio

Let's return to the table we saw earlier. To neutralize market risk, we go through three main assumptions:

1.  Subtract the mean from each value to center around zero. **(Centered around 0)**
2.  Divide each value by the sum of absolute values to create Normalized weights where the total of absolute values equals 1. **(Normalized weights)**
3.  Multiply Normalized weights by book size to get actual positions. **(Assign $20Mn capital)**

![Navigator_Whats_Going_On.png](https://api.worldquantbrain.com/content/images/MbmDbBPhnUIIHmlONixQvzKlCr4=/391/original/Navigator_Whats_Going_On.png)

After creating positions through these three processes each day, we calculate each stock's PnL daily and combine them to produce the final PnL.

In the table above, we can see that out of 8 stocks, 5 predictions were correct and 2 were wrong, resulting in a final profit of 0.03.

### 🍂 Decay

Sometimes **Alpha positions might change too much daily**. For example, with **rank(-returns)**, if the Alpha's premise is true, all stocks' long and short positions need to change every day.

However, changing too many positions in one day can lead to issues with portfolio's stability. In such cases, we can slow down the rate of Alpha position changes through a method called **Decay**.

**Decay** means bringing forward a part of past positions to the present. When determining today's positions, it means applying a certain percentage of yesterday's or the day before's positions.

Let's see the table below.

![Navigator_Decay_Excel.png](https://api.worldquantbrain.com/content/images/Evcwv-Hh-AMw9-svpGREtR2Ntzc=/385/original/Navigator_Decay_Excel.png)

If applying a 3-day Decay, the final position is a weighted average where today's position (2-Feb) is multiplied by 3, yesterday's position (1-Feb) by 2, and the day before's position (31-Jan) by 1.

Expressed as a formula, it becomes **(Position(02Feb)\*3 + Position(01Feb)\*2 + Position(31Jan)\*1)/6**. The general form is like below:

Decay_linear(x,n)=(x[date]∗n+x[date−1]∗(n−1)+…+x[date−n−1]*1)/(n+(n−1)+…+1)

**Decay** allows **easy control of the rate of position changes**. However, note that applying **Decay may weaken signal strength** as current Alpha values reflect more slowly. Typically, values under 10 are used for Decay.

Shall we try creating an Alpha with market neutralization and Decay applied?

**✔️ Completed task:** In Settings, set Neutralization to Market and apply a value of 5 or higher for Decay, then simulate the Alpha.

**Hint:** Set Neutralization to Market and Decay to 5 or higher in Settings.

**Answer:** `rank(-returns) # Neutralization: Market, Decay > 5`