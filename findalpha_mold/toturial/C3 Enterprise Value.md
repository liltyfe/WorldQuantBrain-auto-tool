# About Combining PV and Fundamental Data (2)

### 📋 Creating Price-Fundamental Combined Alpha: EBITDA/Enterprise Value

You can create more meaningful Alphas by combining PV (Price-Volume) data with fundamental data. Let's examine an Alpha that utilizes company valuation metrics by combining Enterprise Value, a PV-related metric, with EBITDA, a fundamental data point.

### 🔍 Data Characteristics

These two types of data have different characteristics. Before creating an Alpha, let's review their features.

EBITDA (Earnings Before Interest, Taxes, Depreciation, and Amortization)

-   Updated on quarterly/annual basis
-   Measures a company's overall financial performance
-   Provides a clearer picture of operating profitability
-   Useful for comparing companies with different capital structures or tax rates

Enterprise Value (EV)

-   Represents the total value of a company
-   Calculated as market cap plus debt, minority interest, and preferred shares, minus cash and cash equivalents
-   Updated frequently based on stock price changes
-   Considers a company's debt and cash position, unlike market cap alone

### 💡 Alpha Ideas

Enterprise Value shows the total value the market assigns to a company, including its debt. EBITDA represents a company's earning power from ongoing operations. By comparing these two, we can assess whether a company is potentially undervalued or overvalued relative to its ability to generate earnings.

### ⚖️ Comparing Two Data Points

The most common way to compare these metrics is by calculating the EV/EBITDA ratio. This is often referred to as the "enterprise multiple."

### ➗ Why Division is Appropriate

Division is particularly suitable here because:

1.  It allows for comparison across companies of different sizes
2.  It creates a standardized metric (the enterprise multiple) widely used in financial analysis
3.  It provides a measure of how many years it would take for a company's EBITDA to pay off its Enterprise Value

### 💭 Interpreting the Ratio

-   A lower EV/EBITDA ratio might suggest that a company is undervalued
-   A higher ratio might indicate overvaluation or high growth expectations
-   Industry comparisons are important, as typical ratios can vary significantly between sectors

### 🔥 Let's try it out!

Let's create an Alpha using **Enterprise Value** **(enterprise_value)** and **EBITDA**. Try creating an Alpha using your preferred comparison method. The most straightforward approach is to simply calculate EV/EBITDA for each company and rank them, with lower values potentially indicating more attractive investments.

**🔥Task:** Create an Alpha using EBITDA and Enterprise Value.

**Hint:** Simulate an alpha using `ebitda` and `enterprise_value`.

**Answer:** `ebitda/enterprise_value`



