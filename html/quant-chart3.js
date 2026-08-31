 
        let globalRawRows = [];
        let globalHeaders = [];
        let chartInstances = {};
        let currentLimit = 20;

        let chartStates = {
            chartDomestic: { '코스피': true, '코스닥': true },
            chartGlobal: { 'S&P 500': true, '나스닥 종합': true },
            chartMacro: { '원/달러 환율': true, '미국채 10년': true },
            chartCommodity: { 'WTI유': true, 'VIX 지수': true }
        };

        const chartColors = {
            '코스피': '#2563eb', '코스닥': '#db2777',
            'S&P 500': '#4f46e5', '나스닥 종합': '#0284c7',
            '원/달러 환율': '#ea580c', '미국채 10년': '#16a34a',
            'WTI유': '#ca8a04', 'VIX 지수': '#9333ea'
        };

        function logDebug(msg) {
            const box = document.getElementById('debug-view');
            if (!box) return;
            box.innerText += "\n" + msg;
            console.log("[DEBUG] " + msg);
        }

        function toggleDebug() {
            const box = document.getElementById('debug-view');
            if (box) box.classList.toggle('hidden');
        }

        function toggleChartSection() {
            const section = document.getElementById('charts-container-section');
            if (section) section.classList.toggle('hidden');
        }

        function setPeriod(limit) {
            currentLimit = limit;
            ['20', '60', 'all'].forEach(id => {
                const btn = document.getElementById('btn-' + id);
                if (btn) btn.className = "text-xs px-3.5 py-1.5 rounded-xl bg-slate-100 text-slate-600 hover:bg-slate-200 font-semibold transition";
            });
            const activeId = limit === 20 ? 'btn-20' : (limit === 60 ? 'btn-60' : 'btn-all');
            const activeBtn = document.getElementById(activeId);
            if (activeBtn) activeBtn.className = "text-xs px-3.5 py-1.5 rounded-xl bg-blue-600 text-white font-bold transition shadow-sm";

            renderAllCharts();
        }

        async function loadData() {
            // 4개 차트 전체를 커버하는 확장 샘플 CSV 데이터
            const sampleCsv = `Date,코스피,코스닥,S&P 500,나스닥 종합,원/달러 환율,미국채 10년,WTI유,VIX 지수
2026-08-10,2495,798,5290,16450,1350.5,4.12,78.5,15.2
2026-08-12,2490,795,5280,16400,1352.0,4.15,79.0,15.8
2026-08-15,2540,815,5380,16800,1345.0,4.08,77.2,14.5
2026-08-20,2580,835,5450,17150,1338.5,4.02,75.6,13.9
2026-08-28,2600,845,5500,17300,1332.0,3.98,74.8,13.2`;

            const rows = sampleCsv.trim().split(/\r?\n/);
            globalHeaders = rows[0].split(',').map(h => h.trim());
            globalRawRows = rows.slice(1);

            renderAllChips();
            renderAllCharts();
        }

        function renderAllChips() {
            Object.keys(chartStates).forEach(canvasId => {
                const containerId = 'chips-' + canvasId.replace('chart', '').toLowerCase();
                const container = document.getElementById(containerId);
                if (!container) return;
                container.innerHTML = '';

                Object.keys(chartStates[canvasId]).forEach(seriesName => {
                    const isActive = chartStates[canvasId][seriesName];
                    const color = chartColors[seriesName] || '#64748b';

                    const btn = document.createElement('button');
                    btn.innerText = seriesName;
                    btn.className = `text-[10px] px-2 py-0.5 rounded-md font-bold transition shadow-sm ${
                        isActive ? 'text-white shadow' : 'bg-slate-100 text-slate-400 line-through'
                    }`;
                    btn.style.backgroundColor = isActive ? color : '#e2e8f0';
                    
                    btn.onclick = () => {
                        chartStates[canvasId][seriesName] = !chartStates[canvasId][seriesName];
                        renderAllChips();
                        renderAllCharts();
                    };

                    container.appendChild(btn);
                });
            });
        }

        function createChart(canvasId, series1, series2) {
            if (globalRawRows.length === 0) return;
            const labels = globalRawRows.map(row => row.split(',')[0]);

            const idx1 = globalHeaders.indexOf(series1);
            const idx2 = globalHeaders.indexOf(series2);

            const data1 = globalRawRows.map(row => parseFloat(row.split(',')[idx1]) || 0);
            const data2 = globalRawRows.map(row => parseFloat(row.split(',')[idx2]) || 0);

            const canvasEl = document.getElementById(canvasId);
            if (!canvasEl) return;
            const ctx = canvasEl.getContext('2d');
            
            if (chartInstances[canvasId]) chartInstances[canvasId].destroy();

            chartInstances[canvasId] = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        { label: series1, data: data1, borderColor: chartColors[series1], borderWidth: 2, pointRadius: 2, tension: 0.15, hidden: !chartStates[canvasId][series1] },
                        { label: series2, data: data2, borderColor: chartColors[series2], borderWidth: 2, pointRadius: 2, tension: 0.15, hidden: !chartStates[canvasId][series2] }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false, // 픽셀 고정 높이 안에서 완벽 정렬
                    scales: {
                        x: { grid: { display: false }, ticks: { font: { size: 9 } } },
                        y: { grid: { color: '#f1f5f9' }, ticks: { font: { size: 9 } } }
                    },
                    plugins: { legend: { display: false } }
                }
            });
        }

        function renderAllCharts() {
            createChart('chartDomestic', '코스피', '코스닥');
            createChart('chartGlobal', 'S&P 500', '나스닥 종합');
            createChart('chartMacro', '원/달러 환율', '미국채 10년');
            createChart('chartCommodity', 'WTI유', 'VIX 지수');
        }

        document.addEventListener('DOMContentLoaded', loadData);
