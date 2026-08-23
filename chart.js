let globalRawRows = [];
let globalHeaders = [];
let chartInstance = null;
let currentLimit = 20;
let selectedSeriesIndex = 1; // 기본 첫 번째 지수 선택

function logDebug(msg) {
    const box = document.getElementById('debug-view');
    if (box) box.innerText += "\n" + msg;
    console.log("[DEBUG] " + msg);
}

function toggleDebug() {
    const box = document.getElementById('debug-view');
    if (box) box.classList.toggle('hidden');
}

function setPeriod(limit) {
    currentLimit = limit;
    ['20', '60', 'all'].forEach(id => {
        const btn = document.getElementById('btn-' + id);
        if (btn) btn.className = "text-xs px-3 py-1.5 rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 font-semibold transition";
    });
    const activeId = limit === 20 ? 'btn-20' : (limit === 60 ? 'btn-60' : 'btn-all');
    const activeBtn = document.getElementById(activeId);
    if (activeBtn) activeBtn.className = "text-xs px-3 py-1.5 rounded-lg bg-blue-600 text-white font-bold transition shadow-sm";

    renderChart();
}

function selectSeries(index) {
    selectedSeriesIndex = index;
    updateChipsUI();
    renderChart();
}

function updateChipsUI() {
    const container = document.getElementById('series-chips');
    if (!container) return;
    container.innerHTML = '';

    for (let i = 1; i < globalHeaders.length; i++) {
        const isSelected = i === selectedSeriesIndex;
        const btn = document.createElement('button');
        btn.innerText = globalHeaders[i];
        btn.className = `text-xs px-3 py-1.5 rounded-full font-bold transition shadow-sm ${
            isSelected ? 'bg-blue-600 text-white shadow' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
        }`;
        btn.onclick = () => selectSeries(i);
        container.appendChild(btn);
    }
}

async function loadData() {
    try {
        logDebug("데이터 로딩 시작...");
        const sampleCsv = `Date,코스피,코스닥,S&P500,나스닥 종합,미국 국채 10년,USD/KRW 환율
2026-08-10,2500,800,5300,16500,4.25,1330
2026-08-11,2510,805,5320,16550,4.28,1332
2026-08-12,2490,795,5280,16400,4.30,1335
2026-08-13,2530,810,5350,16700,4.22,1328
2026-08-14,2540,815,5380,16800,4.20,1325
2026-08-17,2520,808,5340,16650,4.24,1330
2026-08-18,2550,820,5400,16900,4.18,1322
2026-08-19,2560,825,5420,17000,4.15,1320
2026-08-20,2580,835,5450,17150,4.12,1315
2026-08-23,2600,845,5500,17300,4.10,1310`;

        let data = "";
        try {
            const response = await fetch('../history/quant_log.csv');
            if (response.ok) {
                data = await response.text();
            } else {
                throw new Error();
            }
        } catch (err) {
            data = sampleCsv;
        }

        const rows = data.trim().split(/\r?\n/);
        if (rows.length < 2) return;

        globalHeaders = rows[0].split(',').map(h => h.trim());
        globalRawRows = rows.slice(1);

        updateChipsUI();
        renderChart();

        // 렌더링 성공 시 디버그 박스 자동 숨김
        const debugBox = document.getElementById('debug-view');
        if (debugBox) debugBox.classList.add('hidden');

    } catch (e) {
        logDebug("에러 발생: " + e.message);
    }
}

function renderChart() {
    if (globalRawRows.length === 0) return;
    const sliceRows = currentLimit === 999 ? globalRawRows : globalRawRows.slice(-currentLimit);
    
    const labels = [];
    const values = [];
    const seriesName = globalHeaders[selectedSeriesIndex];

    sliceRows.forEach(row => {
        const cols = row.split(',').map(c => c.trim());
        if (cols.length < globalHeaders.length) return;
        labels.push(cols[0]);
        values.push(parseFloat(cols[selectedSeriesIndex]) || 0);
    });

    document.getElementById('chart-title').innerText = `📈 [${seriesName}] 실시간 트렌드 분석`;

    const ctx = document.getElementById('quantChart').getContext('2d');
    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: seriesName,
                data: values,
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.08)',
                borderWidth: 2.5,
                pointRadius: 3,
                fill: true,
                tension: 0.15
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { display: false }, ticks: { font: { size: 10 }, maxTicksLimit: 6 } },
                y: { grid: { color: '#f1f5f9' }, ticks: { font: { size: 10 } } }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', loadData);
