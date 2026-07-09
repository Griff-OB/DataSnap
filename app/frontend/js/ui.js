/**
 * UI Class
 *
 * Manages all user interface interactions, state, and updates for the application.
 * This class orchestrates event listeners, data rendering in tables and charts,
 * and calls to the backend API via the global `window.api` object.
 */
class UI {
    constructor() {
        this.currentSection = 'preview';
        this.dataTable = null;
        this.rowQualityChart = null;
        this.cellQualityChart = null;
        this.currentData = null;
        this.currentPage = 1;
        this.pageSize = 50;
        this.totalRecords = 0;
        this.currentFilter = '';
        this.currentSort = { column: null, order: 'asc' };
        this.choicesInstances = {};
    }

    init() {
        this.initializeEventListeners();
        this.initializeDataTable();
        this.initializeChart();
        this.initializeChoices();
    }

    initializeChoices() {
        const choiceConfigs = {
            'missing-columns': { placeholderValue: 'Apply to All Columns', removeItemButton: true },
            'duplicate-columns': { placeholderValue: 'Check All Columns', removeItemButton: true },
            'outlier-columns': { placeholderValue: 'Apply to All Numeric Columns', removeItemButton: true },
            'string-op-columns': { placeholderValue: 'Apply to All Text Columns', removeItemButton: true },
            'find-replace-columns': { placeholderValue: 'Apply to All Text Columns', removeItemButton: true },
            'email-validation-columns': { placeholderValue: 'Apply to All Text Columns', removeItemButton: true },
        };

        for (const [elementId, config] of Object.entries(choiceConfigs)) {
            const element = document.getElementById(elementId);
            if (element) {
                this.choicesInstances[elementId] = new Choices(element, { placeholder: true, ...config });
            }
        }
    }

