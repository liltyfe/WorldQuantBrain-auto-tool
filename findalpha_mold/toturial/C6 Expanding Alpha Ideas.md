# Expanding Alpha Ideas

We've learned about the basic ideas of creating Alpha. The BRAIN platform ensures you create new ideas different from previously submitted Alphas through a self-correlation check process. However, you don't necessarily have to create just one Alpha from a single idea. You can expand your idea to create and submit multiple viable Alphas using the following methods.

Moreover, if you can create multiple viable Alphas from one idea, this might indicate that it's a robust idea that works well under various constraints. However, be careful not to overfit by fine-tuning too many details to increase In-Sample performance, as this could lead to poor Out-Sample performance.

🪐 Try Different Universes

Changing the universe alters the instruments within it and their position allocations. Generally, Alphas that maintain consistently good performance across multiple universes are considered high-quality.

⚖️ Experiment with Various Neutralizations

Alphas created from basic ideas may be exposed to various factors and risks. You can significantly alter Alpha characteristics by neutralizing different risks.

In Settings' Neutralization options, you can neutralize sector or industry-related risks.

For non-industry risks, you can use operators for neutralization. Try using **Group_neutralize** or **regression_neut** operators to neutralize various risks like Size, Beta, Momentum, etc.

📐 Modify Position Distribution through Operators

Alpha signals can vary depending on position allocation. Operators like **rank, signed_power**, and **log** change how Alpha distributes positions. Generally, distributions with more extreme values tend to have higher volatility and returns. Be careful of overfitting risk when positions are too concentrated in few instruments.

⚗️ Look for Synergies Between Alphas

Well-performing Alphas often have economic significance, and combining multiple Alphas can create synergies. This approach can help build more robust Alphas.

Try using Alphas in Trade_when's entry and exit conditions. With Alphas A1 and A2, you can write formulas like:

**Trade_when(A1>x, A2, A1<=x)**

However, simply linearly combining unrelated Alphas (like 3A1+4A2) isn't good for Alpha pool diversification. Good diversification should be judged by "drawdown diversification" - whether other Alphas can compensate when one experiences drawdown. Always approach Alpha research from an Alpha pool diversification perspective.

If you're struggling to come up with Alpha ideas, refer to the **Example Answers** from previous Steps. You can also check **Example** Alphas by clicking the "Example" button at the **bottom left of the simulation screen**.

🔥 Let's try it out!

Based on what you've learned, try to make and submit more alphas.

**Remember**: you can only earn 2,000 challenge points per day. Each Alpha can earn about 1,000-2,000 points, so to reach 10,000 points needed for Gold level, you'll need to submit Alphas over 5 days. Please submit considering the maximum points achievable per day.

Remaining challenge score: **{remaining_challenge_score = 10000-current_score}**, Required number of Alphas: **{remaining_challenge_score/2000}** **-** **{remaining_challenge_score/1000}** Alphas, depending on individual alpha performance

(Success criteria to move to the next module: User reaches 10K Challenge score / Gold level)

**🔥Task:** Submit your Alphas to reach Gold level! You can achieve Gold level when you reach 10,000 challenge points.