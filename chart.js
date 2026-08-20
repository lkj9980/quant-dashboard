// chart.js
async function loadChart() {
    try {
        const response = await fetch('quant_log.csv');
        if (!response.ok) return;
        
        const data = await response.text();
        const rows = data.trim().split(/\r?\n/);
        const headers = rows[0].split(',').map(h => h.trim());
        const labels = [];
        const datasetsMap = {};
        
        for (let i = 1; i < headers.length; i++) datasetsMap[headers[i]] = [];
        
        rows.slice(-30).forEach(row => {
            const cols = row.split(',').map(c => c.trim());
            if (cols.length < headers.length) return;
            labels.push(cols[0]);
            for (let i = 1; i < headers.length; i++) {
                datasetsMap[headers[i]].push(parseFloat(cols[i]) || 0);
            }
        });

        const colors = ['#2563eb', '#dc2626', '#16a34a', '#ca8a04', '#9333ea', '#0284c7'];
        const chartDatasets = Object.keys(datasetsMap).map((key, idx) => ({
            label: key,
            data: datasetsMap[key],
            borderColor: colors[idx % colors.length],
            borderWidth: 1.5,
            pointRadius: 1,
            tension: 0.1
        }));

        const ctx = document.getElementById('quantChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: { labels: labels, datasets: chartDatasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { grid: { color: '#f1f5f9' } },
                    x: { grid: { display: false }, ticks: { maxTicksLimit: 6 } }
                }
            }
        });
    } catch (e) {
        console.error("차트 로딩 에러:", e);
    }
}

document.addEventListener('DOMContentLoaded', loadChart);
