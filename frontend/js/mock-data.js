/**
 * BEATDROP - MOCK DATA FILE
 * All data is hardcoded for Phase 0 (frontend shell validation)
 * This file contains realistic-looking mock data to validate UX
 */

// ====================
// DASHBOARD STATISTICS
// ====================
const dashboardStats = {
  totalCustomers: 12847,
  churnRate: 23.4,
  avgRetentionScore: 72.5,
  monthlyRevenue: 2450000,
  churnTrend: -12.5,
  revenueTrend: 8.3,
  retentionTrend: 3.1,
  customersAtRisk: 2987,
  segments: [
    { id: 'all', name: 'All Segments', count: 12847, churnRate: 23.4 },
    { id: 'premium', name: 'Premium', count: 8420, churnRate: 18.7 },
    { id: 'basic', name: 'Basic', count: 4427, churnRate: 32.1 },
    { id: 'enterprise', name: 'Enterprise', count: 2350, churnRate: 12.3 },
    { id: 'free', name: 'Free', count: 1650, churnRate: 45.8 }
  ]
};

// ====================
// MOCK CUSTOMER DATA
// ====================
const mockCustomers = [
  {
    msno: "CUST-00123",
    name: "TechCorp Solutions",
    city: "New York",
    gender: "M",
    age: 34,
    plan_type: "premium",
    payment_method: "credit_card",
    tenure_months: 24,
    avg_listens_per_week: 42,
    days_since_last_login: 3,
    payment_failures: 0,
    auto_renew: true,
    total_listen_time: 15420000,
    churn_probability: 0.12,
    risk_tier: "Low",
    monthly_revenue: 1250,
    lifetime_value: 18750,
    industry: "Software",
    contract_expires: "2024-03-15",
    support_tickets: 0
  },
  {
    msno: "CUST-00456",
    name: "Global Services Inc",
    city: "San Francisco",
    gender: "F",
    age: 41,
    plan_type: "premium",
    payment_method: "credit_card",
    tenure_months: 36,
    avg_listens_per_week: 18,
    days_since_last_login: 14,
    payment_failures: 2,
    auto_renew: true,
    total_listend_time: 6780000,
    churn_probability: 0.68,
    risk_tier: "High",
    monthly_revenue: 2500,
    lifetime_value: 45000,
    industry: "Professional Services",
    contract_expires: "2024-06-22",
    support_tickets: 5
  },
  {
    msno: "CUST-00789",
    name: "Startup Innovations LLC",
    city: "Austin",
    gender: "M",
    age: 28,
    plan_type: "basic",
    payment_method: "paypal",
    tenure_months: 8,
    avg_listens_per_week: 35,
    days_since_last_login: 2,
    payment_failures: 0,
    auto_renew: false,
    total_listen_time: 8920000,
    churn_probability: 0.34,
    risk_tier: "Medium",
    monthly_revenue: 499,
    lifetime_value: 3992,
    industry: "Technology",
    contract_expires: "2024-02-15",
    support_tickets: 1
  },
  {
    msno: "CUST-00101",
    name: "DataFlow Systems",
    city: "Boston",
    gender: "F",
    age: 38,
    plan_type: "premium",
    payment_method: "credit_card",
    tenure_months: 48,
    avg_listens_per_week: 22,
    days_since_last_login: 21,
    payment_failures: 1,
    auto_renew: true,
    total_listen_time: 5240000,
    churn_probability: 0.52,
    risk_tier: "Medium",
    monthly_revenue: 3200,
    lifetime_value: 38400,
    industry: "Healthcare",
    contract_expires: "2024-01-30",
    support_tickets: 3
  },
  {
    msno: "CUST-00202",
    name: "Creative Agency Co",
    city: "Los Angeles",
    gender: "M",
    age: 31,
    plan_type: "premium",
    payment_method: "credit_card",
    tenure_months: 15,
    avg_listens_per_week: 55,
    days_since_last_login: 1,
    payment_failures: 0,
    auto_renew: true,
    total_listen_time: 22100000,
    churn_probability: 0.08,
    risk_tier: "Low",
    monthly_revenue: 1850,
    lifetime_value: 27750,
    industry: "Marketing",
    contract_expires: "2024-05-20",
    support_tickets: 0
  },
  {
    msno: "CUST-00303",
    name: "RetailNet Solutions",
    city: "Chicago",
    gender: "F",
    age: 45,
    plan_type: "basic",
    payment_method: "paypal",
    tenure_months: 12,
    avg_listens_per_week: 8,
    days_since_last_login: 45,
    payment_failures: 5,
    auto_renew: true,
    total_listen_time: 1870000,
    churn_probability: 0.92,
    risk_tier: "High",
    monthly_revenue: 299,
    lifetime_value: 2392,
    industry: "E-commerce",
    contract_expires: "2024-04-05",
    support_tickets: 8
  },
  {
    msno: "CUST-00404",
    name: "EduLearn Platform",
    city: "Seattle",
    gender: "M",
    age: 37,
    plan_type: "premium",
    payment_method: "credit_card",
    tenure_months: 28,
    avg_listens_per_week: 48,
    days_since_last_login: 7,
    payment_failures: 1,
    auto_renew: true,
    total_listen_time: 13450000,
    churn_probability: 0.41,
    risk_tier: "Medium",
    monthly_revenue: 1500,
    lifetime_value: 18000,
    industry: "Education",
    contract_expires: "2024-03-18",
    support_tickets: 2
  },
  {
    msno: "CUST-00505",
    name: "FinTech Dynamics",
    city: "New York",
    gender: "F",
    age: 42,
    plan_type: "premium",
    payment_method: "credit_card",
    tenure_months: 60,
    avg_listens_per_week: 12,
    days_since_last_login: 35,
    payment_failures: 3,
    auto_renew: true,
    total_listen_time: 2980000,
    churn_probability: 0.78,
    risk_tier: "High",
    monthly_revenue: 3800,
    lifetime_value: 57000,
    industry: "Financial Services",
    contract_expires: "2024-02-28",
    support_tickets: 4
  }
];

