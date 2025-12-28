# Dividend System Blueprint - Frontend Step 4
# 배당 UI JavaScript 로직 (실제 전체 코드)

## 개요
이 문서는 배당 페이지의 완전한 JavaScript 로직입니다.

---

## 1. JavaScript 코드

`templates/dividend.html`의 `<script>` 태그 안에 추가:

```javascript
// ============================================
// 상태 관리
// ============================================
let selectedTheme = 'dividend_growth'; // Default theme
let basket = [];


// ============================================
// 초기화
// ============================================
document.addEventListener('DOMContentLoaded', async () => {
    await fetchThemes();
    triggerOptimization();
});

document.getElementById('targetInput').addEventListener('change', triggerOptimization);


// ============================================
// 테마 목록 로드
// ============================================
async function fetchThemes() {
    try {
        const res = await fetch('/api/dividend/themes');
        const data = await res.json();

        // Update Meta
        if (data.meta && data.meta.last_updated) {
            document.getElementById('lastUpdated').textContent = data.meta.last_updated;
        }

        const container = document.getElementById('themeCarousel');
        container.innerHTML = '';

        data.themes.forEach((theme, idx) => {
            const isActive = theme.id === selectedTheme;
            const el = document.createElement('div');
            el.className = `flex-shrink-0 w-64 p-5 rounded-2xl cursor-pointer transition border ${isActive ? 'bg-white text-black border-white' : 'glass-card text-gray-300 border-white/5 hover:border-white/20'}`;
            el.onclick = () => selectTheme(theme.id);

            // Icon logic
            let icon = 'fa-chart-line';
            if (theme.id.includes('silver')) icon = 'fa-shield-alt';
            if (theme.id.includes('income')) icon = 'fa-coins';
            if (theme.id.includes('covered')) icon = 'fa-layer-group';
            if (theme.id.includes('reit')) icon = 'fa-building';
            if (theme.id.includes('quality')) icon = 'fa-gem';

            el.innerHTML = `
                <div class="flex items-start justify-between mb-3">
                    <i class="fas ${icon} text-lg ${isActive ? 'text-apple-blue' : 'text-gray-500'}"></i>
                    ${isActive ? '<i class="fas fa-check-circle text-apple-blue"></i>' : ''}
                </div>
                <h4 class="font-bold text-base mb-1 truncate">${theme.title}</h4>
                <p class="text-xs ${isActive ? 'text-gray-600' : 'text-gray-500'} leading-relaxed">${theme.subtitle}</p>
            `;
            container.appendChild(el);
        });

    } catch (e) {
        console.error("Theme fetch failed", e);
    }
}


// ============================================
// 테마 선택
// ============================================
function selectTheme(id) {
    selectedTheme = id;
    fetchThemes(); // Re-render to update active state
    triggerOptimization();
}


// ============================================
// 목표 금액 설정
// ============================================
function setGoal(amount) {
    document.getElementById('targetInput').value = amount;
    triggerOptimization();
}


// ============================================
// 포트폴리오 최적화 트리거
// ============================================
async function triggerOptimization() {
    const themeId = selectedTheme;
    const target = document.getElementById('targetInput').value || 1000000;
    const fx = document.getElementById('fxRate').value;
    const tax = document.getElementById('taxRate').value;

    document.getElementById('loadingOverlay').classList.remove('hidden');

    try {
        const res = await fetch('/api/dividend/all-tiers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                theme_id: themeId,
                target_monthly_krw: target,
                fx_rate: fx,
                tax_rate: tax
            })
        });
        const tiersData = await res.json();
        renderTierCards(tiersData);
    } catch (e) {
        console.error(e);
    } finally {
        document.getElementById('loadingOverlay').classList.add('hidden');
    }
}


// ============================================
// 티어 카드 렌더링
// ============================================
function renderTierCards(tiers) {
    const container = document.getElementById('tierGrid');
    container.innerHTML = '';

    const order = ['defensive', 'balanced', 'aggressive'];
    const config = {
        defensive: { color: 'emerald', label: 'Stable', icon: 'fa-shield-halved' },
        balanced: { color: 'blue', label: 'Balanced', icon: 'fa-scale-balanced' },
        aggressive: { color: 'orange', label: 'Aggressive', icon: 'fa-rocket' }
    };

    order.forEach(tierKey => {
        const data = tiers[tierKey];
        if (!data || data.error) return;

        const style = config[tierKey];
        
        // Badge class mapping
        let badgeClass;
        if (tierKey === 'defensive') badgeClass = "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
        if (tierKey === 'balanced') badgeClass = "bg-blue-500/10 text-blue-400 border border-blue-500/20";
        if (tierKey === 'aggressive') badgeClass = "bg-orange-500/10 text-orange-400 border border-orange-500/20";

        const yieldVal = data.portfolio_yield || data.yield || 'N/A';
        const monthlyFlow = data.expected_monthly_krw || 0;
        const requiredCap = data.required_capital_krw || 0;

        const card = document.createElement('div');
        card.className = "glass-card rounded-3xl p-6 relative group overflow-hidden flex flex-col h-[480px]";
        card.innerHTML = `
            <div class="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition">
                <i class="fas ${style.icon} text-9xl text-white"></i>
            </div>

            <!-- Header -->
            <div class="flex items-center gap-3 mb-4 z-10">
                <span class="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${badgeClass}">
                    ${tierKey}
                </span>
                <span class="text-[10px] text-gray-500 px-2 py-1 bg-white/5 rounded-full border border-white/5">
                    Risk: ${data.risk_label}
                </span>
            </div>

            <!-- Main Info -->
            <div class="mb-8 z-10">
                <h3 class="text-2xl font-bold text-white mb-2">${data.title.split('(')[0]}</h3>
                <p class="text-sm text-gray-400 line-clamp-2 min-h-[40px]">${data.one_liner}</p>
            </div>

            <!-- Metrics -->
            <div class="space-y-6 z-10 flex-grow">
                <!-- Primary metric -->
                <div>
                    <div class="text-[11px] text-gray-500 uppercase tracking-wide mb-1">Est. Monthly Income (Post-Tax)</div>
                    <div class="flex items-baseline gap-1">
                        <span class="text-3xl font-bold text-white tracking-tight">${Number(monthlyFlow).toLocaleString()}</span>
                        <span class="text-sm text-gray-400 font-medium">KRW</span>
                    </div>
                    <!-- Progress vs Goal -->
                    <div class="w-full bg-gray-800/50 h-1.5 rounded-full mt-3 overflow-hidden">
                        <div class="bg-${style.color}-500 h-full rounded-full transition-all" style="width: ${Math.min(100, (monthlyFlow / data.target_monthly_krw) * 100)}%;"></div>
                    </div>
                </div>

                <!-- Secondary Metrics Grid -->
                <div class="grid grid-cols-2 gap-4">
                    <div class="p-3 rounded-xl bg-black/20 border border-white/5">
                        <div class="text-[10px] text-gray-500 mb-1">Capital Required</div>
                        <div class="font-semibold text-white text-sm whitespace-nowrap">${formatCompactNumber(requiredCap)}</div>
                    </div>
                    <div class="p-3 rounded-xl bg-black/20 border border-white/5">
                        <div class="text-[10px] text-gray-500 mb-1">Dividend Yield</div>
                        <div class="font-semibold text-${style.color}-400 text-sm font-mono">${yieldVal}</div>
                    </div>
                </div>
            </div>

            <!-- Action -->
            <div class="mt-auto pt-6 border-t border-white/5 z-10">
                <button onclick='openDetail(${JSON.stringify(data).replace(/'/g, "&#39;")})' class="w-full py-3 rounded-xl bg-white/5 hover:bg-white/10 text-white text-sm font-semibold transition border border-white/10 flex items-center justify-center gap-2">
                    View Analysis <i class="fas fa-arrow-right text-xs opacity-50"></i>
                </button>
            </div>
        `;
        container.appendChild(card);
    });
}


// ============================================
// 숫자 포맷팅
// ============================================
function formatCompactNumber(num) {
    return new Intl.NumberFormat('ko-KR', { notation: "compact", maximumFractionDigits: 1 }).format(num) + '₩';
}


// ============================================
// Drawer 열기/닫기
// ============================================
function openDrawer() {
    document.getElementById('detailDrawer').classList.remove('translate-x-full');
}

function closeDrawer() {
    document.getElementById('detailDrawer').classList.add('translate-x-full');
}


// ============================================
// 상세 패널 열기
// ============================================
function openDetail(data) {
    const content = document.getElementById('drawerContent');

    // Build Allocation Table
    let tableRows = data.allocation.map(item => `
        <tr class="border-b border-white/5 text-sm">
            <td class="py-3 px-1">
                <div class="font-bold text-white">${item.ticker}</div>
                <div class="text-[10px] text-gray-500 truncate max-w-[120px]">${item.name}</div>
            </td>
            <td class="text-right text-gray-300">${item.weight}%</td>
            <td class="text-right text-white font-mono">${item.yield}</td>
        </tr>
    `).join('');

    content.innerHTML = `
        <div class="mb-8">
            <span class="text-xs font-bold px-2 py-1 rounded bg-white/10 text-white mb-2 inline-block">${data.title}</span>
            <h2 class="text-3xl font-bold text-white mb-2">Portfolio Detail</h2>
            <p class="text-gray-400 text-sm leading-relaxed">${data.description || data.one_liner}</p>
        </div>

        <!-- Chart -->
        <div class="mb-8 p-4 rounded-2xl bg-black/40 border border-white/5">
            <h3 class="text-xs text-gray-500 uppercase tracking-widest mb-4">Projected Monthly Cashflow</h3>
            <div class="relative h-48 w-full">
                <canvas id="cashflowChart"></canvas>
            </div>
        </div>

        <!-- Holdings List -->
        <div>
            <h3 class="text-xs text-gray-500 uppercase tracking-widest mb-4">Top Holdings (${data.allocation.length})</h3>
            <table class="w-full text-left border-collapse">
                <thead>
                    <tr class="text-[10px] text-gray-600 border-b border-white/10">
                        <th class="pb-2 font-medium">Asset</th>
                        <th class="pb-2 text-right font-medium">Weight</th>
                        <th class="pb-2 text-right font-medium">Yield</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        </div>
    `;

    openDrawer();

    // Render Chart
    setTimeout(() => {
        const ctx = document.getElementById('cashflowChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                datasets: [{
                    label: 'Monthly Income (KRW)',
                    data: data.chart_data,
                    backgroundColor: '#2997ff',
                    borderRadius: 4,
                    barThickness: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { display: false },
                    x: { grid: { display: false }, ticks: { color: '#666', font: { size: 10 } } }
                }
            }
        });
    }, 100);
}


// ============================================
// Basket 기능 (Placeholder)
// ============================================
function openBasket() {
    alert('Basket feature coming soon!');
}


// ============================================
// 통화 포맷 헬퍼
// ============================================
function krw(val) { return Number(val).toLocaleString() + '₩'; }
function usd(val) { return '$' + Number(val).toLocaleString(); }
```

