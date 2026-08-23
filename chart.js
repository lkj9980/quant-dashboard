
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
