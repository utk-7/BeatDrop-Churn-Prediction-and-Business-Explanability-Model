const CONFIG = {
    // UPDATE THIS to your Render URL after deployment (e.g. "https://beatdrop-api.onrender.com")
    API_BASE_URL: "https://beatdrop-api-2i3o.onrender.com",
    FETCH_TIMEOUT_MS: 60000, // 60 seconds to accommodate Render free-tier cold start
    FEATURE_LABELS: {
        "registered_via_clean": "Registration Channel",
        "age_clean": "Age",
        "days_since_registration": "Membership Tenure",
        "payment_method_id": "Payment Method",
        "days_until_expire": "Days Until Renewal",
        "city": "City",
        "gender": "Gender",
        "days_since_last_transaction": "Days Since Last Payment",
        "is_auto_renew": "Auto-Renewal Status",
        "plan_list_price": "Plan Price",
        "num_plan_changes": "Plan Changes",
        "num_cancellations": "Past Cancellations",
        "payment_plan_days": "Plan Duration",
        "num_payment_methods": "Payment Methods Used",
        "days_since_last_log": "Days Since Last Listened"
    }
};
