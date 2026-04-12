/**
 * API Client for MediAssist Frontend
 * Handles all communication with the FastAPI backend
 */

const API = {
    BASE_URL: '',  // Root path - FastAPI routes are at / not /api

    /**
     * Generic fetch wrapper with error handling
     */
    async request(endpoint, options = {}) {
        const url = `${this.BASE_URL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
        };

        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || data.error || `HTTP ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error(`API Error: ${endpoint}`, error);
            throw error;
        }
    },

    /**
     * Health check - verify API is running
     */
    async healthCheck() {
        return this.request('/health', { method: 'GET' });
    },

    /**
     * Upload a new prescription
     */
    async uploadPrescription(patientId, prescriptionText, metadata = {}) {
        return this.request('/prescriptions/upload', {
            method: 'POST',
            body: JSON.stringify({
                patient_id: patientId,
                prescription_text: prescriptionText,
                metadata: metadata,
            }),
        });
    },

    /**
     * Get all workflows/prescriptions (paginated)
     */
    async getWorkflows(limit = 10, offset = 0, statusFilter = null) {
        let endpoint = `/prescriptions?limit=${limit}&offset=${offset}`;
        if (statusFilter) {
            endpoint += `&status_filter=${statusFilter}`;
        }
        return this.request(endpoint, { method: 'GET' });
    },

    /**
     * Get single workflow details
     */
    async getWorkflow(workflowId) {
        return this.request(`/prescriptions/${workflowId}`, { method: 'GET' });
    },

    /**
     * Get HITL review details for approval
     */
    async getHITLReview(workflowId) {
        return this.request(`/prescriptions/${workflowId}/review`, { method: 'GET' });
    },

    /**
     * Approve a prescription
     */
    async approvePrescription(workflowId, notes = '', pharmacistId = 'PH_001') {
        return this.request(`/prescriptions/${workflowId}/approve`, {
            method: 'POST',
            body: JSON.stringify({
                approved: true,
                notes: notes,
                pharmacist_id: pharmacistId,
            }),
        });
    },

    /**
     * Reject a prescription
     */
    async rejectPrescription(workflowId, notes = '', pharmacistId = 'PH_001') {
        return this.request(`/prescriptions/${workflowId}/reject`, {
            method: 'POST',
            body: JSON.stringify({
                approved: false,
                notes: notes,
                pharmacist_id: pharmacistId,
            }),
        });
    },
};

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API;
}
