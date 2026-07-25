// BeatDrop Main JavaScript - Interactive Components

class BeatDropApp {
  constructor() {
    this.currentPage = 'home';
    this.currentCustomer = null;
    this.activeSegment = 'all';
    this.simulatorFeatures = {};

    // Initialize defaults
    whatIfConfig.features.forEach(f => {
      this.simulatorFeatures[f.id] = f.defaultValue;
    });

    this.init();
  }

  init() {
    this.setupNavigation();
    this.setupEventListeners();
    this.loadPage('home');
  }

  setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-links a');
    navLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const page = link.getAttribute('data-page');
        this.loadPage(page);
      });
    });
  }

  setupEventListeners() {
    // Customer lookup search
    const searchInput = document.getElementById('customer-search');
    if (searchInput) {
      searchInput.addEventListener('input', this.handleSearch.bind(this));
    }

    // What-if simulator sliders
    whatIfConfig.features.forEach(feature => {
      const slider = document.getElementById(`slider-${feature.id}`);
      const valueDisplay = document.getElementById(`value-${feature.id}`);

      if (slider && valueDisplay) {
        slider.addEventListener('input', (e) => {
          const value = parseFloat(e.target.value);
          this.simulatorFeatures[feature.id] = value;
          valueDisplay.textContent = feature.isPercentage
            ? (value * 100).toFixed(0) + '%'
            : Math.round(value) + ' ' + feature.unit;
          this.updateSimulatorResults();
        });
      }
    });

    // Segment filters
    const segmentBtns = document.querySelectorAll('.filter-btn');
    segmentBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
      });
    });
  }

  handleSearch(e) {
    const query = e.target.value.toLowerCase();
    const resultsContainer = document.getElementById('search-results');

    if (!resultsContainer) return;

    if (query.length < 2) {
      resultsContainer.innerHTML = '';
      return;
    }

    const results = mockCustomers.filter(c =>
      c.name.toLowerCase().includes(query) ||
      c.msno.toLowerCase().includes(query)
    ).slice(0, 5);

    if (results.length === 0) {
      resultsContainer.innerHTML = '<div class="search-no-results">No customers found</div>';
      return;
    }

    resultsContainer.innerHTML = results.map(c => `
      <div class="search-result-item" onclick="app.loadCustomer('${c.msno}')">
        <div class="search-result-name">${c.name}</div>
        <div class="search-result-id">${c.msno}</div>
        <span class="risk-badge ${getRiskLevelClass(c.churn_probability)}">
          ${getRiskLevelText(c.churn_probability)}
        </span>
      </div>
    `).join('');
  }

  loadPage(page) {
    this.currentPage = page;

    // Update nav active state
    document.querySelectorAll('.nav-links a').forEach(link => {
      link.classList.toggle('active', link.getAttribute('data-page') === page);
    });

    // Hide all pages, show target
    document.querySelectorAll('.page').forEach(p => {
      p.style.display = 'none';
    });

    const targetPage = document.getElementById(page);
    if (targetPage) {
      targetPage.style.display = 'block';
    }

    // Load page-specific content
    switch (page) {
      case 'home':
        this.renderDashboard();
        break;
      case 'customer-lookup':
        this.renderCustomerSearch();
        break;
      case 'model-performance':
        this.renderModelPerformance();
        break;
      case 'about':
        this.renderAbout();
        break;
    }

    // Update page title
    document.querySelector('.page-title').textContent = this.getPageTitle(page);
  }

  getPageTitle(page) {
    const titles = {
      'home': 'Cohort Dashboard',
      'customer-lookup': 'Customer Lookup',
      'model-performance': 'Model Performance',
      'about': 'About BeatDrop'
    };
    return titles[page] || 'BeatDrop';
  }

  renderDashboard() {
    // Stat cards
    this.renderStatCards();
    // Segment filters
    this.renderSegmentFilters();
    // Churn drivers chart
    this.renderChurnDriversChart();
    // Business impact summary
    this.renderBusinessImpact();
  }

  renderStatCards() {
    const container = document.getElementById('stat-cards');
    if (!container) return;

    container.innerHTML = `
      <div class="stat-card">
        <div class="stat-icon icon-primary">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M16 12h-4v-4h4v4"></path><path d="M12 16v2"></path><path d="M8 12v2"></path></svg>
        </div>
        <div class="stat-label">Total Customers</div>
        <div class="stat-value">${dashboardStats.totalCustomers.toLocaleString()}</div>
        <div class="stat-change positive">
          <svg width="12" height="12" viewBox="0 0 24 24"><path d="M5 15l7-7 7 7" fill="none" stroke="currentColor" stroke-width="2"></path></svg>
          +15.2%
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon icon-danger">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M9 10l6 6"></path><path d="M15 10l-6 6"></path></svg>
        </div>
        <div class="stat-label">Churn Rate</div>
        <div class="stat-value">${dashboardStats.churnRate}%</div>
        <div class="stat-change negative">
          <svg width="12" height="12" viewBox="0 0 24 24"><path d="M19 15l-7-7-7 7" fill="none" stroke="currentColor" stroke-width="2"></path></svg>
          -12.5%
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon icon-success">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M8 12l4 4 8-8"></path></svg>
        </div>
        <div class="stat-label">Avg Retention Score</div>
        <div class="stat-value">${dashboardStats.avgRetentionScore}</div>
        <div class="stat-change positive">
          <svg width="12" height="12" viewBox="0 0 24 24"><path d="M5 15l7-7 7 7" fill="none" stroke="currentColor" stroke-width="2"></path></svg>
          +3.1%
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon icon-primary">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><path d="M3 9h18"></path><path d="M9 21v-12"></path></svg>
        </div>
        <div class="stat-label">Monthly Revenue</div>
        <div class="stat-value">$${dashboardStats.monthlyRevenue.toLocaleString()}</div>
        <div class="stat-change positive">
          <svg width="12" height="12" viewBox="0 0 24 24"><path d="M5 15l7-7 7 7" fill="none" stroke="currentColor" stroke-width="2"></path></svg>
          +8.3%
        </div>
      </div>
    `;
  }

  renderSegmentFilters() {
    const container = document.getElementById('segment-filters');
    if (!container) return;

    container.innerHTML = `
      <div class="filters">
        ${dashboardStats.segments.map(s => `
          <button class="filter-btn ${s.id === this.activeSegment ? 'active' : ''}"
                  onclick="app.setActiveSegment('${s.id}')">
            ${s.name} (${s.count.toLocaleString()})
          </button>
        `).join('')}
      </div>
      <div style="display: flex; gap: 40px; color: var(--text-secondary); font-size: 14px;">
        <div>Churn Rate: <strong>${dashboardStats.churnRate}%</strong></div>
        <div>At-Risk Customers: <strong>${dashboardStats.customersAtRisk.toLocaleString()}</strong></div>
        <div>Revenue at Risk: <strong>$${(dashboardStats.monthlyRevenue * 0.28).toLocaleString()}</strong></div>
      </div>
    `;
  }

  setActiveSegment(segmentId) {
    this.activeSegment = segmentId;
    this.renderSegmentFilters();
  }

  renderChurnDriversChart() {
    const container = document.getElementById('churn-drivers-chart');
    if (!container) return;

    const maxImportance = Math.max(...mockChurnDrivers.map(d => d.importance));

    container.innerHTML = `
      <div class="chart-wrapper">
        <h3 style="margin-bottom: 16px; font-size: 16px;">Top Churn Drivers</h3>
        <div style="display: flex; flex-direction: column; gap: 12px;">
          ${mockChurnDrivers.map(driver => {
            const percentage = (driver.importance / maxImportance) * 100;
            return `
              <div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                  <span style="font-size: 13px;">${driver.label}</span>
                  <span style="font-size: 13px; font-weight: 500;">${driver.importance.toFixed(1)}%</span>
                </div>
                <div style="background: var(--border); border-radius: 4px; height: 8px; overflow: hidden;">
                  <div style="width: ${driver.direction === 'up' ? percentage : percentage * 0.5}%;
                           height: 100%;
                           background: ${driver.direction === 'up' ? 'linear-gradient(90deg, #ef4444, #fca5a5)' : 'linear-gradient(90deg, #10b981, #6ee7b7)'};
                           border-radius: 4px;"></div>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;
  }

  renderBusinessImpact() {
    const container = document.getElementById('business-impact');
    if (!container) return;

    container.innerHTML = `
      <div class="chart-wrapper">
        <h3 style="margin-bottom: 16px; font-size: 16px;">Business Impact Summary</h3>
        <div class="grid grid-2" style="gap: 20px;">
          <div>
            <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 4px;">Potential Revenue at Stake</div>
            <div style="font-size: 24px; font-weight: 700;">$${mockModelMetrics.businessImpact.potentialRevenue.toLocaleString()}</div>
          </div>
          <div>
            <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 4px;">Customers to Retarget</div>
            <div style="font-size: 24px; font-weight: 700;">${mockModelMetrics.businessImpact.retainedCustomers.toLocaleString()}</div>
          </div>
          <div>
            <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 4px;">Cost Savings</div>
            <div style="font-size: 24px; font-weight: 700; color: var(--success);">$${mockModelMetrics.businessImpact.costSavings.toLocaleString()}</div>
          </div>
          <div>
            <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 4px;">ROI</div>
            <div style="font-size: 24px; font-weight: 700;">${mockModelMetrics.businessImpact.roi}x</div>
          </div>
        </div>
      </div>
    `;
  }

  renderCustomerSearch() {
    document.getElementById('customer-search').value = '';
    document.getElementById('search-results').innerHTML = '';
  }

  loadCustomer(customerId) {
    this.currentCustomer = getCustomerById(customerId);

    if (!this.currentCustomer) return;

    document.getElementById('selected-customer-name').textContent = this.currentCustomer.name;
    document.getElementById('selected-customer-id').textContent = this.currentCustomer.msno;

    const riskClass = getRiskLevelClass(this.currentCustomer.churn_probability);
    const riskText = getRiskLevelText(this.currentCustomer.churn_probability);

    document.getElementById('risk-badge').className = `risk-badge ${riskClass}`;
    document.getElementById('risk-badge').textContent = riskText;

    document.getElementById('churn-probability').textContent = (this.currentCustomer.churn_probability * 100).toFixed(1) + '%';
    document.getElementById('retention-score').textContent = calculateMockRetention(this.currentCustomer.churn_probability);

    // Render SHAP explanation
    this.renderShapExplanation();

    // Render usage trend
    this.renderUsageTrend();

    // Render suggested actions
    this.renderSuggestedActions();

    // Reset simulator to customer's current values
    this.resetSimulatorToCustomer();
  }

  renderShapExplanation() {
    const container = document.getElementById('shap-explanation');
    if (!container || !this.currentCustomer) return;

    const shap = generateShapExplanation(this.currentCustomer);
    const maxAbsValue = Math.max(...shap.map(s => Math.abs(s.contribution)));

    container.innerHTML = `
      <h4 style="margin-bottom: 12px; font-size: 14px; color: var(--text-secondary);">SHAP Explanation</h4>
      <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 16px;">
        Features that push risk up (red) vs down (green)
      </p>
      ${shap.map(s => {
        const width = Math.abs(s.contribution / maxAbsValue) * 100;
        const direction = s.contribution >= 0 ? 'up' : 'down';
        return `
          <div class="shap-item">
            <div class="shap-bar shap-${direction}" style="width: ${width}px;"></div>
            <span class="shap-label">${s.label}</span>
            <span class="shap-value">${s.contribution >= 0 ? '+' : ''}${s.contribution.toFixed(3)}</span>
          </div>
        `;
      }).join('')}
    `;
  }

  renderUsageTrend() {
    const container = document.getElementById('usage-trend');
    if (!container || !this.currentCustomer) return;

    const trend = usageTrendData[this.currentCustomer.msno] || usageTrendData['CUST-00123'];

    container.innerHTML = `
      <div class="chart-wrapper">
        <h4 style="margin-bottom: 12px; font-size: 14px;">Usage Trend (Last 30 Days)</h4>
        <div style="display: flex; align-items: flex-end; gap: 4px; height: 150px; padding: 10px 0;">
          ${trend.map((point, i) => {
            const height = point.usage * 100;
            const color = point.usage < 0.5 ? '#ef4444' : point.usage < 0.7 ? '#f59e0b' : '#10b981';
            return `<div title="${point.date}: ${Math.round(point.usage * 100)}%" style="flex: 1; height: ${height}%; background: ${color}; border-radius: 4px 4px 0 0;"></div>`;
          }).join('')}
        </div>
      </div>
    `;
  }

  renderSuggestedActions() {
    const container = document.getElementById('suggested-actions');
    if (!container || !this.currentCustomer) return;

    const actions = suggestedActions[this.currentCustomer.msno] || suggestedActions['CUST-00123'];

    container.innerHTML = `
      <h4 style="margin-bottom: 12px; font-size: 14px;">Suggested Actions</h4>
      ${actions.map(a => `
        <div style="padding: 12px; background: var(--background); border-radius: 6px; margin-bottom: 8px; border-left: 4px solid ${a.priority === 'high' ? '#ef4444' : a.priority === 'medium' ? '#f59e0b' : '#10b981'};">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
              <div style="font-weight: 500; margin-bottom: 4px;">${a.action}</div>
              <div style="font-size: 12px; color: var(--text-secondary);">${a.reason}</div>
            </div>
            <span style="font-size: 12px; padding: 2px 8px; border-radius: 10px; background: ${a.priority === 'high' ? 'rgba(239, 68, 68, 0.1)' : a.priority === 'medium' ? 'rgba(245, 158, 11, 0.1)' : 'rgba(16, 185, 128, 0.1)'}; color: ${a.priority === 'high' ? '#ef4444' : a.priority === 'medium' ? '#f59e0b' : '#10b981'};">${a.priority}</span>
          </div>
        </div>
      `).join('')}
    `;
  }

  resetSimulatorToCustomer() {
    if (!this.currentCustomer) return;

    // Set simulator values based on customer's current state
    const features = {
      days_since_last_login: this.currentCustomer.days_since_last_login || 14,
      support_ticket_count: this.currentCustomer.support_tickets || 1,
      feature_usage_rate: Math.min(1, (this.currentCustomer.avg_listens_per_week || 35) / 100),
      contract_expiration_days: 120,
      payment_failures: this.currentCustomer.payment_failures || 0,
      plan_downgrades: 0
    };

    Object.keys(features).forEach(id => {
      this.simulatorFeatures[id] = features[id];
      const slider = document.getElementById(`slider-${id}`);
      const valueDisplay = document.getElementById(`value-${id}`);
      if (slider && valueDisplay) {
        slider.value = features[id];
        valueDisplay.textContent = whatIfConfig.features.find(f => f.id === id)?.isPercentage
          ? (features[id] * 100).toFixed(0) + '%'
          : Math.round(features[id]).toString() + ' ' + whatIfConfig.features.find(f => f.id === id)?.unit;
      }
    });

    this.updateSimulatorResults();
  }

  updateSimulatorResults() {
    const churnProb = calculateMockRiskProbability(this.simulatorFeatures);
    const retentionScore = calculateMockRetention(churnProb);

    document.getElementById('sim-churn').textContent = (churnProb * 100).toFixed(1) + '%';
    document.getElementById('sim-retention').textContent = retentionScore;

    const riskClass = getRiskLevelClass(churnProb);
    document.getElementById('sim-risk-badge').className = `risk-badge ${riskClass}`;
    document.getElementById('sim-risk-badge').textContent = getRiskLevelText(churnProb);
  }
}

function calculateMockRetention(churnProbability) {
  return Math.round((1 - churnProbability) * 100);
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.app = new BeatDropApp();
});