    initializeEventListeners() {
        const on = (id, ev, fn) => { const el = document.getElementById(id); if (el) el.addEventListener(ev, fn); };

        // Navigation & Theme
        document.querySelectorAll('.btn-operation').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchSection(e.target.dataset.section));
        });
        on('theme-selector', 'change', (e) => { document.documentElement.setAttribute('data-theme', e.target.value); });

        // File & Session Management
        on('upload-btn', 'click', () => document.getElementById('file-input').click());
        on('file-input', 'change', (e) => {
            const file = e.target.files[0];
            if (file) { e.target.value = null; this.handleFileUpload(file); }
        });
        on('save-session', 'click', () => this.saveSession());
        on('load-session', 'click', () => document.getElementById('session-input').click());
        on('session-input', 'change', (e) => { if (e.target.files[0]) this.loadSession(e.target.files[0]); });
        on('export-data-btn', 'click', () => this.handleExport());
        on('export-format', 'change', (e) => this.updateExportFilename(e.target.value));

        // Data Controls & Pagination
        on('refresh-data', 'click', () => this.refreshData());
        on('global-filter', 'input', (e) => { this.currentFilter = e.target.value; this.currentPage = 1; this.refreshData(); });

        // ✅ FIX: robust pagination handlers (+ preventDefault for <a>)
        const prevBtn = document.getElementById('prev-page');
        if (prevBtn) {
            prevBtn.addEventListener('click', (e) => {
                e.preventDefault?.();
                this.goToPage(this.currentPage - 1);
            });
        }
        const nextBtn = document.getElementById('next-page');
        if (nextBtn) {
            nextBtn.addEventListener('click', (e) => {
                e.preventDefault?.();
                this.goToPage(this.currentPage + 1);
            });
        }

        // Operations
        on('analyze-data', 'click', () => this.analyzeData());
        on('handle-missing', 'click', () => this.handleMissingValues());
        on('remove-duplicates', 'click', () => this.removeDuplicates());
        on('handle-outliers', 'click', () => this.handleOutliers());
        on('apply-string-ops', 'click', () => this.applyStringOperations());
        on('apply-find-replace', 'click', () => this.applyFindAndReplace());
        on('apply-email-validation', 'click', () => this.handleEmailValidation());
        on('sort-data', 'click', () => this.sortData());
        on('group-data', 'click', () => this.groupByData());
        on('add-calc-column', 'click', () => this.addCalculatedColumn());

        // Visualization
        on('generate-quality-chart', 'click', () => this.generateQualityChart());

        // Dynamic Form Controls
        on('missing-method', 'change', (e) => { document.getElementById('fill-value').style.display = e.target.value === 'fill_value' ? 'block' : 'none'; });
    }

    initializeDataTable() {
        this.dataTable = new Tabulator("#data-table", {
            height: "500px",
            layout: "fitColumns",
            placeholder: "No data available. Upload a file to get started.",
            movableColumns: true,
            resizableRows: true,
            cellEdited: (cell) => {
                const rowData = cell.getRow().getData();
                this.editCell(rowData.original_index, cell.getColumn().getField(), cell.getValue());
            },
        });
    }

    initializeChart() {
        const rowCtx = document.getElementById('row-quality-chart')?.getContext('2d');
        if (rowCtx) {
            this.rowQualityChart = new Chart(rowCtx, {
                type: 'pie',
                data: {
                    labels: ['Waiting for data...'],
                    datasets: [{ data: [1], backgroundColor: ['#ccc'] }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Row Quality (Clean vs. Duplicates)'
                        },
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
    
        const cellCtx = document.getElementById('cell-quality-chart')?.getContext('2d');
        if (cellCtx) {
            this.cellQualityChart = new Chart(cellCtx, {
                type: 'pie',
                data: {
                    labels: ['Waiting for data...'],
                    datasets: [{ data: [1], backgroundColor: ['#ccc'] }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Cell Quality (Valid vs. Missing)'
                        },
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
    }

    // ✅ New helper to clamp & change page
    goToPage(n) {
        const totalPages = Math.max(1, Math.ceil(this.totalRecords / this.pageSize));
        const next = Math.min(Math.max(1, n), totalPages);
        if (next !== this.currentPage) {
            this.currentPage = next;
            this.refreshData();
        }
    }

    switchSection(sectionName) {
        document.querySelectorAll('.btn-operation').forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[data-section="${sectionName}"]`)?.classList.add('active');
        document.querySelectorAll('.content-section').forEach(section => section.classList.remove('active'));
        document.getElementById(`${sectionName}-section`)?.classList.add('active');
        this.currentSection = sectionName;
        if (sectionName === 'preview') this.refreshData();
    }

    async handleFileUpload(file) {
        const progressBar = document.getElementById('upload-progress');
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        if (!progressBar || !progressFill || !progressText) return;

        progressBar.style.display = 'block';
        progressFill.style.width = '0%';
        progressText.textContent = '0%';

        try {
            const uploadId = Date.now().toString();
            const chunkSize = 1024 * 1024; // 1MB
            const totalChunks = Math.ceil(file.size / chunkSize);

            for (let i = 0; i < totalChunks; i++) {
                const start = i * chunkSize;
                const end = Math.min(start + chunkSize, file.size);
                const chunk = file.slice(start, end);
                const chunkData = {
                    file_chunk: chunk, upload_id: uploadId, chunk_index: i,
                    total_chunks: totalChunks, original_filename: file.name
                };

                const response = await window.api.uploadChunk(chunkData);
                if (response.status === 'error') throw new Error(response.message);

                const progress = Math.round(((i + 1) / totalChunks) * 100);
                progressFill.style.width = `${progress}%`;
                progressText.textContent = `${progress}%`;

                if (response.status === 'complete') {
                    this.showNotification('File uploaded successfully!', 'success');
                    this.updateFileInfo(file.name, response.rows, response.columns);
                    this.refreshData();
                    break;
                }
            }
        } catch (error) {
            this.showNotification(`Upload failed: ${error.message}`, 'error');
        } finally {
            setTimeout(() => { progressBar.style.display = 'none'; }, 1500);
        }
    }

    async refreshData() {
        try {
            const params = {
                page: this.currentPage, limit: this.pageSize, filter_val: this.currentFilter
            };
            if (this.currentSort.column) {
                params.sort_by = this.currentSort.column;
                params.sort_order = this.currentSort.order;
            }
            const response = await window.api.getData(params);
            if (response.status === 'success') {
                const data = JSON.parse(response.data);

                // ✅ Ensure numeric and fallback if backend omits it
                const total = Number(response.total_records);
                this.totalRecords = Number.isFinite(total) && total >= 0
                    ? total
                    : (Array.isArray(data) ? data.length : 0);

                this.currentData = data;
                this.updateDataTable(data);
                this.updatePagination();
                this.updateColumnSelects();
            }
        } catch (error) {
            this.showNotification(`Failed to load data: ${error.message}`, 'error');
        }
    }

    formatColumnTitle(field) {
        if (!field) return '';
        const withSpaces = field.replace(/_/g, ' ');
        return withSpaces.replace(/\b\w/g, char => char.toUpperCase());
    }

    updateDataTable(data) {
        if (!this.dataTable) return;
        this.dataTable.clearData();
        if (!data || data.length === 0) {
            this.dataTable.setColumns([]);
            return;
        }
        const newColumns = Object.keys(data[0])
            .filter(key => key !== 'original_index')
            .map(key => ({
                title: this.formatColumnTitle(key),
                field: key,
                editor: "input",
                minWidth: 120,
                headerFilter: "input",
                headerFilterPlaceholder: "Filter...",
                tooltip: true,
                headerTooltip: true,
            }));
            
        this.dataTable.setColumns(newColumns);
        this.dataTable.setData(data);
    }

    updatePagination() {
        const totalPages = Math.max(1, Math.ceil(this.totalRecords / this.pageSize));
        const pageInfo = document.getElementById('page-info');
        if (pageInfo) pageInfo.textContent = `Page ${this.currentPage} of ${totalPages}`;

        // ✅ FIX: use element property, not setAttribute
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');
        if (prevBtn) prevBtn.disabled = (this.currentPage <= 1);
        if (nextBtn) nextBtn.disabled = (this.currentPage >= totalPages);
    }

    updateColumnSelects() {
        const get = (id) => document.getElementById(id);
        const singleSelects = ['sort-column', 'group-column', 'agg-column'];
        const multiSelectIds = Object.keys(this.choicesInstances);

        if (!this.currentData || this.currentData.length === 0) {
            singleSelects.forEach(id => {
                const el = get(id);
                if (el) el.innerHTML = '<option value="">Select column</option>';
            });
            multiSelectIds.forEach(id => this.choicesInstances[id]?.clearStore());
            return;
        }

        const columns = Object.keys(this.currentData[0]).filter(k => k !== 'original_index');
        const choiceArray = columns.map(col => ({ value: col, label: this.formatColumnTitle(col) }));

        singleSelects.forEach(selectId => {
            const select = get(selectId);
            if (!select) return;
            const currentValue = select.value || '';
            select.innerHTML = '<option value="">Select column</option>';
            columns.forEach(col => {
                const option = document.createElement('option');
                option.value = col;
                option.textContent = this.formatColumnTitle(col);
                select.appendChild(option);
            });
            if (currentValue && columns.includes(currentValue)) select.value = currentValue;
        });

        multiSelectIds.forEach(id => {
            const inst = this.choicesInstances[id];
            if (!inst) return;
            inst.clearStore();
            inst.setChoices(choiceArray, 'value', 'label', true);
        });
    }

    async editCell(originalIndex, column, value) {
        try {
            await window.api.editCell({ original_index: originalIndex, column_name: column, new_value: value });
            this.showNotification('Cell updated successfully', 'success');
        } catch (error) {
            this.showNotification(`Failed to update cell: ${error.message}`, 'error');
            this.refreshData();
        }
    }

    async analyzeData() {
        try {
            const response = await window.api.getProfile();
            if (response.status === 'success') this.displayProfile(response.profile);
        } catch (error) {
            this.showNotification(`Failed to analyze data: ${error.message}`, 'error');
        }
    }

    // --- All operation handlers ---
    async handleMissingValues() {
        try {
            const data = {
                method: document.getElementById('missing-method').value,
                fill_value: document.getElementById('fill-value').value,
                columns: this.choicesInstances['missing-columns'].getValue(true)
            };
            const response = await window.api.handleMissingValues(data);
            this.showNotification(response.message, 'success');
            this.refreshData();
        } catch (error) {
            this.showNotification(`Operation failed: ${error.message}`, 'error');
        }
    }

    async removeDuplicates() {
        try {
            const data = { columns: this.choicesInstances['duplicate-columns'].getValue(true) };
            const response = await window.api.removeDuplicates(data);
            this.showNotification(response.message, 'success');
            this.refreshData();
        } catch (error) {
            this.showNotification(`Operation failed: ${error.message}`, 'error');
        }
    }

    async handleOutliers() {
        try {
            const data = {
                method: document.getElementById('outlier-method').value,
                columns: this.choicesInstances['outlier-columns'].getValue(true)
            };
            const response = await window.api.handleOutliers(data);
            this.showNotification(response.message, 'success');
            this.refreshData();
        } catch (error) {
            this.showNotification(`Operation failed: ${error.message}`, 'error');
        }
    }

    async applyStringOperations() {
        try {
            const data = {
                operation: document.getElementById('string-operation').value,
                columns: this.choicesInstances['string-op-columns'].getValue(true)
            };
            const response = await window.api.applyStringOperations(data);
            this.showNotification(response.message, 'success');
            this.refreshData();
        } catch (error) {
            this.showNotification(`Operation failed: ${error.message}`, 'error');
        }
    }

    async applyFindAndReplace() {
        const findValue = document.getElementById('find-value').value;
        if (!findValue) {
            this.showNotification("The 'Find' field cannot be empty.", 'warning');
            return;
        }
        try {
            const data = {
                find_value: findValue,
                replace_value: document.getElementById('replace-value').value,
                columns: this.choicesInstances['find-replace-columns'].getValue(true),
                match_case: document.getElementById('match-case').checked,
                use_regex: document.getElementById('use-regex').checked
            };
            const response = await window.api.findAndReplace(data);
            this.showNotification(response.message, 'success');
            this.refreshData();
        } catch (error) {
            this.showNotification(`Operation failed: ${error.message}`, 'error');
        }
    }

    async handleEmailValidation() {
        try {
            const data = {
                columns: this.choicesInstances['email-validation-columns'].getValue(true),
                action: document.getElementById('email-validation-action').value
            };
            const response = await window.api.validateEmails(data);
            this.showNotification(response.message, 'success');
            this.refreshData();
        } catch (error) {
            this.showNotification(`Operation failed: ${error.message}`, 'error');
        }
    }

    async sortData() {
        const column = document.getElementById('sort-column').value;
        if (!column) {
            this.showNotification('Please select a column to sort.', 'warning');
            return;
        }
        try {
            const data = {
                columns: [column],
                ascending: document.getElementById('sort-order').value === 'asc'
            };
            const response = await window.api.sortData(data);
            this.showNotification(response.message, 'success');
            this.refreshData();
        } catch (error) {
            this.showNotification(`Operation failed: ${error.message}`, 'error');
        }
    }

    async groupByData() {
        const groupColumn = document.getElementById('group-column').value;
        if (!groupColumn) {
            this.showNotification('Please select a column to group by.', 'warning');
            return;
        }
        try {
            const data = {
                group_columns: [groupColumn],
                agg_column: document.getElementById('agg-column').value,
                agg_function: document.getElementById('agg-function').value
            };
            const response = await window.api.groupByData(data);
            this.showNotification(response.message, 'success');
            this.refreshData();
        } catch (error) {
            this.showNotification(`Operation failed: ${error.message}`, 'error');
        }
    }

    async addCalculatedColumn() {
        const columnName = document.getElementById('calc-column-name').value;
        const expression = document.getElementById('calc-expression').value;
        if (!columnName || !expression) {
            this.showNotification('Please provide both a column name and an expression.', 'warning');
            return;
        }
        try {
            const response = await window.api.addCalculatedColumn({ column_name: columnName, expression: expression });
            this.showNotification(response.message, 'success');
            this.refreshData();
            document.getElementById('calc-column-name').value = '';
            document.getElementById('calc-expression').value = '';
        } catch (error) {
            this.showNotification(`Operation failed: ${error.message}`, 'error');
        }
    }

    async generateQualityChart() {
        try {
            const response = await window.api.getProfile();
            if (response.status === 'success') {
                const profile = response.profile;
                const themeBgColor = getComputedStyle(document.body).getPropertyValue('--bg-primary').trim() || '#ffffff';
    
                // Chart 1: Row Quality
                const cleanRows = profile.totalRows - profile.duplicateRows;
                const rowChartData = {
                    labels: ['Clean Rows', 'Duplicate Rows'],
                    datasets: [{
                        label: 'Row Count',
                        data: [cleanRows, profile.duplicateRows],
                        backgroundColor: ['#3b82f6', '#ef4444'],
                        borderColor: themeBgColor,
                        borderWidth: 2
                    }]
                };
    
                if (this.rowQualityChart) {
                    this.rowQualityChart.data = rowChartData;
                    this.rowQualityChart.update();
                }
    
                // Chart 2: Cell Quality (Invalid data = missing cells)
                const totalCells = profile.totalRows * profile.totalColumns;
                const validCells = totalCells > 0 ? totalCells - profile.missingCells : 0;
                const cellChartData = {
                    labels: ['Valid Cells', 'Missing Cells'],
                    datasets: [{
                        label: 'Cell Count',
                        data: [validCells, profile.missingCells],
                        backgroundColor: ['#10b981', '#f59e0b'],
                        borderColor: themeBgColor,
                        borderWidth: 2
                    }]
                };
    
                if (this.cellQualityChart) {
                    this.cellQualityChart.data = cellChartData;
                    this.cellQualityChart.update();
                }
            }
        } catch (error) {
            this.showNotification(`Failed to generate quality charts: ${error.message}`, 'error');
        }
    }
    
    // --- Session, Export, and Utility Methods ---
    
    async saveSession() {
        try {
            const response = await window.api.saveSession();
            if (response.status === 'success') {
                this.showNotification('Session saved successfully', 'success');
                const blob = new Blob([JSON.stringify(response, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `data_session_${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }
        } catch (error) {
            this.showNotification(`Failed to save session: ${error.message}`, 'error');
        }
    }

    async loadSession(file) {
        try {
            const response = await window.api.loadSession(file);
            if (response.status === 'success') {
                this.showNotification('Session loaded successfully', 'success');
                this.updateFileInfo(response.filename, response.rows, response.columns);
                this.refreshData();
            }
        } catch (error) {
            this.showNotification(`Failed to load session: ${error.message}`, 'error');
        }
    }

    async handleExport() {
        const exportBtn = document.getElementById('export-data-btn');
        if (!exportBtn) return;
        
        const originalText = exportBtn.innerHTML;
        exportBtn.innerHTML = 'Exporting...';
        exportBtn.disabled = true;

        try {
            const format = document.getElementById('export-format').value;
            let filename = document.getElementById('export-filename').value || document.getElementById('export-filename').placeholder;
            const blob = await window.api.exportData({ format, filename });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
            this.showNotification('File exported successfully!', 'success');
        } catch (error) {
            this.showNotification(`Export failed: ${error.message}`, 'error');
        } finally {
            exportBtn.innerHTML = originalText;
            exportBtn.disabled = false;
        }
    }

    displayProfile(profile) {
        const profileContent = document.getElementById('profile-content');
        if (!profileContent) return;
        let piiList = Object.entries(profile.piiSummary).map(([col, types]) => {
            const typeNames = Array.isArray(types) ? types.map(t => t.type || t).join(', ') : 'Unknown';
            return `<li><strong>${this.formatColumnTitle(col)}:</strong> ${typeNames}</li>`;
        }).join('');
        let html = `
            <div class="profile-overview"><h3>Dataset Overview</h3><div class="profile-stats">
                <div class="stat-item"><strong>Total Rows:</strong> ${profile.totalRows.toLocaleString()}</div>
                <div class="stat-item"><strong>Total Columns:</strong> ${profile.totalColumns}</div>
                <div class="stat-item"><strong>Missing Cells:</strong> ${profile.missingCells.toLocaleString()}</div>
                <div class="stat-item"><strong>Duplicate Rows:</strong> ${profile.duplicateRows.toLocaleString()}</div>
            </div></div><div class="quality-scores"><h3>Data Quality Scores</h3><div class="score-grid">
                <div class="score-item"><div class="score-label">Overall</div><div class="score-value ${this.getScoreClass(profile.overallScore)}">${profile.overallScore}%</div></div>
                <div class="score-item"><div class="score-label">Completeness</div><div class="score-value ${this.getScoreClass(profile.completenessScore)}">${profile.completenessScore}%</div></div>
                <div class="score-item"><div class="score-label">Uniqueness</div><div class="score-value ${this.getScoreClass(profile.uniquenessScore)}">${profile.uniquenessScore}%</div></div>
                <div class="score-item"><div class="score-label">Consistency</div><div class="score-value ${this.getScoreClass(profile.consistencyScore)}">${profile.consistencyScore}%</div></div>
                <div class="score-item"><div class="score-label">Validity</div><div class="score-value ${this.getScoreClass(profile.validityScore)}">${profile.validityScore}%</div></div>
            </div></div>`;
        if (profile.piiDetected) {
            html += `<div class="pii-warning"><h3>⚠️ PII Data Detected</h3><p>Personally Identifiable Information may be present in the following columns:</p><ul>${piiList}</ul></div>`;
        }
        if (profile.recommendations && profile.recommendations.length > 0) {
            html += `<div class="recommendations"><h3>Recommendations</h3><ul>${profile.recommendations.map(rec => `<li>${rec}</li>`).join('')}</ul></div>`;
        }
        profileContent.innerHTML = html;
    }

    getScoreClass(score) {
        if (score >= 90) return 'score-excellent';
        if (score >= 70) return 'score-good';
        if (score >= 50) return 'score-fair';
        return 'score-poor';
    }

    updateExportFilename(format) {
        const filenameInput = document.getElementById('export-filename');
        if (!filenameInput) return;
        const currentName = filenameInput.value || filenameInput.placeholder || 'export';
        const baseName = currentName.split('.')[0];
        filenameInput.placeholder = `${baseName}.${format}`;
    }

    updateFileInfo(filename, rows, columns) {
        const fileInfo = document.getElementById('file-info');
        if (fileInfo) {
            fileInfo.innerHTML = `<p><strong>File:</strong> ${filename}</p><p><strong>Rows:</strong> ${rows.toLocaleString()}</p><p><strong>Columns:</strong> ${columns}</p>`;
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => notification.classList.add('show'), 10);
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

window.ui = new UI();
