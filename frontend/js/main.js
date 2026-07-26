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
        if(el) el.innerHTML = `<div style="padding: 24px; text-align: center; color: var(--text-secondary);">Loading... <br><small style="opacity:0.7">(Waking up backend may take up to a minute if idle)</small></div>`;
    }
    
    // DASHBOARD
    async loadDashboard() {
        this.showLoading('stat-cards');
        this.showLoading('business-impact');
        this.showLoading('segment-filters');
        
        try {
            const stats = await apiFetch('/cohort/stats');
            this.renderStatCards(stats);
            this.renderSegmentFilters(stats);
            
            const impact = await apiFetch('/business-impact/top-actions?top_n=10&diversify=true');
            this.renderBusinessImpact(impact);
            
            const shap = await apiFetch('/model/global-shap');
            this.renderGlobalShap(shap);
        } catch (e) {
            this.showError('stat-cards', e.message);
            this.showError('business-impact', e.message);
            this.showError('segment-filters', 'Failed to load filters');
        }
    }
    
    async loadDashboardWithParams(paramStr, activeId) {
        this.showLoading('stat-cards');
        this.showLoading('business-impact');
        
        try {
            const stats = await apiFetch('/cohort/stats' + paramStr);
            this.renderStatCards(stats);
            document.querySelectorAll('.filter-btn').forEach(b => {
                b.classList.toggle('active', b.dataset.id === activeId);
            });
            
            const connector = paramStr ? '&' : '?';
            const impact = await apiFetch('/business-impact/top-actions' + paramStr + connector + 'top_n=10&diversify=true');
            this.renderBusinessImpact(impact);
        } catch (e) {
             this.showError('stat-cards', e.message);
             this.showError('business-impact', e.message);
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
    
    renderGlobalShap(shap, containerId = 'churn-drivers-chart') {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const drivers = shap.drivers || [];
        const maxImpact = Math.max(...drivers.map(d => d.impact));
        
        container.innerHTML = `
            <div>
                <h3 style="margin-bottom: 16px; font-size: 16px;">Global Churn Drivers</h3>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    ${drivers.map(d => {
                        const pct = (d.impact / maxImpact) * 100;
                        const color = d.direction === 'High' ? 'var(--danger)' : 'var(--primary)';
                        const label = CONFIG.FEATURE_LABELS[d.feature] || d.feature;
                        return `
                            <div style="display: flex; align-items: center; justify-content: space-between; font-size: 13px;">
                                <div style="width: 140px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${label}">${label}</div>
                                <div style="flex-grow: 1; margin: 0 12px; height: 8px; background: var(--surface); border-radius: 4px; overflow: hidden;">
                                    <div style="width: ${pct}%; height: 100%; background: ${color}; border-radius: 4px;"></div>
                                </div>
                                <div style="width: 40px; text-align: right; color: var(--text-secondary);">${d.impact.toFixed(3)}</div>
                            </div>
                        `;
                    }).join('')}
                </div>
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
        
        const usageTrend = document.getElementById('usage-trend');
        if (usageTrend) {
            usageTrend.innerHTML = `
                <div style="padding: 24px; text-align: center; color: var(--text-secondary); border: 1px dashed var(--border); border-radius: 4px; height: 100%; display: flex; align-items: center; justify-content: center; flex-direction: column;">
                    <p style="font-size: 13px;">Select a customer to view usage history.</p>
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
            console.error('Failed to load sample customers:', e.message);
        }
        
        const handleSearch = (e) => {
            const query = e.target.value.trim();
            const resultsContainer = document.getElementById('search-results');
            
            let matches = [];
            if (query.length === 0) {
                // Show first 10 samples when empty
                matches = this.sampleMsnos.slice(0, 10);
            } else {
                matches = this.sampleMsnos.filter(m => m.toLowerCase().includes(query.toLowerCase())).slice(0, 10);
            }
            
            if (matches.length === 0) {
                 resultsContainer.innerHTML = '<div style="padding: 12px; color: var(--text-secondary);">No matching sample customers found</div>';
                 return;
            }
            
            resultsContainer.innerHTML = matches.map(m => `
                <div style="padding: 12px; cursor: pointer; border-bottom: 1px solid var(--border); background: var(--surface);" onclick="app.selectCustomer('${m}')">
                    ${m}
                </div>
            `).join('');
        };
        
        searchInput.addEventListener('input', handleSearch);
        searchInput.addEventListener('focus', handleSearch);
        searchInput.addEventListener('click', handleSearch);
        
        // Hide dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target !== searchInput && !document.getElementById('search-results').contains(e.target)) {
                document.getElementById('search-results').innerHTML = '';
            }
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
                ${explain.top_drivers.map(d => {
                    // Extract feature name and direction, e.g. "registered_via_clean (High)"
                    let featureName = d;
                    let direction = "";
                    const match = d.match(/(.*?)\s*\((High|Low)\)$/);
                    if (match) {
                        featureName = match[1];
                        direction = ` (${match[2]})`;
                    }
                    const label = CONFIG.FEATURE_LABELS[featureName] || featureName;
                    return `<div style="padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 13px;">${label}${direction}</div>`;
                }).join('')}
            `;
            
            const actions = await apiFetch(`/customers/${encodeURIComponent(msno)}/suggested-action`);
            const actionsContainer = document.getElementById('suggested-actions');
            actionsContainer.innerHTML = `
                <div style="padding: 16px; background: var(--background); border-radius: 4px; border-left: 4px solid var(--primary);">
                    <div style="font-weight: 500; font-size: 16px; margin-bottom: 4px;">${actions.suggested_action}</div>
                    <div style="font-size: 13px; color: var(--text-secondary);">Based on drivers: ${actions.top_drivers_used.join(', ') || 'General factors'}</div>
                </div>
            `;
            
            const usageContainer = document.getElementById('usage-trend');
            if (usageContainer) {
                usageContainer.innerHTML = `<div style="padding: 24px; text-align: center; color: var(--text-secondary);">Loading usage history...</div>`;
                try {
                    const usage = await apiFetch(`/customers/${encodeURIComponent(msno)}/usage-history`);
                    if (!usage.history || usage.history.length === 0) {
                        usageContainer.innerHTML = `
                            <div style="padding: 24px; text-align: center; color: var(--text-secondary); border: 1px dashed var(--border); border-radius: 4px; height: 100%; display: flex; align-items: center; justify-content: center; flex-direction: column;">
                                <p style="font-size: 13px;">No streaming history available for this customer</p>
                                <p style="font-size: 12px; margin-top: 4px;">(No Synthetic Log Coverage)</p>
                            </div>
                        `;
                    } else {
                        const maxSecs = Math.max(...usage.history.map(h => h.total_secs)) || 1;
                        usageContainer.innerHTML = `
                            <div style="display: flex; align-items: flex-end; height: 150px; gap: 4px; padding-top: 20px;">
                                ${usage.history.map(h => {
                                    const hPct = (h.total_secs / maxSecs) * 100;
                                    return `
                                        <div style="flex-grow: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%;">
                                            <div style="width: 100%; background: var(--primary); height: ${hPct}%; min-height: 2px; border-radius: 2px 2px 0 0;" title="${h.date}: ${(h.total_secs/60).toFixed(1)} mins"></div>
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                            <div style="text-align: center; font-size: 12px; color: var(--text-secondary); margin-top: 8px;">Daily Streaming Usage (Total Seconds)</div>
                        `;
                    }
                } catch(err) {
                    usageContainer.innerHTML = `<div style="color: var(--danger); padding: 16px;">Failed to load history</div>`;
                }
            }
            
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
                
                this.renderLineChart('roc-curve', perf.curves?.roc?.fpr, perf.curves?.roc?.tpr, 'False Positive Rate', 'True Positive Rate');
                this.renderLineChart('pr-curve', perf.curves?.pr?.recall, perf.curves?.pr?.precision, 'Recall', 'Precision');
                this.renderConfusionMatrix(perf.curves?.confusion_matrix);
                
                
                this.renderLineChart('calibration-plot', perf.curves?.calibration?.prob_pred, perf.curves?.calibration?.prob_true, 'Mean Predicted Probability', 'Fraction of Positives');
                
                // For global shap in performance page, the element might not exist, but let's check
                if (document.getElementById('feature-importance')) {
                    this.renderGlobalShap({drivers: perf.global_shap}, 'feature-importance');
                }
                
            } catch(e) {
                this.showError('performance-cards', e.message);
            }
        }
    }
    
    renderLineChart(containerId, xVals, yVals, xLabel, yLabel) {
        const el = document.getElementById(containerId);
        if (!el || !xVals || !yVals) return;
        
        let pathData = '';
        for (let i = 0; i < xVals.length; i++) {
            const x = xVals[i] * 100;
            const y = 100 - (yVals[i] * 100);
            pathData += `${i === 0 ? 'M' : 'L'} ${x} ${y} `;
        }
        
        el.innerHTML = `
            <div style="position: relative; width: 100%; height: 200px; padding: 20px 0 20px 30px;">
                <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none" style="border-left: 1px solid var(--border); border-bottom: 1px solid var(--border);">
                    <path d="${pathData}" fill="none" stroke="var(--primary)" stroke-width="2" vector-effect="non-scaling-stroke"></path>
                    <line x1="0" y1="100" x2="100" y2="0" stroke="var(--border)" stroke-width="1" stroke-dasharray="4" vector-effect="non-scaling-stroke"></line>
                </svg>
                <div style="position: absolute; bottom: 0; left: 0; right: 0; text-align: center; font-size: 11px; color: var(--text-secondary);">${xLabel}</div>
                <div style="position: absolute; top: 0; bottom: 0; left: 0; display: flex; align-items: center; justify-content: center; width: 30px; font-size: 11px; color: var(--text-secondary); writing-mode: vertical-rl; transform: rotate(180deg);">${yLabel}</div>
            </div>
        `;
    }
    
    renderConfusionMatrix(cm) {
        const el = document.getElementById('confusion-matrix');
        if (!el || !cm) return;
        
        el.innerHTML = `
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
                <table style="border-collapse: collapse; text-align: center;">
                    <tr>
                        <td></td>
                        <td style="padding: 4px; font-size: 12px; color: var(--text-secondary);">Pred Negative</td>
                        <td style="padding: 4px; font-size: 12px; color: var(--text-secondary);">Pred Positive</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px; font-size: 12px; color: var(--text-secondary);">True Negative</td>
                        <td style="border: 1px solid var(--border); padding: 16px; background: rgba(29, 185, 84, 0.1); color: var(--success); font-weight: bold; font-size: 18px;">${cm.tn.toLocaleString()}</td>
                        <td style="border: 1px solid var(--border); padding: 16px; background: rgba(239, 68, 68, 0.1); color: var(--danger); font-weight: bold; font-size: 18px;">${cm.fp.toLocaleString()}</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px; font-size: 12px; color: var(--text-secondary);">True Positive</td>
                        <td style="border: 1px solid var(--border); padding: 16px; background: rgba(239, 68, 68, 0.1); color: var(--danger); font-weight: bold; font-size: 18px;">${cm.fn.toLocaleString()}</td>
                        <td style="border: 1px solid var(--border); padding: 16px; background: rgba(29, 185, 84, 0.1); color: var(--success); font-weight: bold; font-size: 18px;">${cm.tp.toLocaleString()}</td>
                    </tr>
                </table>
            </div>
        `;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new BeatDropApp();
});