// ====================
// MOCK GLOBAL STATISTICS
// ====================
const mockGlobalStats = {
  total_customers: 12543,
  overall_churn_rate: 0.28,
  at_risk_count: 3492,
  revenue_at_risk: 2850000,
  recoverable_revenue: 1980000
};

// ====================
// MOCK SEGMENT FILTERS
// ====================
const planTypes = ["All Plans", "Premium", "Basic", "Free"];
const tenureBuckets = ["All Tenures", "0-6 months", "7-12 months", "13-24 months", "25+ months"];
const paymentMethods = ["All Methods", "Credit Card", "PayPal", "Bank Transfer"];

// ====================
// MOCK CHURN DRIVERS (SHAP-style feature importances)
// ====================
const mockChurnDrivers = [
  { feature: "days_since_last_login", importance: 0.28, direction: "up", label: "Days Since Last Login" },
  { feature: "support_ticket_count", importance: 0.22, direction: "up", label: "Support Ticket Count" },
  { feature: "feature_usage_rate", importance: 0.19, direction: "down", label: "Feature Usage Rate" },
  { feature: "contract_expiration", importance: 0.15, direction: "up", label: "Contract Expiration" },
  { feature: "payment_failures", importance: 0.10, direction: "up", label: "Payment Failures" },
  { feature: "plan_downgrades", importance: 0.06, direction: "up", label: "Plan Downgrades" }
];

// ====================
// MOCK MODEL PERFORMANCE METRICS
// ====================
const mockModelMetrics = {
  rocAuc: 0.92,
  prAuc: 0.89,
  precision: 0.87,
  recall: 0.85,
  f1Score: 0.86,
  accuracy: 0.89,
  calibrationError: 0.04,
  featureImportance: [
    { feature: "Days Since Last Login", importance: 0.28 },
    { feature: "Support Ticket Count", importance: 0.22 },
    { feature: "Feature Usage Rate", importance: 0.19 },
    { feature: "Contract Expiration", importance: 0.15 },
    { feature: "Payment Failures", importance: 0.10 },
    { feature: "Plan Downgrades", importance: 0.06 }
  ]
};

// ====================
// MOCK ROC/PR CURVE DATA (for SVG rendering)
// ====================
const mockRocCurve = {
  fpr: [0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 1.0],
  tpr: [0, 0.45, 0.68, 0.78, 0.84, 0.88, 0.91, 0.93, 0.95, 0.97, 1.0]
};

const mockPrCurve = {
  recall: [1.0, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60, 0.50, 0.40],
  precision: [0.35, 0.45, 0.52, 0.58, 0.62, 0.66, 0.69, 0.72, 0.74, 0.76, 0.78]
};

