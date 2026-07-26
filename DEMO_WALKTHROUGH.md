# BeatDrop Demo Walkthrough

Welcome to the BeatDrop live demo! Here is a guided tour of the application to see the machine learning model and business logic in action.

> **Note**: As mentioned in the README, the main Dashboard currently experiences a memory limit crash on the live deployment. Please use the navigation bar to proceed directly to the **Customer Lookup** page.

### 1. Customer Lookup
Navigate to the "Customer Lookup" tab. 
- Start typing in the Search bar. The API will auto-suggest a valid customer ID (MSNO).
- Select a customer and hit "Lookup Customer".
- **What you're seeing**: 
  - **Risk Tier & CLV**: The model's calibrated churn probability and the financial Expected Value of retaining them.
  - **SHAP Explanation**: The green and red bars visually explain exactly *why* this specific user is at risk. For example, a high number of past cancellations pushes risk up (red), while a long membership tenure pushes risk down (green).

### 2. What-If Simulator
Scroll down on the Customer Lookup page to find the **What-If Simulator**.
- Change the user's "Membership Tenure" (Days Since Registration) to a much lower number (e.g., 10 days).
- Click "Run Simulation".
- **What you're seeing**: The frontend sends the modified profile back to the FastAPI backend, which runs inference through the XGBoost model in real-time. You'll instantly see how the churn probability spikes for newer users.

### 3. Model Performance
Navigate to the "Model Performance" tab.
- **What you're seeing**: These charts are pulled directly from the model's metadata. 
  - The **Global Churn Drivers** chart shows the average SHAP impact of every feature across the entire dataset.
  - The **Calibration Curve** demonstrates the v0.2.0 correction: the model's predicted probabilities closely hug the ideal diagonal line, meaning a 60% prediction genuinely translates to a 60% churn rate.

### 4. About
Navigate to the "About" tab for a high-level overview of the project's architecture, framing, and honest disclosures about the dataset constraints.
