class ChartManager {
    constructor() {
        this.charts = new Map();
    }

    createChart(canvasId, config) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.error(`Canvas with id ${canvasId} not found`);
            return null;
        }
        const ctx = canvas.getContext('2d');
        const chart = new Chart(ctx, config);
        this.charts.set(canvasId, chart);
        return chart;
    }

    updateChart(canvasId, newData) {
        const chart = this.charts.get(canvasId);
        if (chart) {
            chart.data = newData;
            chart.update();
        }
    }

    destroyChart(canvasId) {
        const chart = this.charts.get(canvasId);
        if (chart) {
            chart.destroy();
            this.charts.delete(canvasId);
        }
    }

    generateBarChart(labels, data, label = 'Data') {
        return {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: data,
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        };
    }

    generateLineChart(labels, data, label = 'Data') {
        return {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: data,
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        };
    }

    generatePieChart(labels, data) {
        const colors = [
            '#3b82f6', '#ef4444', '#10b981', '#f59e0b',
            '#8b5cf6', '#06b6d4', '#84cc16', '#f97316',
            '#ec4899', '#6b7280', '#14b8a6', '#f97316'
        ];
        return {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.slice(0, data.length),
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        };
    }

    generateScatterChart(data, label = 'Data') {
        return {
            type: 'scatter',
            data: {
                datasets: [{
                    label: label,
                    data: data,
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom'
                    },
                    y: {
                        beginAtZero: true
                    }
                }
            }
        };
    }
}

// Create global chart manager
window.chartManager = new ChartManager();
