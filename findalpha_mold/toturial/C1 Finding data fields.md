# Finding data fields

### 📁 How to Use Data in BRAIN

BRAIN enables easy access to financial market data using predefined names. In this step, we'll learn how to find the data you want. Let's first look at data classification system in BRAIN.

-   **Dataset Categories**
-   **Datasets**
-   **Data fields**

### 🏷️ Dataset Categories

**Dataset Categories** divide data into 17 main categories. You can see these categories by clicking "Data" at the top of the platform screen. (BRAIN shows only 7 categories before becoming a consultant.) Notable examples include Fundamental data from company financial statements and PV data related to stock prices and transaction volumes.

### 📦 Datasets

**Datasets** are collections of data with the same theme. They're usually named by adding numbers to the dataset category name. For example, PV1 dataset has price/volume-related data from the stock market, including price information like opening, high, low, closing prices, and information like 20-day average transaction volume. The fundamental6 dataset provides extensive data from financial statements including company assets, capital, and liabilities.

### 🔢 Data fields

**Data fields** are the actual matrix-form data used in the platform. You can access the contents within data fields through their names in the simulator. The returns data we used earlier was accessing the returns data field containing return information.

### 🔍 Finding Desired Data

BRAIN provides a [**Data Section**](https://platform.worldquantbrain.com/data) to find desired data fields. You can search by dataset or data field names, or explore from categories.
Remember to set your desired region, delay, and universe in the top right before searching, as available data fields differ by region and universe!

**✔️ Completed task:** This time let's run a simulation using data fields different from the earlier example of returns. Feel free to search for any data you want and simulate an Alpha you'd like to create.
Try simulating an Alpha using data fields other than returns.

**Hint:** You can explore data fields by clicking Data at the top of the screen.
The simulator also provides auto-completion when you start typing the data field.

**Answer:** `vwap/close`