---

## 2. 핵심 함수 요약

| 함수 | 역할 |
|------|------|
| `fetchThemes()` | `/api/dividend/themes` 호출 → 테마 캐러셀 렌더 |
| `selectTheme(id)` | 테마 선택 후 재최적화 트리거 |
| `triggerOptimization()` | `/api/dividend/all-tiers` POST → 3개 티어 로드 |
| `renderTierCards(tiers)` | 방어/균형/공격 카드 렌더링 |
| `openDetail(data)` | Drawer 열기 + 상세 테이블 + Chart.js 차트 |
| `formatCompactNumber(num)` | 큰 숫자 "1.5억₩" 형태로 변환 |

---

## 3. API 호출 흐름

```
1. 페이지 로드 → fetchThemes() → renderCarousel
2. targetInput 변경 → triggerOptimization()
3. 테마 클릭 → selectTheme() → triggerOptimization()
4. API 응답 → renderTierCards()
5. "View Analysis" 클릭 → openDetail() → Drawer + Chart
```

---

## 4. 전체 시스템 완성 체크리스트

| 파일 | 상태 | 설명 |
|------|------|------|
| BACKEND_STEP1.md | ✅ | 폴더 구조, tags.json, universe_seed.json, dividend_plans.json |
| BACKEND_STEP2.md | ✅ | loader.py (yfinance 데이터 수집) |
| BACKEND_STEP3.md | ✅ | engine.py, portfolio_optimizer.py, risk_analytics.py, dividend_analyzer.py, backtest.py |
| BACKEND_STEP4.md | ✅ | Flask API 라우트 |
| FRONTEND_STEP1.md | ✅ | index.html 랜딩 페이지 |
| FRONTEND_STEP2.md | ✅ | dashboard.html + 배당 탭 iframe |
| FRONTEND_STEP3.md | ✅ | dividend.html HTML/CSS |
| FRONTEND_STEP4.md | ✅ | dividend.html JavaScript |

🎉 **Blueprint 완성!**
