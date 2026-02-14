# What is an Alpha?

### 🧐 What does `-returns` mean?

Let's examine the expression we just ran in detail. First, **returns** is a data field that has the stock's returns for each company on each date.

|  Dates   |  MSFT   |   HOG   |  AAPL   |  GOOG   |   PG    |
| :------: | :-----: | :-----: | :-----: | :-----: | :-----: |
| 20100105 | 0.032%  | 0.745%  | 0.173%  | -0.441% | 0.033%  |
| 20100106 | -0.613% | -0.234% | -1.591% | -2.522% | -0.474% |
| 20100107 | -1.033% | 0.820%  | -0.185% | -2.328% | -0.542% |
| 20100108 | 0.683%  | -1.047% | 0.665%  | 1.333%  | -0.132% |

And we added a minus sign to **returns**, right? This means we're going to **bet against returns**.

Therefore, the formula we just ran expresses the idea of investing opposite to company returns. In other words, we predicted that companies with high returns yesterday will see price decreases, while those with low returns will see price increases.

As you can see, just investing opposite to returns can create an Alpha that generates quite decent returns. We call this Price Reversion. We'll look at this in more detail soon.

### 👍 What is an Alpha?

To WorldQuant, **Alpha** is **a mathematical model that seeks to predict the future price movement of various financial instruments**.

### 🔧 Operators

Operators transform data fields. You can consider the minus sign placed in front of returns as a type of operator.

**✔️ Completed task:** This time, let's use an operator called rank(). This operator sorts the values within the input and represents them as evenly spaced values. We will see how this operator works precisely in the further step. Try creating an Alpha by applying rank() to the -returns we ran earlier.
Try simulating an Alpha by applying `rank()` to `-returns`.

**Hint:** Enter `rank(-returns)` and run the simulation.

**Answer:** `rank(-returns)`