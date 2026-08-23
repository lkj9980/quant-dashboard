// chart.js
let globalRows = [];
let globalHeaders = [];
let unifiedChartInstance = null;
let currentLimit = 'all';

// 현재 활성화된 단일 시리즈 이름 저장 (기본값: 코스피)
let activeSeriesName = '코스피';

const seriesColors = {
    '코스피': '#2563eb',
    'S&P500': '#7c3aed',
    '코스닥': '#16a34a',
    '나스닥': '#dc2626'
};

function logDebug(msg) {
    const box = document.getElementById('debug-view');
    if (box) box.innerText += "\n" + msg;
    console.log(msg);    
}

function toggleDebug() {
    const box = document.getElementById('debug-view');
    if (box) box.classList.toggle('hidden');
}

// 시리즈 단일 선택 핸들러 (멀티 셀렉 방지)
function selectSeries(seriesName, btnEl) {
    activeSeriesName = seriesName;
    
    // 모든 칩의 스타일을 비활성화 상태로 초기화
    const chips = document.querySelectorAll('#series-chips .chip-btn');
    chips.forEach(chip => {
        chip.style.backgroundColor = '#e2e8f0';
        chip.style.color = '#94a3b8';
        chip.classList.add('opacity-40');
    });

    // 클릭된 칩만 활성화 상태로 설정
    btnEl.style.backgroundColor = seriesColors[seriesName] || '#2563eb';
    btnEl.style.color = '#ffffff';
    btnEl.classList.remove('opacity-40');

    renderChart(globalRows, globalHeaders, currentLimit);
    logDebug(`단일 선택 칩 변경: [${seriesName}]`);
}

function changePeriod(limit) {
    currentLimit = limit;
    
    // 기간 버튼 스타일 업데이트
    ['20', '60', 'all'].forEach(id => {
        const btn = document.getElementById('btn-' + id);
        if (btn) {
            if ((id === 'all' && limit === 'all') || (Number(id) === limit)) {
                btn.className = "text-xs px-3 py-1.5 rounded-lg font-bold bg-blue-600 text-white transition";
            } else {
                btn.className = "text-xs px-3 py-1.5 rounded-lg font-bold bg-slate-200 text-slate-700 hover:bg-slate-300 transition";
            }
        }
    });

    renderChart(globalRows, globalHeaders, currentLimit);
}

