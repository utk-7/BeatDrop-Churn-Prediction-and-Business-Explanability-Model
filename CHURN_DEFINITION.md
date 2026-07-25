# Churn Definition (KKBox)

Based on the official KKBox `WSDMChurnLabeller.scala` and `train.csv` labels, churn is defined using the following logic:

### The Definition
A customer is considered **churned** (`is_churn = 1`) if they **do not renew their subscription within 30 days** of their current `membership_expire_date`. 
Conversely, a customer is **retained** (`is_churn = 0`) if they have a valid renewal transaction within that 30-day window.

### Technical Implementation Details
1. **Last Expiration Date:** For a given observation window, the customer's last `membership_expire_date` is determined from their transaction history up to a specific cutoff date.
2. **Renewal Gap:** The system looks for the first subscription transaction following that expiration date.
3. **Threshold:**
   - If `gap < 30` days: The customer renewed in time (`is_churn = 0`).
   - If `gap >= 30` days: The customer is marked as churned (`is_churn = 1`).
   - If there is **no subsequent transaction** found, they are also marked as churned (`is_churn = 1`).
4. **Cancellations (`is_cancel` = 1):** Explicit cancellation events dynamically adjust the `membership_expire_date` backwards. However, a cancellation alone doesn't mean churn if the user resubscribes before the 30-day gap is reached.

*Note: This definition is applied natively by KKBox in the generation of `train.csv` and `train_v2.csv`. For our ML problem, we predict this target variable exactly as-is.*
