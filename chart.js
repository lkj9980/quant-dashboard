// chart.js
function logDebug(msg) {
    const box = document.getElementById('debug-view');
    if (box) box.innerText += "\n" + msg;
    console.log(msg);            
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
