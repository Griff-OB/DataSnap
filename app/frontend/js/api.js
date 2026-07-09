/**
 * API Class
 *
 * This class provides a centralized interface for all communication
 * with the backend server. It handles request/response logic,
 * error handling, and data formatting.
 */
class API {
    constructor() {
        this.baseURL = '/api';
    }

    /**
     * Generic request handler for API calls. It intelligently handles
     * headers for JSON and FormData requests.
     * @param {string} endpoint - The API endpoint to call (e.g., '/profile').
     * @param {object} options - Standard fetch options (method, body, headers, etc.).
     * @returns {Promise<any>} - A promise that resolves to the response data.
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const fetchOptions = { ...options };
        if (!fetchOptions.headers) {
            fetchOptions.headers = {};
        }
        if (!(options.body instanceof FormData)) {
            fetchOptions.headers['Content-Type'] = 'application/json';
        }

        try {
            const response = await fetch(url, fetchOptions);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || `HTTP error! Status: ${response.status}`);
            }
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                return await response.json();
            }
            return response; // Return the raw response for non-JSON content (like blobs)
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // --- Data Operations ---

    async uploadChunk(chunkData) {
        const formData = new FormData();
        Object.keys(chunkData).forEach(key => {
            formData.append(key, chunkData[key]);
        });
        return this.request('/upload', {
            method: 'POST',
            body: formData,
        });
    }

    async getData(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/data?${queryString}`);
    }

    async editCell(data) {
        return this.request('/edit-cell', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async exportData(options = {}) {
        const response = await this.request('/export', {
            method: 'POST',
            body: JSON.stringify(options)
        });
        return response.blob();
    }

    // --- Analysis Operations ---

    async getProfile() {
        return this.request('/profile');
    }

    // --- Cleaning Operations ---

    async handleMissingValues(data) {
        return this.request('/clean/handle-missing', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async removeDuplicates(data = {}) {
        return this.request('/clean/remove-duplicates', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async handleOutliers(data) {
        return this.request('/clean/handle-outliers', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async applyStringOperations(data) {
        return this.request('/clean/string-ops', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async findAndReplace(data) {
        return this.request('/clean/find-replace', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * FIX: ADDED THE MISSING FUNCTION
     * Performs email validation on specified columns.
     * @param {object} data - { columns, action: 'clear' | 'remove_row' }.
     * @returns {Promise<object>} A promise resolving to the operation result.
     */
    async validateEmails(data) {
        return this.request('/clean/validate-emails', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // --- Transform Operations ---

    async sortData(data) {
        return this.request('/transform/sort', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async groupByData(data) {
        return this.request('/transform/group-by', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async pivotData(data) {
        return this.request('/transform/pivot', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async addCalculatedColumn(data) {
        return this.request('/transform/calculated-column', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // --- Session Operations ---

    async saveSession() {
        return this.request('/session/save', {
            method: 'POST'
        });
    }

    async loadSession(file) {
        const formData = new FormData();
        formData.append('session_file', file);
        return this.request('/session/load', {
            method: 'POST',
            body: formData,
        });
    }
}

window.api = new API();