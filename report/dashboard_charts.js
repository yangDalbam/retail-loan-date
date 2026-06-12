// dashboard_charts.js
document.addEventListener('DOMContentLoaded', () => {
    // 공통 설정
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Outfit', 'Noto Sans KR', sans-serif";
    Chart.defaults.layout = { padding: { top: 20, bottom: 30, left: 20, right: 20 } };
    if (Chart.defaults.plugins.legend) {
        Chart.defaults.plugins.legend.labels.padding = 20;
    }
    const colors = [
        '#38bdf8', '#818cf8', '#34d399', '#fbbf24', '#f87171', '#a78bfa'
    ];

    const { labels, companies, data } = dashboardData;

    // Helper: 특정 시점의 데이터 가져오기
    const getDataForMonth = (item, monthIndex) => {
        return companies.map(company => data[item][company][monthIndex]);
    };

    // Helper: select 박스 옵션 채우기
    const populateSelect = (selectId, defaultIndex) => {
        const select = document.getElementById(selectId);
        if (!select) return;
        labels.forEach((label, idx) => {
            const option = document.createElement('option');
            option.value = idx;
            option.text = label;
            if (idx === defaultIndex) option.selected = true;
            select.appendChild(option);
        });
        return select;
    };

    // 포맷터 헬퍼
    const formatMoney = (val) => (val / 100000000).toLocaleString(undefined, {maximumFractionDigits: 1}) + '억';
    const formatPercent = (val) => (val * 100).toFixed(2) + '%';
    
    // 축 설정
    const moneyYAxis = { ticks: { callback: formatMoney } };
    const percentYAxis = { ticks: { callback: formatPercent } };

    // 툴팁 설정
    const moneyTooltip = {
        callbacks: {
            label: (ctx) => `${ctx.dataset.label || ctx.label}: ${formatMoney(ctx.raw || ctx.parsed.y)}원`
        }
    };
    const percentTooltip = {
        callbacks: {
            label: (ctx) => `${ctx.dataset.label || ctx.label}: ${formatPercent(ctx.raw || ctx.parsed.y)}`
        }
    };

    // 최신 월(가장 마지막 인덱스)
    const latestIdx = labels.length - 1;

    // --- Chart 1: 회사별 대출잔액 변화 추이 (Line) ---
    const ctx1 = document.getElementById('chart1')?.getContext('2d');
    if (ctx1) {
        new Chart(ctx1, {
            type: 'line',
            data: {
                labels: labels,
                datasets: companies.map((company, i) => ({
                    label: company,
                    data: data['개인신용 대출잔액'][company],
                    borderColor: colors[i % colors.length],
                    backgroundColor: colors[i % colors.length] + '33',
                    tension: 0.3,
                    fill: false
                }))
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: moneyYAxis },
                plugins: { tooltip: moneyTooltip }
            }
        });
    }

    // --- Chart 2: 대출잔액 비중 (Doughnut) ---
    const ctx2 = document.getElementById('chart2')?.getContext('2d');
    if (ctx2) {
        const select2 = populateSelect('periodSelect2', latestIdx);
        const chart2 = new Chart(ctx2, {
            type: 'doughnut',
            data: {
                labels: companies,
                datasets: [{
                    data: getDataForMonth('개인신용 대출잔액', latestIdx),
                    backgroundColor: colors,
                    borderWidth: 1,
                    borderColor: '#1e293b'
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { tooltip: moneyTooltip }
            }
        });

        select2.addEventListener('change', (e) => {
            chart2.data.datasets[0].data = getDataForMonth('개인신용 대출잔액', e.target.value);
            chart2.update();
        });
    }

    // --- Chart 4: 회사별 연체율 변동 추이 (Line) ---
    const ctx4 = document.getElementById('chart4')?.getContext('2d');
    if (ctx4) {
        new Chart(ctx4, {
            type: 'line',
            data: {
                labels: labels,
                datasets: companies.map((company, i) => ({
                    label: company,
                    data: data['연체율'][company],
                    borderColor: colors[i % colors.length],
                    tension: 0.3,
                    fill: false
                }))
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: percentYAxis },
                plugins: { tooltip: percentTooltip }
            }
        });
    }

    // --- Chart 5: 6개사 평균 연체율 추이 (Line) ---
    const ctx5 = document.getElementById('chart5')?.getContext('2d');
    if (ctx5) {
        const avgDelayRates = [0.0589, 0.0494, 0.0377, 0.0315, 0.0206, 0.0171, 0.0145, 0.0151, 0.0126, 0.0128, 0.0096];


        new Chart(ctx5, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '6개사 가중평균 연체율',
                    data: avgDelayRates,
                    borderColor: '#f43f5e',
                    backgroundColor: 'rgba(244, 63, 94, 0.2)',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: percentYAxis },
                plugins: { tooltip: percentTooltip }
            }
        });
    }

    // --- Chart 3: 회사별 연체금액 비교 (Bar) ---
    const ctx3 = document.getElementById('chart3')?.getContext('2d');
    if (ctx3) {
        const select3 = populateSelect('periodSelect3', latestIdx);
        const chart3 = new Chart(ctx3, {
            type: 'bar',
            data: {
                labels: companies,
                datasets: [{
                    label: '연체금액',
                    data: getDataForMonth('연체금액', latestIdx),
                    backgroundColor: colors,
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: moneyYAxis },
                plugins: { tooltip: moneyTooltip }
            }
        });

        select3.addEventListener('change', (e) => {
            chart3.data.datasets[0].data = getDataForMonth('연체금액', e.target.value);
            chart3.update();
        });
    }

    // --- Chart 8: 대출잔액과 연체금액 산점도 (Scatter) ---
    const ctx8 = document.getElementById('chart8')?.getContext('2d');
    if (ctx8) {
        const select8 = populateSelect('periodSelect8', latestIdx);
        
        const getScatterData = (idx) => {
            return companies.map((company, i) => ({
                label: company,
                data: [{
                    x: data['개인신용 대출잔액'][company][idx],
                    y: data['연체금액'][company][idx]
                }],
                backgroundColor: colors[i % colors.length],
                pointRadius: 8,
                pointHoverRadius: 10
            }));
        };

        const chart8 = new Chart(ctx8, {
            type: 'scatter',
            data: { datasets: getScatterData(latestIdx) },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: {
                    x: { title: { display: true, text: '대출잔액 (억원)' }, ticks: { callback: formatMoney } },
                    y: { title: { display: true, text: '연체금액 (억원)' }, ticks: { callback: formatMoney } }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `${ctx.dataset.label}: 대출 ${formatMoney(ctx.parsed.x)}원 / 연체 ${formatMoney(ctx.parsed.y)}원`
                        }
                    }
                }
            }
        });

        select8.addEventListener('change', (e) => {
            chart8.data.datasets = getScatterData(e.target.value);
            chart8.update();
        });
    }

    // Helper to calculate min, avg, max
    const getStats = (item) => {
        return companies.map(c => {
            const arr = data[item][c];
            const min = Math.min(...arr);
            const max = Math.max(...arr);
            const avg = arr.reduce((a, b) => a + b, 0) / arr.length;
            return { min, avg, max };
        });
    };

    // --- Chart 9: 회사별 연체금액 요약 (Bar) ---
    const ctx9 = document.getElementById('chart9')?.getContext('2d');
    if (ctx9) {
        const stats = getStats('연체금액');
        new Chart(ctx9, {
            type: 'bar',
            data: {
                labels: companies,
                datasets: [
                    { label: '최소', data: stats.map(s => s.min), backgroundColor: '#34d399' },
                    { label: '평균', data: stats.map(s => s.avg), backgroundColor: '#38bdf8' },
                    { label: '최대', data: stats.map(s => s.max), backgroundColor: '#f87171' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: moneyYAxis },
                plugins: { tooltip: moneyTooltip }
            }
        });
    }

    // --- Chart 10: 회사별 연체율 요약 (Bar) ---
    const ctx10 = document.getElementById('chart10')?.getContext('2d');
    if (ctx10) {
        const stats = getStats('연체율');
        new Chart(ctx10, {
            type: 'bar',
            data: {
                labels: companies,
                datasets: [
                    { label: '최소', data: stats.map(s => s.min), backgroundColor: '#34d399' },
                    { label: '평균', data: stats.map(s => s.avg), backgroundColor: '#8b5cf6' },
                    { label: '최대', data: stats.map(s => s.max), backgroundColor: '#f87171' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: percentYAxis },
                plugins: { tooltip: percentTooltip }
            }
        });
    }

    // --- Chart 6: 매각을 통한 연체율 하락 효과 (Bar) ---
    const ctx6 = document.getElementById('chart6')?.getContext('2d');
    if (ctx6) {
        const select6 = populateSelect('periodSelect6', latestIdx);
        
        const getReductionData = (idx) => {
            return companies.map(company => {
                const balance = data['개인신용 대출잔액'][company][idx];
                const sellAmt = data['매각 금액'][company][idx];
                return balance > 0 ? (sellAmt / balance) * 100 : 0;
            });
        };

        const chart6 = new Chart(ctx6, {
            type: 'bar',
            data: {
                labels: companies,
                datasets: [{
                    label: '연체율 하락 효과 (%p)',
                    data: getReductionData(latestIdx),
                    backgroundColor: '#10b981'
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: { ticks: { callback: (val) => val.toFixed(2) + '%p' } } },
                plugins: {
                    tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: ${ctx.raw.toFixed(2)}%p` } }
                }
            }
        });

        select6.addEventListener('change', (e) => {
            chart6.data.datasets[0].data = getReductionData(e.target.value);
            chart6.update();
        });
    }

    // --- Chart 7: 월별 회사별 매각 금액 추이 (Stacked Bar) ---
    const ctx7 = document.getElementById('chart7')?.getContext('2d');
    if (ctx7) {
        new Chart(ctx7, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: companies.map((company, i) => ({
                    label: company,
                    data: data['매각 금액'][company],
                    backgroundColor: colors[i % colors.length]
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { stacked: true },
                    y: { stacked: true, ...moneyYAxis }
                },
                plugins: { tooltip: moneyTooltip }
            }
        });
    }
});
