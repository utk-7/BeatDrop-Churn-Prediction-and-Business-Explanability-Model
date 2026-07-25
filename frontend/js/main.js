// BeatDrop Main JavaScript - Interactive Components (Live API Version)

class BeatDropApp {
    constructor() {
        this.currentPage = document.querySelector('.nav-links a.active')?.dataset.page || 'home';
        this.currentCustomer = null;
        this.simulatorDebounceId = null;
        
        // Define which features we can override for What-If
        this.simulatorFeatures = [
            { id: 'plan_list_price', label: 'Plan Price ($)', min: 0, max: 200, step: 1 },
            { id: 'payment_plan_days', label: 'Plan Duration (Days)', min: 7, max: 365, step: 1 },
            { id: 'days_since_registration', label: 'Tenure (Days)', min: 0, max: 3000, step: 10 },
            { id: 'is_auto_renew', label: 'Auto Renew (0=No, 1=Yes)', min: 0, max: 1, step: 1 }
        ];
        
        this.currentSimulatorValues = {};
        
        this.init();
    }
    
    init() {
        if (this.currentPage === 'home') this.loadDashboard();
        if (this.currentPage === 'customer-lookup') this.loadCustomerLookup();
        if (this.currentPage === 'model-performance') this.loadModelPerformance();
    }
    
    // UI Helpers
    showError(containerId, message) {
        const el = document.getElementById(containerId);
        if(el) el.innerHTML = `<div style="padding: 16px; color: var(--danger); background: rgba(239, 68, 68, 0.1); border-radius: 4px; font-weight: 500;">${message}</div>`;
    }
    
    showLoading(containerId) {
        const el = document.getElementById(containerId);
        if(el) el.innerHTML = `<div style="padding: 24px; text-align: center; color: var(--text-secondary);">Loading...</div>`;
    }
    
    // DASHBOARD
    async loadDashboard() {
        this.showLoading('stat-cards');
        this.showLoading('business-impact');
        this.showLoading('segment-filters');
        
        // GAP DECLARATION
        const driversChart = document.getElementById('churn-drivers-chart');
        if (driversChart) {
            driversChart.innerHTML = `
                <div style="padding: 24px; text-align: center; color: var(--text-secondary); border: 1px dashed var(--border); border-radius: 4px; height: 100%;">
                    <h3 style="margin-bottom: 8px; font-size: 16px;">Global Churn Drivers</h3>
                    <p style="font-size: 13px;">Data not yet available.</p>
                    <p style="font-size: 12px; margin-top: 8px;">(Requires a dedicated pre-computed global SHAP endpoint to aggregate efficiently across the cohort)</p>
                </div>
            `;
        }
        
        try {
            const stats = await apiFetch('/cohort/stats');
            this.renderStatCards(stats);
            this.renderSegmentFilters(stats);
            
            const impact = await apiFetch('/business-impact/top-actions?top_n=10');
            this.renderBusinessImpact(impact);
        } catch (e) {
            this.showError('stat-cards', e.message);
            this.showError('business-impact', e.message);
            this.showError('segment-filters', 'Failed to load filters');
        }
    }
    
    async loadDashboardWithParams(paramStr, activeId) {
        this.showLoading('stat-cards');
        try {
            const stats = await apiFetch('/cohort/stats' + paramStr);
            this.renderStatCards(stats);
            document.querySelectorAll('.filter-btn').forEach(b => {
                b.classList.toggle('active', b.dataset.id === activeId);
            });
        } catch (e) {
             this.showError('stat-cards', e.message);
        }
    }
    
    renderStatCards(stats) {
        const container = document.getElementById('stat-cards');
        if (!container) return;
        
        container.innerHTML = `
            <div class="stat-card">
                <div class="stat-label">Total Sample Customers</div>
                <div class="stat-value">${stats.total_customers.toLocaleString()}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Churn Prob</div>
                <div class="stat-value">${(stats.churn_rate * 100).toFixed(1)}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">High Risk Tier</div>
                <div class="stat-value" style="color: var(--danger);">${(stats.risk_tier_distribution.High * 100).toFixed(1)}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Low Risk Tier</div>
                <div class="stat-value" style="color: var(--success);">${(stats.risk_tier_distribution.Low * 100).toFixed(1)}%</div>
            </div>
        `;
    }
    
