# What's going on in the platform?

### 🔍 What Happens in the Platform When Running a Simulation

#### 🏛 Position

When starting a simulation, BRAIN calculates how much to invest in each stock by setting positions.

Positions consist mainly of **long positions** and **short positions**. In BRAIN, a long position means **buying stocks**, betting that the stock price will rise. Conversely, a short position means **selling stocks**, betting that the stock price will fall.

When you press the simulate button, BRAIN calculates positions for each stock through the process shown in the table below. Don't worry if it looks complicated! It's simple when you look at it step by step.

![Navigator_Whats_Going_On.png](https://api.worldquantbrain.com/content/images/MbmDbBPhnUIIHmlONixQvzKlCr4=/391/original/Navigator_Whats_Going_On.png)

#### 🧮 Expression Calculation

Let's examine each step. First, the simulator calculates the results of the expression formula.

**rank()** ranks the input values and arranges them evenly from 1 to 0 in descending order. For example, if there are 5 stocks, it returns 5 values like **0, 0.25, 0.5, 0.75, 1** according to the input value order.

In the table above, column D, **Alpha value on 2-Feb: rank(-returns)**, shows this process.

After calculating **rank()**, it goes through a process called **neutralization**.

#### 🌐 Market Neutralization

**Neutralization** means **removing specific influences from an Alpha**. Since overall market movements often influence stock prices, having only long positions for many stocks carries a high risk of market exposure.

Therefore, BRAIN assumes the construction of a **long-short portfolio** where half the positions are long positions and the other half are short positions.

Before constructing a long-short portfolio, let's see what happens when we only take long positions. Click on Settings, then change **Neutralization** to **None** and check the results.

![Navigator_Market_Neutralization_None.png](https://api.worldquantbrain.com/content/images/RgRWklm-wIGrsldmSpKxqcIFxXc=/392/original/Navigator_Market_Neutralization_None.png)

As we saw earlier, applying the rank operator gives values from minimum 0 to maximum 1, allowing us to construct a long-only portfolio..

**✔️ Completed task:** Change Neutralization to None in Settings and check the results.

**Hint:** Set Neutralization to None in Settings and simulate the alpha.

**Answer:** `rank(-returns) # Neutralization: None`