function renderChart(rows, headers, limit) {
    const labels = [];
    const seriesData = {};
    for (let i = 1; i < headers.length; i++) {
        seriesData[headers[i]] = [];
    }

    const targetRows = limit === 'all' ? rows : rows.slice(-limit);

    targetRows.forEach(row => {
        const cols = row.split(',').map(c => c.trim());
        if (cols.length < headers.length) return;
        labels.push(cols[0]);
        for (let i = 1; i < headers.length; i++) {
            seriesData[headers[i]].push(parseFloat(cols[i]) || 0);
        }
    });

    // 단일 선택된 시리즈만 데이터셋에 포함
    const datasets = [];
    if (activeSeriesName && seriesData[activeSeriesName]) {
        datasets.push({
            label: activeSeriesName,
            data: seriesData[activeSeriesName],
            borderColor: seriesColors[activeSeriesName] || '#3b82f6',
            backgroundColor: seriesColors[activeSeriesName] || '#3b82f6',
            borderWidth: 2,
            pointRadius: 2,
            tension: 0.2,
            fill: true,
            backgroundColor: (context) => {
                const ctx = context.chart.ctx;
                const gradient = ctx.createLinearGradient(0, 0, 0, 300);
                gradient.addColorStop(0, (seriesColors[activeSeriesName] || '#3b82f6') + '33');
                gradient.addColorStop(1, (seriesColors[activeSeriesName] || '#3b82f6') + '00');
                return gradient;
            }
        });
    }

    const ctx = document.getElementById('quantChart').getContext('2d');
    if (unifiedChartInstance) unifiedChartInstance.destroy();

    unifiedChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 9 }, maxTicksLimit: 6 }
                },
                y: {
                    grid: { color: '#f1f5f9' },
                    ticks: { font: { size: 10 } }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { font: { size: 10 }, boxWidth: 12, usePointStyle: true }
                }
            }
        }
    });

    logDebug(`✨ 단일 선택 차트 렌더링 완료 (선택 시리즈: ${activeSeriesName}, 데이터 포인트: ${labels.length}개)`);
}
async function loadChart() {
    try {
        // 저장된 CSV 파일 경로 (상대 경로 위치에 맞게 조정 필요, 예: 'history/quant_log.csv' 등)
        logDebug("1. loadChart 함수 실행됨");
        const response = await fetch('../history/quant_log.csv');
        logDebug("2. fetch 요청 완료, 상태코드: " + response.status);
        if (!response.ok) {
            logDebug("❌ 에러: CSV 파일을 읽지 못했습니다.");
            console.error("🚨 [차트 에러] CSV 파일을 불러오지 못했습니다. 상태 코드:", response.status);
            return;
        }
        
        const data = await response.text();
        logDebug("3. CSV 데이터 로드 성공 (총 글자수: " + data.length + ")");
        const rows = data.trim().split(/\r?\n/);
        logDebug("4. 행(Row) 개수: " + rows.length);
        if (rows.length < 2) {
            logDebug("⚠️ 경고: 데이터 행이 2개 미만입니다.");
            console.warn("⚠️ [차트 경고] CSV 데이터가 부족합니다.");
            return;
        }
        
        const headers = rows[0].split(',');
        logDebug("5. 헤더(컬럼명) 인식 완료: " + headers.join(', '));
        const labels = [];
        const datasetsMap = {};
        
        for (let i = 1; i < headers.length; i++) {
            datasetsMap[headers[i]] = [];
        }
        
        // 최근 20개 데이터만 슬라이싱해서 가독성 유지
        const recentRows = rows.slice(-20);
        recentRows.forEach(row => {
            const cols = row.split(',');
            labels.push(cols[0]); // Date (시간)
            
            for (let i = 1; i < headers.length; i++) {
                const val = parseFloat(cols[i]);
                datasetsMap[headers[i]].push(isNaN(val) ? null : val);
            }
        });
        
        const colors = ['#2563eb', '#dc2626', '#16a34a', '#ca8a04', '#9333ea'];
        let colorIndex = 0;
        
        const chartDatasets = Object.keys(datasetsMap).map(key => {
            const color = colors[colorIndex % colors.length];
            colorIndex++;
            return {
                label: key,
                data: datasetsMap[key],
                borderColor: color,
                backgroundColor: color,
                borderWidth: 2,
                pointRadius: 2,
                tension: 0.1
            };
        });
        
        const ctx = document.getElementById('quantChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: { labels: labels, datasets: chartDatasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { grid: { color: '#f1f5f9' }, ticks: { font: { size: 10 } } },
                    x: { grid: { display: false }, ticks: { font: { size: 9 }, maxTicksLimit: 5 } }
                },
                plugins: {
                    legend: { position: 'bottom', labels: { font: { size: 10 }, boxWidth: 10 } }
                }
            }
        });
        if (!ctx) {
            logDebug("❌ 에러: 'quantChart' 캔버스 요소를 찾을 수 없습니다!");
            return;
        }
        
        globalHeaders = rows[0].split(',').map(h => h.trim());
        globalRows = rows.slice(1);
        logDebug("2. 헤더 감지: " + globalHeaders.slice(1).join(', '));
                
        // 초기 전체 보기 렌더링
        renderChart(globalRows, globalHeaders, 'all');
        logDebug("✨ 6. 차트 렌더링 코드 도달 완료!");
        
        // 차트 렌더링이 성공적으로 끝난 직후에 디버그 박스를 자동으로 숨김
        const debugBox = document.getElementById('debug-view');
        if (debugBox) {
            debugBox.classList.add('hidden'); // 또는 debugBox.style.display = 'none';
        }

    } catch (e) {
        logDebug("💥 예외 발생 (Catch): " + e.message);
        console.error("차트 로딩 에러:", e);
    }
}

document.addEventListener('DOMContentLoaded', loadChart);
