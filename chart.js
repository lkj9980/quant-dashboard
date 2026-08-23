
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
            console.log("[DEBUG] " + msg);
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

        async function loadCharts() {
            try {
                logDebug("1. 데이터 로딩 시작...");
                
                const sampleCsv = `Date,코스피,코스닥,S&P500,나스닥
2026-06-01,2350,750,5100,15800
2026-06-10,2380,760,5150,15950
2026-06-20,2400,770,5180,16100
2026-07-01,2420,775,5200,16150
2026-07-10,2450,780,5230,16200
2026-07-20,2460,785,5240,16250
2026-08-01,2480,790,5250,16300
2026-08-04,2495,795,5280,16400
2026-08-05,2470,785,5210,16200
2026-08-06,2500,800,5300,16500
2026-08-07,2510,805,5320,16550
2026-08-08,2490,795,5280,16400
2026-08-11,2530,810,5350,16700
2026-08-12,2540,815,5380,16800
2026-08-13,2520,808,5340,16650
2026-08-14,2550,820,5400,16900
2026-08-18,2560,825,5420,17000
2026-08-19,2580,835,5450,17150
2026-08-20,2570,830,5430,17100
2026-08-21,2600,845,5500,17300`;

                let data = "";
                try {
                    const response = await fetch('../history/quant_log.csv');
                    if (response.ok) {
                        data = await response.text();
                        logDebug("📁 외부 CSV 파일 로드 성공");
                    } else {
                        throw new Error("파일 없음");
                    }
                } catch (err) {
                    logDebug("⚠️ 외부 파일 로드 실패, 내장 샘플 데이터 사용");
                    data = sampleCsv;
                }

                const rows = data.trim().split(/\r?\n/);
                if (rows.length < 2) return;

                globalHeaders = rows[0].split(',').map(h => h.trim());
                globalRows = rows.slice(1);
                
                logDebug("2. 헤더 감지: " + globalHeaders.slice(1).join(', '));
                
                // 초기 전체 보기 렌더링
                renderChart(globalRows, globalHeaders, 'all');

            } catch (e) {
                logDebug("💥 차트 생성 중 에러: " + e.message);
            }
        }

        document.addEventListener('DOMContentLoaded', loadCharts);
