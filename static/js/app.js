/**
 * MediAssist Dashboard Application Logic
 * Handles tabs, polling, forms, and UI interactions
 */

const App = {
    // Config
    config: {
        pollIntervals: {
            queue: 3000,      // 3 seconds
            hitl: 5000,       // 5 seconds
            dashboard: 10000, // 10 seconds
        },
        pharmacistId: localStorage.getItem('pharmacistId') || 'PH_001',
    },

    // State
    state: {
        currentTab: 'queue',
        pollTimers: {},
        workflows: [],
        metrics: { total: 0, success: 0, failed: 0, awaiting: 0 },
        hitlList: [],
    },

    /**
     * Initialize app on page load
     */
    init() {
        console.log('Initializing MediAssist Dashboard');
        this.setupTabListeners();
        this.setupFormListeners();
        this.setupSettingsModal();
        this.checkHealth();

        // Start with Queue tab
        this.switchTab('queue');
    },

    /**
     * Tab switching logic
     */
    setupTabListeners() {
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.dataset.tab;
                this.switchTab(tab);
            });
        });
    },

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('hidden', content.id !== `tab-${tabName}`);
        });

        this.state.currentTab = tabName;

        // Stop all polls
        this.stopAllPolls();

        // Start relevant poll
        if (tabName === 'queue') {
            this.loadQueue();
            this.startPoll('queue', () => this.loadQueue());
        } else if (tabName === 'hitl') {
            this.loadHITLList();
            this.startPoll('hitl', () => this.loadHITLList());
        } else if (tabName === 'dashboard') {
            this.loadDashboard();
            this.startPoll('dashboard', () => this.loadDashboard());
        }
    },

    /**
     * Polling mechanism
     */
    startPoll(name, callback) {
        if (this.state.pollTimers[name]) {
            clearInterval(this.state.pollTimers[name]);
        }
        this.state.pollTimers[name] = setInterval(callback, this.config.pollIntervals[name]);
    },

    stopAllPolls() {
        Object.keys(this.state.pollTimers).forEach(key => {
            clearInterval(this.state.pollTimers[key]);
        });
        this.state.pollTimers = {};
    },

    /**
     * Health check
     */
    async checkHealth() {
        try {
            const health = await API.healthCheck();
            this.setStatus('ok', `API Connected (${health.status})`);
        } catch (error) {
            this.setStatus('error', 'API Disconnected');
        }
    },

    /**
     * Load and display prescription queue
     */
    async loadQueue() {
        try {
            this.showLoading('queue');

            const limit = document.getElementById('queue-limit')?.value || 10;
            const status = document.getElementById('queue-status-filter')?.value || '';
            const data = await API.getWorkflows(limit, 0, status || null);

            this.state.workflows = data.items || [];
            this.renderQueueTable();
            this.updateRefreshTime('queue');
        } catch (error) {
            this.showError('queue', error.message);
        }
    },

    renderQueueTable() {
        const tbody = document.getElementById('queue-table-body');
        if (!tbody) return;

        tbody.innerHTML = this.state.workflows.map(wf => {
            const statusClass = {
                'IN_PROGRESS': 'bg-blue-50 text-blue-700',
                'AWAITING_HUMAN': 'bg-yellow-50 text-yellow-700',
                'COMPLETED': 'bg-green-50 text-green-700',
                'FAILED': 'bg-red-50 text-red-700',
            }[wf.workflow_status] || 'bg-gray-50';

            return `
        <tr class="border-b hover:bg-gray-50">
          <td class="px-4 py-3 text-sm font-medium text-gray-900">${wf.workflow_id.slice(0, 8)}...</td>
          <td class="px-4 py-3 text-sm text-gray-600">${wf.patient_id}</td>
          <td class="px-4 py-3 text-sm text-gray-600">${wf.current_step}</td>
          <td class="px-4 py-3"><span class="px-3 py-1 rounded-full text-xs font-semibold ${statusClass}">${wf.workflow_status}</span></td>
          <td class="px-4 py-3 text-sm text-gray-500">${new Date(wf.created_at).toLocaleTimeString()}</td>
          <td class="px-4 py-3 text-sm">
            <button onclick="App.viewWorkflow('${wf.workflow_id}')" class="text-blue-600 hover:text-blue-900 font-medium">View</button>
            ${wf.awaiting_human ? `<button onclick="App.switchToHITL('${wf.workflow_id}')" class="ml-3 text-orange-600 hover:text-orange-900 font-medium">Approve</button>` : ''}
          </td>
        </tr>
      `;
        }).join('');

        if (this.state.workflows.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="px-4 py-8 text-center text-gray-500">No prescriptions found</td></tr>';
        }
    },

    /**
     * View workflow details in modal
     */
    async viewWorkflow(workflowId) {
        try {
            const wf = await API.getWorkflow(workflowId);
            const modal = document.getElementById('detail-modal');

            let validationHtml = 'No validation data';
            if (wf.validation_result) {
                validationHtml = `
          <div class="bg-gray-50 p-3 rounded">
            <p><strong>Risk Score:</strong> ${wf.validation_result.risk_score}</p>
            <p><strong>Safe Dosage:</strong> ${wf.validation_result.dosage_safe ? '✓' : '✗'}</p>
            ${wf.validation_result.interactions?.length ? `<p><strong>Interactions:</strong> ${wf.validation_result.interactions.join(', ')}</p>` : ''}
            ${wf.validation_result.contraindications?.length ? `<p><strong>Contraindications:</strong> ${wf.validation_result.contraindications.map(c => typeof c === 'string' ? c : c.condition).join(', ')}</p>` : ''}
          </div>
        `;
            }

            modal.innerHTML = `
        <div class="fixed inset-0 bg-black bg-opacity-50 z-40" onclick="App.closeModal()"></div>
        <div class="fixed inset-0 z-50 flex items-center justify-center">
          <div class="bg-white rounded-lg shadow-lg max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
            <div class="p-6 border-b flex justify-between items-center">
              <h3 class="text-lg font-bold">Workflow Details</h3>
              <button onclick="App.closeModal()" class="text-gray-500 hover:text-gray-700">✕</button>
            </div>
            <div class="p-6 space-y-4">
              <div><strong>ID:</strong> ${wf.workflow_id}</div>
              <div><strong>Patient:</strong> ${wf.patient_id}</div>
              <div><strong>Status:</strong> ${wf.workflow_status}</div>
              <div><strong>Current Step:</strong> ${wf.current_step}</div>
              <div><strong>Created:</strong> ${new Date(wf.created_at).toLocaleString()}</div>
              <div><strong>Validation:</strong> ${validationHtml}</div>
              ${wf.errors?.length ? `<div class="text-red-600"><strong>Errors:</strong> ${wf.errors.join(', ')}</div>` : ''}
            </div>
          </div>
        </div>
      `;
        } catch (error) {
            this.showError('queue', error.message);
        }
    },

    closeModal() {
        document.getElementById('detail-modal').innerHTML = '';
    },

    /**
     * HITL Approval tab
     */
    async loadHITLList() {
        try {
            this.showLoading('hitl');
            const data = await API.getWorkflows(100, 0, 'AWAITING_HUMAN');
            this.state.hitlList = data.items || [];
            this.renderHITLList();
            this.updateRefreshTime('hitl');
        } catch (error) {
            this.showError('hitl', error.message);
        }
    },

    renderHITLList() {
        const container = document.getElementById('hitl-list');
        if (!container) return;

        if (this.state.hitlList.length === 0) {
            container.innerHTML = '<div class="text-center py-8 text-gray-500">No prescriptions awaiting human review</div>';
            return;
        }

        container.innerHTML = this.state.hitlList.map(wf => {
            const validation = wf.validation_result || {};
            const inventory = wf.inventory_status || {};

            return `
        <div class="bg-white border-l-4 border-orange-500 p-6 mb-4 rounded shadow-sm">
          <div class="grid grid-cols-2 gap-4 mb-4">
            <div>
              <div class="text-sm text-gray-600"><strong>Workflow ID:</strong></div>
              <div class="font-mono text-sm">${wf.workflow_id.slice(0, 12)}...</div>
              
              <div class="text-sm text-gray-600 mt-2"><strong>Patient ID:</strong></div>
              <div>${wf.patient_id}</div>
            </div>
            <div>
              <div class="text-sm text-gray-600"><strong>Risk Score:</strong></div>
              <div class="text-2xl font-bold text-orange-600">${(validation.risk_score * 100).toFixed(0)}%</div>
              
              <div class="text-sm text-gray-600 mt-2"><strong>Stock Available:</strong></div>
              <div>${inventory.available ? '✓ Yes' : '✗ No'}</div>
            </div>
          </div>

          ${validation.interactions?.length ? `
          <div class="mb-3 p-2 bg-yellow-50 border border-yellow-200 rounded">
            <strong class="text-sm text-yellow-900">⚠ Interactions:</strong>
            <div class="text-sm text-yellow-800">${validation.interactions.join(', ')}</div>
          </div>
          ` : ''}

          ${validation.contraindications?.length ? `
          <div class="mb-3 p-2 bg-red-50 border border-red-200 rounded">
            <strong class="text-sm text-red-900">⛔ Contraindications:</strong>
            <div class="text-sm text-red-800">
              ${validation.contraindications.map(c => typeof c === 'string' ? c : c.condition).join(', ')}
            </div>
          </div>
          ` : ''}

          <div class="mb-4 p-2 bg-blue-50 border border-blue-200 rounded">
            <strong class="text-sm text-blue-900">Clinical Notes:</strong>
            <div class="text-sm text-blue-800">${validation.reasoning || 'No clinical notes available'}</div>
          </div>

          <div class="flex gap-3 mt-4">
            <textarea id="notes-${wf.workflow_id}" placeholder="Add approval notes..." class="flex-1 p-2 border rounded text-sm"></textarea>
          </div>
          <div class="flex gap-3 mt-3">
            <button onclick="App.submitApproval('${wf.workflow_id}', true)" class="flex-1 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 font-semibold">Approve</button>
            <button onclick="App.submitApproval('${wf.workflow_id}', false)" class="flex-1 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 font-semibold">Reject</button>
          </div>
        </div>
      `;
        }).join('');
    },

    async submitApproval(workflowId, approved) {
        try {
            const notes = document.getElementById(`notes-${workflowId}`)?.value || '';

            if (approved) {
                await API.approvePrescription(workflowId, notes, this.config.pharmacistId);
                this.showNotification('success', '✓ Prescription approved');
            } else {
                await API.rejectPrescription(workflowId, notes, this.config.pharmacistId);
                this.showNotification('success', '✓ Prescription rejected');
            }

            this.loadHITLList();
        } catch (error) {
            this.showNotification('error', `Error: ${error.message}`);
        }
    },

    switchToHITL(workflowId) {
        this.switchTab('hitl');
    },

    /**
     * Dashboard metrics
     */
    async loadDashboard() {
        try {
            this.showLoading('dashboard');
            const data = await API.getWorkflows(1000, 0);

            const workflows = data.items || [];
            const total = workflows.length;
            const completed = workflows.filter(w => w.workflow_status === 'COMPLETED').length;
            const failed = workflows.filter(w => w.workflow_status === 'FAILED').length;
            const awaiting = workflows.filter(w => w.awaiting_human).length;
            const inProgress = workflows.filter(w => w.workflow_status === 'IN_PROGRESS').length;

            this.state.metrics = {
                total,
                completed,
                failed,
                awaiting,
                inProgress,
                successRate: total > 0 ? Math.round((completed / total) * 100) : 0,
            };

            this.renderDashboard();
            this.updateRefreshTime('dashboard');
        } catch (error) {
            this.showError('dashboard', error.message);
        }
    },

    renderDashboard() {
        const metrics = this.state.metrics;
        const metricsContainer = document.getElementById('metrics-grid');

        if (metricsContainer) {
            metricsContainer.innerHTML = `
        <div class="bg-white p-6 rounded-lg shadow-sm border-l-4 border-blue-500">
          <div class="text-gray-600 text-sm">Total Processed</div>
          <div class="text-4xl font-bold text-blue-600 mt-2">${metrics.total}</div>
        </div>
        <div class="bg-white p-6 rounded-lg shadow-sm border-l-4 border-green-500">
          <div class="text-gray-600 text-sm">Success Rate</div>
          <div class="text-4xl font-bold text-green-600 mt-2">${metrics.successRate}%</div>
        </div>
        <div class="bg-white p-6 rounded-lg shadow-sm border-l-4 border-yellow-500">
          <div class="text-gray-600 text-sm">Awaiting Review</div>
          <div class="text-4xl font-bold text-yellow-600 mt-2">${metrics.awaiting}</div>
        </div>
        <div class="bg-white p-6 rounded-lg shadow-sm border-l-4 border-red-500">
          <div class="text-gray-600 text-sm">Failed</div>
          <div class="text-4xl font-bold text-red-600 mt-2">${metrics.failed}</div>
        </div>
        <div class="bg-white p-6 rounded-lg shadow-sm border-l-4 border-purple-500">
          <div class="text-gray-600 text-sm">In Progress</div>
          <div class="text-4xl font-bold text-purple-600 mt-2">${metrics.inProgress}</div>
        </div>
        <div class="bg-white p-6 rounded-lg shadow-sm border-l-4 border-indigo-500">
          <div class="text-gray-600 text-sm">Completed</div>
          <div class="text-4xl font-bold text-indigo-600 mt-2">${metrics.completed}</div>
        </div>
      `;
        }

        // Simple chart via text
        const chartContainer = document.getElementById('status-chart');
        if (chartContainer) {
            const total = metrics.total || 1;
            const completedPct = Math.round((metrics.completed / total) * 100);
            const failedPct = Math.round((metrics.failed / total) * 100);
            const awaitingPct = Math.round((metrics.awaiting / total) * 100);
            const inProgressPct = Math.round((metrics.inProgress / total) * 100);

            chartContainer.innerHTML = `
        <div class="space-y-3">
          <div>
            <div class="flex justify-between text-sm mb-1">
              <span>Completed</span>
              <span class="font-semibold">${completedPct}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div class="bg-green-600 h-2 rounded-full" style="width: ${completedPct}%"></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-sm mb-1">
              <span>Failed</span>
              <span class="font-semibold">${failedPct}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div class="bg-red-600 h-2 rounded-full" style="width: ${failedPct}%"></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-sm mb-1">
              <span>Awaiting Review</span>
              <span class="font-semibold">${awaitingPct}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div class="bg-yellow-600 h-2 rounded-full" style="width: ${awaitingPct}%"></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-sm mb-1">
              <span>In Progress</span>
              <span class="font-semibold">${inProgressPct}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div class="bg-purple-600 h-2 rounded-full" style="width: ${inProgressPct}%"></div>
            </div>
          </div>
        </div>
      `;
        }
    },

    /**
     * Form listeners
     */
    setupFormListeners() {
        // Queue filters
        const filterBtn = document.getElementById('queue-filter-btn');
        if (filterBtn) {
            filterBtn.addEventListener('click', () => this.loadQueue());
        }

        // New prescription form
        const uploadForm = document.getElementById('upload-form');
        if (uploadForm) {
            uploadForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.submitNewPrescription();
            });
        }

        // Refresh buttons
        document.querySelectorAll('.refresh-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.target.dataset.tab;
                if (tab === 'queue') this.loadQueue();
                else if (tab === 'hitl') this.loadHITLList();
                else if (tab === 'dashboard') this.loadDashboard();
            });
        });
    },

    async submitNewPrescription() {
        try {
            const patientId = document.getElementById('patient-id')?.value;
            const prescriptionText = document.getElementById('prescription-text')?.value;

            if (!patientId || !prescriptionText) {
                this.showNotification('error', 'Please fill in all fields');
                return;
            }

            const result = await API.uploadPrescription(patientId, prescriptionText);
            this.showNotification('success', `✓ Prescription submitted: ${result.workflow_id.slice(0, 12)}...`);

            // Reset form
            document.getElementById('upload-form').reset();

            // Refresh queue
            this.loadQueue();
        } catch (error) {
            this.showNotification('error', `Error: ${error.message}`);
        }
    },

    setupSettingsModal() {
        const settingsBtn = document.getElementById('settings-btn');
        const settingsModal = document.getElementById('settings-modal');
        const closeBtn = settingsModal?.querySelector('button');

        if (settingsBtn && settingsModal) {
            settingsBtn.addEventListener('click', () => {
                settingsModal.classList.remove('hidden');
                document.getElementById('pharmacist-id-input').value = this.config.pharmacistId;
            });

            closeBtn.addEventListener('click', () => {
                settingsModal.classList.add('hidden');
            });

            document.getElementById('save-settings-btn')?.addEventListener('click', () => {
                const newId = document.getElementById('pharmacist-id-input').value;
                if (newId) {
                    this.config.pharmacistId = newId;
                    localStorage.setItem('pharmacistId', newId);
                    this.showNotification('success', 'Settings saved');
                    settingsModal.classList.add('hidden');
                }
            });
        }
    },

    /**
     * UI Helpers
     */
    showNotification(type, message) {
        const container = document.getElementById('notifications');
        if (!container) return;

        const classes = {
            success: 'bg-green-500 text-white',
            error: 'bg-red-500 text-white',
            info: 'bg-blue-500 text-white',
        }[type] || 'bg-gray-500 text-white';

        const notif = document.createElement('div');
        notif.className = `${classes} px-4 py-3 rounded mb-2 animate-slide-in`;
        notif.textContent = message;
        container.appendChild(notif);

        setTimeout(() => notif.remove(), 4000);
    },

    showLoading(tabName) {
        const tabContent = document.getElementById(`tab-${tabName}`);
        if (tabContent) {
            const spinner = tabContent.querySelector('.spinner');
            if (spinner) spinner.classList.remove('hidden');
        }
    },

    showError(tabName, message) {
        const tabContent = document.getElementById(`tab-${tabName}`);
        if (tabContent) {
            const spinner = tabContent.querySelector('.spinner');
            if (spinner) spinner.classList.add('hidden');
        }
        this.showNotification('error', message);
    },

    updateRefreshTime(tabName) {
        const timeEl = document.getElementById(`refresh-time-${tabName}`);
        if (timeEl) {
            timeEl.textContent = new Date().toLocaleTimeString();
        }
    },

    setStatus(status, message) {
        const statusEl = document.getElementById('status-message');
        if (statusEl) {
            statusEl.textContent = message;
            statusEl.className = status === 'ok' ? 'text-green-600' : 'text-red-600';
        }
    },
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
