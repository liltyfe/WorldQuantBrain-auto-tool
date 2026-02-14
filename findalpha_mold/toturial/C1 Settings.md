# Settings

Now let's explain each item in the settings. Let's open the settings and take a look.

### 🌐 Language / Instrument Type

BRAIN supports backtest simulation using a simplified language called Fast Expression, targeting only stocks (Equity). Don't worry about Fast Expression - a detailed explanation will follow later!

### 🌍 Region

**Region** determines which area's stocks you want to simulate.

Currently, you can simulate in United States (USA) region. Once you reach the level and become a BRAIN consultant, you'll be able to run simulations in more regions.

Regions supported at the consultant level include Asia (ASI), Europe (EUR), China (CHN), Korea (KOR), Taiwan (TWN), Hong Kong (HKG), Japan (JPN), Americas (AMR), and Global (GLB) which allows simultaneous simulation of stocks from all regions.

### 🪐 Universe

**Universe** is a group of US stocks defined on the basis of their liquidity.

For example, you can select universes targeting TOP N stocks (N can be 3000, 1000, 500, and 200), meaning the simulation will run on N stocks based on most liquid.

### 🐢 Delay

**Delay** is an option that determines how much delay the data has. Using today's data immediately isn't as easy as you might think.

For example, considering closing prices, we can't know them until the stock market ends for the day. Due to this constraint, it's common to create Delay1 Alphas that use data accumulated up to yesterday.

However, if you want to reflect market changes faster, creating Delay0 Alphas might be a good idea. But Delay0 Alphas have many constraints and require stricter conditions for submission.

In Delay0, even data fields with the same names as in Delay1 might have different values. The close price data mentioned above uses actual closing prices in Delay1, but in Delay0, it uses prices from slightly before market close along with middle values.

### 🏛 Neutralization

When creating Alphas, positions often concentrate in specific industries. For example, imagine oil prices rose yesterday, causing all oil & gas stocks to rise while airlines industry stocks, which use oil as fuel, all fell.

In such situations, in Alphas like rank(-returns) might concentrate long or short positions in those two industries. Like the market risk exposure we looked at earlier, this Alpha becomes exposed to industry risk.

While we hedged market risk by taking equal long and short positions, how can we hedge industry risk?

Like hedging market risk, we can hedge through neutralization. However, instead of neutralizing across all stocks, we neutralize only within companies in the same industry.

This way, we can take long positions in petrochemical stocks that rose less and short positions in those that rose more. Similarly, we take long positions in aviation stocks that fell more and short positions in those that fell less.

### 🍂 Decay

**Decay** is a setting that determines how much past positions to reflect. As we looked at earlier in detail, higher Decay values lower Alpha turnover. However, note that the Alpha's Sharpe ratio might decrease as information becomes delayed.

### ✂️ Truncation

When creating Alphas, positions might become concentrated in specific stocks. In such cases, you can use **Truncation**, which limits the maximum weight a single stock can have. In the TOP3000 universe, using about 0.01(1%) is typical. However, in smaller universes like TOP200, having larger maximum positions might be better.

### 🧮 Pasteurization, Unit Handling, NaN Handling

These three options are somewhat difficult concepts to use from the start, but simply put:

-   **Pasteurization** determines whether to include stocks not in the universe in calculations or leave them as NaN.
-   **Unit Handling** detects and warns about mismatched data field units during simulation. It only provides warnings without affecting actual simulation, so only the Verify option is available.
-   **NaN Handling** is an option to choose whether to replace missing values (NaN) in data fields with 0.

### ⏳ Test Period

**Test Period** allows a subset of PnL to be hidden as a validation period. This PnL can be viewed by clicking the '**Show test period**' button. With this feature, you can check the performance of the hidden period and assess the robustness of the alpha based on the performance during this period.

**✔️ Completed task:** Try creating and simulating an Alpha with your preferred settings. You can proceed to the next step once simulation is complete, regardless of the Alpha's content.
Simulate any Alpha you want and check the results.

**Hint:** Click on the 'Example' button in the bottom left corner for an example Alpha. Simulate and check the results.

**Answer:** `vwap/close`