    renderSegmentFilters(stats) {
        const container = document.getElementById('segment-filters');
        if (!container) return;
        
        container.innerHTML = `
            <div class="filters">
                <button class="filter-btn active" data-id="all" onclick="app.loadDashboardWithParams('', 'all')">All Customers</button>
                <button class="filter-btn" data-id="plan30" onclick="app.loadDashboardWithParams('?plan_type=30', 'plan30')">30-Day Plans</button>
                <button class="filter-btn" data-id="new" onclick="app.loadDashboardWithParams('?tenure_bucket=new', 'new')">New (&lt;30 days)</button>
                <button class="filter-btn" data-id="old" onclick="app.loadDashboardWithParams('?tenure_bucket=old', 'old')">Tenured (&ge;30 days)</button>
            </div>
        `;
    }
    
    renderBusinessImpact(impact) {
        const container = document.getElementById('business-impact');
        if (!container) return;
        
        container.innerHTML = `
            <div>
                <h3 style="margin-bottom: 16px; font-size: 16px;">Top Priority Interventions (Sample)</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="text-align: left; font-size: 12px; color: var(--text-secondary); border-bottom: 1px solid var(--border);">
                            <th style="padding: 8px 0;">Customer ID</th>
                            <th>Prob</th>
                            <th>Est. CLV</th>
                            <th style="text-align: right;">Exp. Value (EV)</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${impact.customers.map(c => `
                            <tr>
                                <td style="padding: 12px 0; font-size: 14px;"><a href="customer-lookup.html" style="color: var(--primary); text-decoration: none;" onclick="localStorage.setItem('searchMsno', '${c.msno}')">${c.msno}</a></td>
                                <td style="color: ${c.churn_probability > 0.3 ? 'var(--danger)' : 'var(--text-primary)'}">${(c.churn_probability * 100).toFixed(1)}%</td>
                                <td>$${c.estimated_clv.toLocaleString()}</td>
                                <td style="text-align: right; font-weight: 600; color: var(--success);">$${c.expected_value.toFixed(2)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }
    
    // CUSTOMER LOOKUP
    async loadCustomerLookup() {
        const searchInput = document.getElementById('customer-search');
        if (!searchInput) return;
        
        // GAP DECLARATION
        const usageTrend = document.getElementById('usage-trend');
        if (usageTrend) {
            usageTrend.innerHTML = `
                <div style="padding: 24px; text-align: center; color: var(--text-secondary); border: 1px dashed var(--border); border-radius: 4px; height: 100%; display: flex; align-items: center; justify-content: center; flex-direction: column;">
                    <p style="font-size: 13px;">Usage trend data not yet available.</p>
                    <p style="font-size: 12px; margin-top: 4px;">(Requires a new GET /customers/{msno}/usage-history endpoint)</p>
                </div>
            `;
        }
        
        // Pre-fill from Dashboard link
        const prefill = localStorage.getItem('searchMsno');
        if (prefill) {
            localStorage.removeItem('searchMsno');
            this.selectCustomer(prefill);
            return;
        }
        
        try {
            const sampleRes = await apiFetch('/customers/sample');
            this.sampleMsnos = sampleRes.msnos || [];
        } catch(e) {
            this.sampleMsnos = [];
            this.showError('search-results', e.message);
        }
        
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            const resultsContainer = document.getElementById('search-results');
            if (query.length < 2) {
                resultsContainer.innerHTML = '';
                return;
            }
            
            const exactMatches = this.sampleMsnos.filter(m => m.toLowerCase().includes(query.toLowerCase())).slice(0, 5);
            
            if (exactMatches.length === 0) {
                 resultsContainer.innerHTML = '<div style="padding: 12px; color: var(--text-secondary);">No matching sample customers found</div>';
                 return;
            }
            
            resultsContainer.innerHTML = exactMatches.map(m => `
                <div style="padding: 12px; cursor: pointer; border-bottom: 1px solid var(--border); background: var(--surface);" onclick="app.selectCustomer('${m}')">
                    ${m}
                </div>
            `).join('');
        });
    }
    
    async selectCustomer(msno) {
        document.getElementById('customer-search').value = msno;
        document.getElementById('search-results').innerHTML = '';
        document.getElementById('customer-details').style.display = 'block';
        
        document.getElementById('selected-customer-name').textContent = "Real Customer Profile";
        document.getElementById('selected-customer-id').textContent = msno;
        
        this.showLoading('shap-explanation');
        this.showLoading('suggested-actions');
        
        document.getElementById('churn-probability').textContent = 'Loading...';
        document.getElementById('retention-score').textContent = 'Loading...';
        document.getElementById('clv').textContent = 'Loading...';
        
        try {
            const profile = await apiFetch(`/customers/${encodeURIComponent(msno)}`);
            this.currentCustomer = profile;
            
            const predict = await apiFetch(`/customers/${encodeURIComponent(msno)}/predict`);
            document.getElementById('churn-probability').textContent = (predict.churn_probability * 100).toFixed(1) + '%';
            document.getElementById('clv').textContent = '$' + predict.estimated_clv.toLocaleString();
            
            // Just use inverse for "retention score" since it's just a display metric
            document.getElementById('retention-score').textContent = ((1 - predict.churn_probability) * 100).toFixed(1);
            
            const riskBadge = document.getElementById('risk-badge');
            riskBadge.textContent = predict.risk_tier;
            riskBadge.className = 'risk-badge risk-' + predict.risk_tier.toLowerCase();
            
            const explain = await apiFetch(`/customers/${encodeURIComponent(msno)}/explain`);
            const shapContainer = document.getElementById('shap-explanation');
            shapContainer.innerHTML = `
                <h4 style="margin-bottom: 12px; font-size: 14px; color: var(--text-secondary);">Top SHAP Drivers (Increasing Risk)</h4>
                ${explain.top_drivers.map(d => `<div style="padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 13px;">${d}</div>`).join('')}
            `;
            
            const actions = await apiFetch(`/customers/${encodeURIComponent(msno)}/suggested-action`);
            const actionsContainer = document.getElementById('suggested-actions');
            actionsContainer.innerHTML = `
                <div style="padding: 16px; background: var(--background); border-radius: 4px; border-left: 4px solid var(--primary);">
                    <div style="font-weight: 500; font-size: 16px; margin-bottom: 4px;">${actions.suggested_action}</div>
                    <div style="font-size: 13px; color: var(--text-secondary);">Based on drivers: ${actions.top_drivers_used.join(', ') || 'General factors'}</div>
                </div>
            `;
            
            this.initSimulator(profile, predict);
            
        } catch (e) {
            document.getElementById('churn-probability').textContent = 'Error';
            this.showError('shap-explanation', e.message);
            this.showError('suggested-actions', e.message);
        }
    }
    
    initSimulator(profile, predict) {
        const container = document.getElementById('simulator-sliders-container');
        if (!container) return;
        
        this.currentSimulatorValues = {};
        
        container.innerHTML = this.simulatorFeatures.map(f => {
            const val = profile[f.id] !== undefined && profile[f.id] !== null ? profile[f.id] : 0;
            this.currentSimulatorValues[f.id] = val;
            return `
              <div class="slider-container">
                <div class="slider-label">
                  <span>${f.label}</span>
                  <span class="slider-value" id="value-${f.id}">${val}</span>
                </div>
                <input type="range" id="slider-${f.id}" class="slider" data-id="${f.id}"
                       min="${f.min}" max="${Math.max(f.max, val * 2 || 10)}" step="${f.step}" value="${val}">
              </div>
            `;
        }).join('');
        
        // set initial predict values
        this.updateSimulatorUI(predict);
        
        document.querySelectorAll('.slider').forEach(sl => {
            sl.addEventListener('input', (e) => {
                const id = e.target.dataset.id;
                const val = parseFloat(e.target.value);
                document.getElementById(`value-${id}`).textContent = val;
                this.currentSimulatorValues[id] = val;
                
                this.scheduleSimulateUpdate();
            });
        });
    }
    
    scheduleSimulateUpdate() {
        if (this.simulatorDebounceId) clearTimeout(this.simulatorDebounceId);
        
        document.getElementById('sim-churn').textContent = '...';
        
        this.simulatorDebounceId = setTimeout(async () => {
            try {
                const msno = this.currentCustomer.msno;
                const payload = this.currentSimulatorValues;
                const result = await apiFetch(`/customers/${encodeURIComponent(msno)}/simulate`, {
                    method: 'POST',
                    body: JSON.stringify(payload)
                });
                this.updateSimulatorUI(result);
            } catch(e) {
                document.getElementById('sim-churn').textContent = 'Error';
            }
        }, 500); // 500ms debounce
    }
    
    updateSimulatorUI(predict) {
        document.getElementById('sim-churn').textContent = (predict.churn_probability * 100).toFixed(1) + '%';
        document.getElementById('sim-retention').textContent = '$' + predict.estimated_clv.toLocaleString();
        
        const b = document.getElementById('sim-risk-badge');
        b.textContent = predict.risk_tier;
        b.className = 'risk-badge risk-' + predict.risk_tier.toLowerCase();
    }
    
    // MODEL PERFORMANCE
    async loadModelPerformance() {
        // GAP DECLARATION
        const roc = document.getElementById('roc-curve');
        if (roc) roc.innerHTML = `
            <div style="padding: 24px; text-align: center; color: var(--text-secondary); border: 1px dashed var(--border); border-radius: 4px; height: 100%; display: flex; align-items: center; justify-content: center; flex-direction: column;">
                <p style="font-size: 13px;">ROC Curve visualization gap.</p>
                <p style="font-size: 12px; margin-top: 4px;">(Backend only provides scalar metrics, not point arrays.)</p>
            </div>
        `;
        const pr = document.getElementById('pr-curve');
        if (pr) pr.innerHTML = `
            <div style="padding: 24px; text-align: center; color: var(--text-secondary); border: 1px dashed var(--border); border-radius: 4px; height: 100%; display: flex; align-items: center; justify-content: center; flex-direction: column;">
                <p style="font-size: 13px;">PR Curve visualization gap.</p>
                <p style="font-size: 12px; margin-top: 4px;">(Backend only provides scalar metrics, not point arrays.)</p>
            </div>
        `;
        const cm = document.getElementById('confusion-matrix');
        if (cm) cm.innerHTML = `
            <div style="padding: 24px; text-align: center; color: var(--text-secondary); border: 1px dashed var(--border); border-radius: 4px; height: 100%; display: flex; align-items: center; justify-content: center; flex-direction: column;">
                <p style="font-size: 13px;">Confusion matrix gap.</p>
                <p style="font-size: 12px; margin-top: 4px;">(Data not provided by API.)</p>
            </div>
        `;
        
        const cards = document.getElementById('performance-cards');
        if (cards) {
            cards.innerHTML = `<div style="padding: 24px; text-align: center; color: var(--text-secondary);">Loading...</div>`;
            try {
                const perf = await apiFetch('/model/performance');
                cards.innerHTML = `
                    <div class="stat-card">
                        <div class="stat-label">Model Version</div>
                        <div class="stat-value" style="font-size:24px;">${perf.model_version}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">PR-AUC</div>
                        <div class="stat-value" style="font-size:24px;">${perf.metrics.pr_auc.toFixed(4)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Brier Score</div>
                        <div class="stat-value" style="font-size:24px;">${perf.metrics.brier_score.toFixed(4)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Calibration</div>
                        <div class="stat-value" style="font-size:14px; margin-top: 8px;">${perf.calibration}</div>
                    </div>
                `;
            } catch(e) {
                this.showError('performance-cards', e.message);
            }
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new BeatDropApp();
});