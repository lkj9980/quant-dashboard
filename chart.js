let globalRawRows = [];
let globalHeaders = [];
let chartInstance = null;
let currentLimit = 20;

// 각 차트별 지표 활성화 상태 관리 (기본 모두 켜짐)
let chartStates = {
    chartDomestic: { '코스피': true, '코스닥': true },
    chartGlobal: { 'S&P 500': true, '나스닥 종합': true },
    chartMacro: { 'USD/KRW 환율': true, '미국 국채 10년': true },
    chartCommodity: { 'WTI 유가': true, 'VIX 변동성': true }
};

const chartColors = {
    '코스피': '#2563eb', '코스닥': '#db2777',
    'S&P 500': '#4f46e5', '나스닥 종합': '#0284c7',
    'USD/KRW 환율': '#059669', '미국 국채 10년': '#d97706',
    'WTI 유가': '#ea580c', 'VIX 변동성': '#7c3aed'
};

function logDebug(msg) {
    const box = document.getElementById('debug-view');
    if (!box) {
      console.log("[DEBUG (DOM Missing)] " + msg);
      return;
    }
    box.innerText += "\n" + msg;
    console.log("[DEBUG] " + msg);
}

function toggleDebug() {
    const box = document.getElementById('debug-view');
    if (box) box.classList.toggle('hidden');
}

// 제어 패널(칩+기간설정)과 차트를 한 세트로 껐다 켰다 하는 함수
function toggleChartSection() {
    const section = document.getElementById('chart-toggle-section');
    if (section) {
section.classList.toggle('hidden');
    }
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

function selectSeries(index) {
    selectedSeriesIndex = index;
    updateChipsUI();
    renderAllCharts();
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
const sampleCsv = `Date,코스피,코스닥,코스피 200,S&P 500,나스닥 종합,나스닥 100,S&P 500 선물,나스닥 100 선물,러셀 2000 선물,미국 국채 10년,미국 국채 30년,USD/KRW 환율,WTI 유가,국제 금,구리 선물,VIX 변동성
2026-08-10 09:00,2495,798,328,5290,16450,18450,5300,18500,2090,4.25,4.35,1330,78,2400,4.1,15.2
2026-08-10 15:55,2500,800,330,5300,16500,18500,5310,18550,2100,4.25,4.35,1330,78,2400,4.1,15.2
2026-08-11 15:55,2510,805,332,5320,16550,18600,5330,18620,2110,4.28,4.38,1332,77,2410,4.12,15.0
2026-08-12 15:55,2490,795,328,5280,16400,18400,5290,18420,2080,4.30,4.40,1335,79,2390,4.08,15.8
2026-08-13 15:55,2530,810,334,5350,16700,18750,5360,18780,2125,4.22,4.32,1328,76,2420,4.15,14.5
2026-08-14 15:55,2540,815,335,5380,16800,18850,5390,18880,2140,4.20,4.30,1325,75,2430,4.18,14.2
2026-08-17 15:55,2520,808,332,5340,16650,18700,5350,18720,2115,4.24,4.34,1330,77,2415,4.13,14.9
2026-08-18 15:55,2550,820,337,5400,16900,18950,5410,18980,2150,4.18,4.28,1322,74,2440,4.20,13.8
2026-08-19 15:55,2560,825,338,5420,17000,19050,5430,19080,2165,4.15,4.25,1320,73,2450,4.22,13.5
2026-08-20 15:55,2580,835,341,5450,17150,19200,5460,19230,2180,4.12,4.22,1315,72,2465,4.25,13.0
2026-08-28 07:00,2600,845,344,5500,17300,19400,5510,19430,2200,4.10,4.20,1310,71,2480,4.28,12.5`;
let data = "";
try {
    const response = await fetch('../history/quant_log.csv');
    if (response.ok) {
data = await response.text();
logDebug("서버 CSV 로드 성공");
    } else {
throw new Error("파일 없음 또는 경로 에러");
    }
} catch (err) {
    logDebug("외부 파일 로드 실패 (CORS 또는 경로 문제), 안전한 샘플 데이터 사용");
    data = sampleCsv;
}

const rows = data.trim().split(/\r?\n/);
if (rows.length < 2) return;

globalHeaders = rows[0].split(',').map(h => h.trim());
const rawRows = rows.slice(1);    

// ★ 핵심: 날짜별로 그룹화하여 동일 날짜의 '마지막(최신) 행'만 남기는 전처리 로직
const dailyMap = {};
rawRows.forEach(row => {
    const cols = row.split(',').map(c => c.trim());
    if (cols.length < globalHeaders.length) return;
    
    // 날짜 문자열에서 시간(HH:MM)이 포함되어 있다면 앞의 날짜 부분(YYYY-MM-DD)만 추출
    // 예: "2026-08-20 15:30" -> "2026-08-20"
    const fullDateStr = cols[0];
    const dateKey = fullDateStr.split(' ')[0]; 

    // 같은 날짜 데이터가 여러 개 들어오면 나중에 들어온(마지막) 값으로 계속 덮어씀
    dailyMap[dateKey] = cols;
});

// 맵에 정리된 데이터를 다시 배열로 변환
globalRawRows = Object.keys(dailyMap).sort().map(dateKey => {
    const cols = dailyMap[dateKey];
    // X축 레이블을 깔끔하게 날짜만 보이도록 첫 번째 열을 날짜 전용 키로 설정
    cols[0] = dateKey;
    return cols.join(',');
});

logDebug(`일자별 압축 완료: 총 ${Object.keys(dailyMap).length}일치 데이터 확보`);

renderAllChips();
renderAllCharts();

const debugBox = document.getElementById('debug-view');
if (debugBox) debugBox.classList.add('hidden');

    } catch (e) {
logDebug("에러 발생: " + e.message);
    }
}