// ====================
// MOCK CONFUSION MATRIX
// ====================
const mockConfusionMatrix = {
  trueNegatives: 8234,
  falsePositives: 432,
  falseNegatives: 587,
  truePositives: 3594
};

// ====================
// MOCK CALIBRATION DATA
// ====================
const mockCalibrationCurve = [
  { predicted: 0.0, actual: 0.02 },
  { predicted: 0.1, actual: 0.09 },
  { predicted: 0.2, actual: 0.18 },
  { predicted: 0.3, actual: 0.29 },
  { predicted: 0.4, actual: 0.41 },
  { predicted: 0.5, actual: 0.52 },
  { predicted: 0.6, actual: 0.61 },
  { predicted: 0.7, actual: 0.69 },
  { predicted: 0.8, actual: 0.78 },
  { predicted: 0.9, actual: 0.87 },
  { predicted: 1.0, actual: 0.95 }
];

// ====================
// MOCK USAGE TREND DATA (last 30 days)
// ====================
const usageTrendData = {
  'CUST-00123': [
    { date: '2024-01-01', usage: 0.92 },
    { date: '2024-01-06', usage: 0.88 },
    { date: '2024-01-11', usage: 0.75 },
    { date: '2024-01-16', usage: 0.62 },
    { date: '2024-01-21', usage: 0.45 },
    { date: '2024-01-26', usage: 0.32 }
  ],
  'CUST-00456': [
    { date: '2024-01-01', usage: 0.78 },
    { date: '2024-01-06', usage: 0.82 },
    { date: '2024-01-11', usage: 0.85 },
    { date: '2024-01-16', usage: 0.80 },
    { date: '2024-01-21', usage: 0.79 },
    { date: '2024-01-26', usage: 0.78 }
  ],
  'CUST-00789': [
    { date: '2024-01-01', usage: 0.65 },
    { date: '2024-01-06', usage: 0.70 },
    { date: '2024-01-11', usage: 0.68 },
    { date: '2024-01-16', usage: 0.72 },
    { date: '2024-01-21', usage: 0.69 },
    { date: '2024-01-26', usage: 0.71 }
  ]
};

// ====================
// MOCK SUGGESTED ACTIONS
// ====================
const suggestedActions = {
  'CUST-00123': [
    { priority: 'high', action: 'Schedule retention call within 48 hours', reason: 'High churn probability + inactivity' },
    { priority: 'high', action: 'Offer contract extension discount', reason: 'Contract expiring soon' },
    { priority: 'medium', action: 'Escalate to customer success manager', reason: 'Multiple support tickets' },
    { priority: 'low', action: 'Review feature usage for customization', reason: 'Low engagement' }
  ],
  'CUST-00456': [
    { priority: 'medium', action: 'Schedule quarterly business review', reason: 'Mid-market tier with moderate churn risk' },
    { priority: 'low', action: 'Send product update email', reason: 'Good engagement history' }
  ],
  'CUST-00789': [
    { priority: 'low', action: 'Send appreciation reward for loyal listener', reason: 'Good engagement' }
  ]
};

// ====================
// MOCK CALCULATION FUNCTIONS
// ====================
function getCustomerById(id) {
  return mockCustomers.find(c => c.msno === id);
}

function getRiskLevelClass(riskScore) {
  if (riskScore >= 0.7) return 'risk-high';
  if (riskScore >= 0.4) return 'risk-medium';
  return 'risk-low';
}

function getRiskLevelText(riskScore) {
  if (riskScore >= 0.7) return 'High';
  if (riskScore >= 0.4) return 'Medium';
  return 'Low';
}

// What-If Simulator Feature Configuration
const whatIfConfig = {
  features: [
    {
      id: 'days_since_last_login',
      label: 'Days Since Last Login',
      min: 0,
      max: 180,
      step: 1,
      defaultValue: 14,
      unit: 'days'
    },
    {
      id: 'support_ticket_count',
      label: 'Support Ticket Count',
      min: 0,
      max: 20,
      step: 1,
      defaultValue: 1,
      unit: 'tickets'
    },
    {
      id: 'feature_usage_rate',
      label: 'Feature Usage Rate',
      min: 0,
      max: 1,
      step: 0.05,
      defaultValue: 0.65,
      unit: '%',
      isPercentage: true
    },
    {
      id: 'contract_expiration_days',
      label: 'Contract Expiration (Days)',
      min: 0,
      max: 365,
      step: 7,
      defaultValue: 120,
      unit: 'days'
    },
    {
      id: 'payment_failures',
      label: 'Payment Failures',
      min: 0,
      max: 10,
      step: 1,
      defaultValue: 0,
      unit: 'count'
    },
    {
      id: 'plan_downgrades',
      label: 'Plan Downgrades',
      min: 0,
      max: 5,
      step: 1,
      defaultValue: 0,
      unit: 'count'
    }
  ]
};

