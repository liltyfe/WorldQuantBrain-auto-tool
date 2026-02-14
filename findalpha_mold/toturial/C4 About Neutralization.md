# About Neutralization

🎯 What is Neutralization?

**Neutralization** is a technique to obtain pure Alpha performance by removing or minimizing the influence of specific factors. Through neutralization, you can reduce (or remove) unwanted factor influences in a specific Alpha. Typically, but not always, applying neutralization increases the **Sharpe ratio** while reducing **returns or margins**.

In BRAIN, you can implement neutralization through **Group Neutralize** operator.

🤝 Group Neutralize

**Group neutralization** standardizes values only within defined groups. The most representative example is industry-based neutralization available in Settings. By dividing into industry groups and standardizing within them, you can neutralize industry-based Alpha performance in your simulation.

Beyond industry neutralization in Settings, BRAIN allows group neutralization using various **group data** and the **group_neutralize operator**.

🗂️ Group Datafields

The second input of **group_neutralize(x,group)** allows you to input group data. Group data fields are data that classify each instrument based on specific criteria. You can use various data fields, including **sector**, **industry**, and **subindustry**, which can be found in the settings, as well as additional datafields like **exchange**. You can find many group datafields in [Price Volume Data for Equity](https://platform.worldquantbrain.com/data/data-sets/pv1?delay=1&instrumentType=EQUITY&limit=20&offset=0&region=USA&universe=TOP3000) and [Relationship Data for Equity](https://platform.worldquantbrain.com/data/data-sets/pv13?delay=1&instrumentType=EQUITY&limit=20&offset=0&region=USA&universe=TOP3000), so take a look for useful datafields that suit your needs.

🛒 Bucket() Operator

If there's no suitable existing group for your idea, you can create your own using the **bucket operator** as shown below:

**bucket(X, range="{start},{end},{step}")**

For example, if you want to divide into 10 groups based on market capitalization size, you can create group variables using **bucket(rank(cap),range="0,1,0.1")** which creates 10 groups from 0~0.1, 0.1~0.2, …, 0.9~1.0 based on rank(cap) values.

🛠️ Densify() Operator

When using group datafields, you may encounter situations where excessive computation leads to simulation failures. This can happen when the values of the group datafields are **sparsely distributed**, making the computation inefficient. In such cases, applying **densify(x) operator** to the group datafields can help resolve the issue. More detailed information can be found in the description of densify(x) in the [Operator Explorer](https://platform.worldquantbrain.com/learn/operators/detailed-operator-descriptions).

🔥 Let's try it out!

Let's create an Alpha that group-neutralizes the difference between put and call option implied volatility. First, let's assign the following formula to iv_difference:

**iv_difference = implied_volatility_call\_{expiry} - implied_volatility_put_{expiry};**

The difference in implied volatility can be affected by the stock's inherent volatility. Since stocks with higher volatility will have larger differences in implied volatility, neutralizing stock volatility might help catch purer option demand differences. Let's create volatility groups named **std_group**. **To avoid high turnover of group, it's recommended to use medium to long-term periods like 120 or 180**.

**std_group = bucket(rank(historical_volatility_{period}),range="0.1,1,0.1");**

Now let's perform group neutralization using this group:

**group_neutralize(iv_difference,std_group)**

**🔥Task:** Create an Alpha incorporating all of these elements!

**Hint:** Try creating groups using `rank(historical_volatility_120)` with `bucket()`.

**Answer:** `iv_difference = implied_volatility_call_120 - implied_volatility_put_120;std_group = bucket(rank(historical_volatility_120),range="0.1,1,0.1");group_neutralize(iv_difference,std_group)`