// 토글 칩 UI 생성 함수
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

// 보조축 지원 차트 생성 함수 (칩 상태 연동)
function createDualAxisChart(canvasId, series1, series2) {
    if (globalRawRows.length === 0) return;
  
    const sliceRows = currentLimit === 999 ? globalRawRows : globalRawRows.slice(-currentLimit);
    const labels = [];

    sliceRows.forEach(row => {
      const cols = row.split(',').map(c => c.trim());

      if (cols.length < globalHeaders.length) return;
      labels.push(cols[0]);
    });

    const idx1 = globalHeaders.indexOf(series1);
    const idx2 = globalHeaders.indexOf(series2);
  
    const data1 = [];
    const data2 = [];

    sliceRows.forEach(row => {
      const cols = row.split(',').map(c => c.trim());
      data1.push(idx1 !== -1 ? parseFloat(cols[idx1]) || 0 : 0);
      data2.push(idx2 !== -1 ? parseFloat(cols[idx2]) || 0 : 0);      
    });

    const state1 = chartStates[canvasId][series1];
    const state2 = chartStates[canvasId][series2];

    const canvasEl = document.getElementById(canvasId);

    if (!canvasEl) return;
    const ctx = canvasEl.getContext('2d');
    
    if (chartInstances[canvasId]) {
      chartInstances[canvasId].destroy();
    }

    chartInstances[canvasId] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: series1,
            data: data1,
            borderColor: chartColors[series1],
            backgroundColor: 'transparent',
            borderWidth: 2,
            pointRadius: 2,
            tension: 0.15,
            hidden: !state1,
            yAxisID: 'y'
          },
          {
            label: series2,
            data: data2,
            orderColor: chartColors[series2],
            backgroundColor: 'transparent',
            borderWidth: 2,
            pointRadius: 2,
            tension: 0.15,
            hidden: !state2,
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { 
            grid: { display: false }, 
            ticks: { font: { size: 9 }, maxTicksLimit: 5 } 
          },
          y: {
            type: 'linear',
            display: true,
            position: 'left',
            grid: { color: '#f1f5f9' },
            ticks: { font: { size: 9 }, color: chartColors[series1] }
          },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            grid: { drawOnChartArea: false },
            ticks: { font: { size: 9 }, color: chartColors[series2] }
          }
        },
        plugins: {
          legend: { display: false } // 범례 숨김 (상단 칩으로 대체)
          }
      }
    });
}

function renderAllCharts() {
    createDualAxisChart('chartDomestic', '코스피', '코스닥');
    createDualAxisChart('chartGlobal', 'S&P 500', '나스닥 종합');
    createDualAxisChart('chartMacro', 'USD/KRW 환율', '미국 국채 10년');
    createDualAxisChart('chartCommodity', 'WTI 유가', 'VIX 변동성');
}

document.addEventListener('DOMContentLoaded', loadData);
