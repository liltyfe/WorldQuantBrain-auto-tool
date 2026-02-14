# About Universe

💫 Across the Universe

In BRAIN, you can select various universes ranging from TOP3000 to TOP200 based on transaction volume. Each universe has different characteristics, and if an Alpha's performance consistently appears across many universes, it can be considered a robust Alpha.

🌌 Universe Structure

The smaller the universe number, the more it consists of stocks with **higher liquidity and market capitalization**. Therefore, a **"small universe"** typically refers to a universe composed of large, actively traded companies.

Higher liquidity means more frequent transaction, which implies faster reflection of information in the stock market. As a result, **smaller universes often show relatively weaker Alpha signals**.

🌠 Subuniverse Test

Earlier in the submission criteria, we saw the **Subuniverse Test**, which checks if Alpha signals persist in smaller universes. By verifying if the Alpha works well in universes with higher liquidity where signals are harder to generate, it assesses Alpha's **robustness**.

If an Alpha fails this test, it likely works from low-volume stocks, making it **difficult to realize in practice**. In such cases, Subuniverse Sharpe can improve by concentrating positions more on high-volume, large-cap stocks.

🔥 Let's try it out!

Your Alphas might be a good Alpha that works quite well even in smaller universes. Since different universes often lead to lower correlations, this can increase diversity in terms of Alpha submission.

Check the Alpha's performance by simulating across various universes.

**🔥Task:** Simulate an Alpha in various universes such as TOP1000, TOP500, TOP200.

**Hint:** Apply `ts_rank()` to OEY and simulate in a universe other than TOP3000.

**Answer:** `# TOP500ts_rank(operating_income/cap,250)`