/**
 * MOCK CALCULATION - What-If Simulator
 * This is a simplified weighted model for demo purposes only.
 * Will be replaced by actual model inference in production.
 */
function calculateMockRiskProbability(features) {
  // Default values from config
  const defaults = {};
  whatIfConfig.features.forEach(f => { defaults[f.id] = f.defaultValue; });

  const f = { ...defaults, ...features };

  // Weighted contributions (arbitrary weights for demo)
  const weights = {
    days_since_last_login: 0.35,
    support_ticket_count: 0.22,
    feature_usage_rate: -0.18, // negative = lower usage = higher risk
    contract_expiration_days: -0.15, // negative = closer expiration = higher risk
    payment_failures: 0.10,
    plan_downgrades: 0.06
  };

  // Normalize features to 0-1 range
  const normalized = {
    days_since_last_login: f.days_since_last_login / 180,
    support_ticket_count: f.support_ticket_count / 20,
    feature_usage_rate: f.feature_usage_rate,
    contract_expiration_days: 1 - (f.contract_expiration_days / 365), // invert
    payment_failures: f.payment_failures / 10,
    plan_downgrades: f.plan_downgrades / 5
  };

  // Base probability
  let score = 0.15;

  // Add weighted contributions
  Object.keys(weights).forEach(key => {
    score += normalized[key] * weights[key];
  });

  // Apply sigmoid-like squashing
  score = 1 / (1 + Math.exp(-10 * (score - 0.5)));

  return Math.max(0, Math.min(1, score));
}

function getRiskTierFromProbability(probability) {
  if (probability < 0.3) return 'Low';
  if (probability < 0.6) return 'Medium';
  return 'High';
}

function calculateMockCLV(monthlyRevenue, retentionScore) {
  const months = retentionScore * 12;
  return Math.round(monthlyRevenue * months * 1.5);
}

// ====================
// SHAP EXPLANATION GENERATOR
// ====================
function generateShapExplanation(customer) {
  const features = [
    {
      feature: 'days_since_last_login',
      label: 'Days Since Last Login',
      value: customer.days_since_last_login,
      threshold: 14,
      contribution: customer.days_since_last_login > 14 ? 0.22 : -0.05
    },
    {
      feature: 'support_ticket_count',
      label: 'Support Tickets',
      value: customer.support_tickets || 0,
      threshold: 2,
      contribution: (customer.support_tickets || 0) > 2 ? 0.18 : -0.08
    },
    {
      feature: 'feature_usage_rate',
      label: 'Feature Usage Rate',
      value: Math.round((customer.avg_listens_per_week / 100) * 100),
      threshold: 50,
      contribution: customer.avg_listens_per_week < 20 ? 0.15 : -0.12
    },
    {
      feature: 'contract_expiration_days',
      label: 'Contract Expires Soon',
      value: Math.floor((new Date(customer.contract_expires) - new Date()) / (1000 * 60 * 60 * 24)),
      threshold: 30,
      contribution: Math.floor((new Date(customer.contract_expires) - new Date()) / (1000 * 60 * 60 * 24)) < 30 ? 0.14 : -0.06
    },
    {
      feature: 'payment_failures',
      label: 'Payment Failures',
      value: customer.payment_failures,
      threshold: 0,
      contribution: customer.payment_failures > 0 ? 0.12 : -0.05
    },
    {
      feature: 'plan_downgrades',
      label: 'Plan Downgrades',
      value: 0, // Not in mock data
      threshold: 0,
      contribution: 0
    }
  ];

  // Normalize positive contributions to match churn probability
  const totalPositive = features.filter(f => f.contribution > 0).reduce((sum, f) => sum + f.contribution, 0);

  return features.map(f => ({
    ...f,
    contribution: totalPositive > 0 && f.contribution > 0
      ? (f.contribution / totalPositive) * customer.churn_probability
      : f.contribution
  }));
}