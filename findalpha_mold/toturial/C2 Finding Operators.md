# Finding Operators

### 🛠️ Using Operators in BRAIN

Just like we applied **rank()** to **-returns** to transform values within the matrix, operators process matrices within data fields. BRAIN provides various [operators](https://platform.worldquantbrain.com/learn/operators), including simple arithmetic operations and more complex ones.

### ➗ Arithmetic Operators

**Arithmetic operators** enable arithmetic operations including basic math operations and rounding.

### 💡 Logical Operators

**Logical operators** evaluate expressions and return true or false values. In BRAIN, true equals 1 and false equals 0.

### ⏰ Time Series Operators

**Time series operators** perform operations related to past d-day values for specific stocks. For example, ts_mean(x,d) calculates the average of x over d days.

### ❌ Cross Sectional Operators

**Cross-sectional operators** compare or process values across target stocks at a specific point in time. For example, rank(x) orders x values at a specific time and distributes them from 0 to 1.

### 📐 Vector Operators

When searching for data fields, you might find **vector-type data fields**. Instead of having a single value per stock per day, these store multiple values (in vector format). To convert these into Alpha positions, you need to transform them into a single representative value like mean or median. These operators serve this purpose.

### 🎭 Transformational Operators

**Transformational operators** enable transformation of values within matrices through specific operations.

### 👪 Group Operators

When exploring data fields, you might find group-type data fields that group companies based on specific criteria. For example, the industry data field is a group data field that classifies companies by industry. **Group operators** include operations like calculating representative values (mean/sum/median) within groups or performing neutralization within groups.

**✔️ Completed task:** This time let's run a simulation using one of the time series operators. Feel free to search for any data you want and simulate an Alpha you'd like to create.
Try simulating an Alpha using a Time Series operator.

**Hint:** Click Learn at the top of the screen and go to Operator to see available operators.
They are categorized by type, and Time Series operators are grouped together.
Most time series operators start with `ts_`.

**Answer:** `-ts_delta(close,5)`