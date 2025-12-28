# Dividend System Blueprint - Frontend Step 3
# 배당 UI HTML/CSS 구조 (실제 전체 코드)

## 개요
이 문서는 배당 최적화 페이지(`dividend.html`)의 완전한 소스 코드입니다.

---

## 1. dividend.html 전체 코드

`templates/dividend.html`:

```html
<!DOCTYPE html>
<html lang="ko" class="dark">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dividend Optim | Premium</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
                    },
                    colors: {
                        apple: {
                            gray: '#1c1c1e',
                            blue: '#2997ff',
                            blue_dark: '#0071e3',
                            green: '#30d158',
                            orange: '#ff9f0a',
                            red: '#ff453a',
                            purple: '#bf5af2',
                            indigo: '#5e5ce6',
                        }
                    },
                    backdropBlur: {
                        'xs': '2px',
                    }
                }
            }
        }
    </script>
    <!-- Fonts & Icons -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        body {
            background-color: #000000;
            color: #f5f5f7;
            font-family: 'Inter', sans-serif;
            -webkit-font-smoothing: antialiased;
        }

        /* Hide Scrollbar but allow scroll */
        .no-scrollbar::-webkit-scrollbar {
            display: none;
        }
        .no-scrollbar {
            -ms-overflow-style: none;
            scrollbar-width: none;
        }

        /* Glassmorphism Utilities */
        .glass-panel {
            background: rgba(28, 28, 30, 0.6);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .glass-card {
            background: rgba(44, 44, 46, 0.4);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            transition: all 0.3s ease;
        }

        .glass-card:hover {
            background: rgba(58, 58, 60, 0.5);
            transform: translateY(-2px);
            border-color: rgba(255, 255, 255, 0.15);
        }

        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .animate-fade-in {
            animation: fadeIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }

        /* Custom Range Slider */
        input[type=range] {
            -webkit-appearance: none;
            appearance: none;
            background: transparent;
        }

        input[type=range]::-webkit-slider-thumb {
            -webkit-appearance: none;
            height: 20px;
            width: 20px;
            border-radius: 50%;
            background: #ffffff;
            cursor: pointer;
            margin-top: -8px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
        }

        input[type=range]::-webkit-slider-runnable-track {
            width: 100%;
            height: 4px;
            cursor: pointer;
            background: #3a3a3c;
            border-radius: 2px;
        }
    </style>
</head>

<body class="min-h-screen pb-20 selection:bg-apple-blue selection:text-white">

    <!-- Navbar -->
    <nav class="fixed top-0 w-full z-50 glass-panel border-b-0">
        <div class="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <a href="/" class="text-white/60 hover:text-white transition"><i class="fas fa-chevron-left"></i> Home</a>
                <div class="h-4 w-[1px] bg-white/20 mx-2"></div>
                <h1 class="font-semibold text-lg tracking-tight">Dividend<span class="text-apple-blue">Optim</span></h1>
            </div>
            <div class="text-xs text-gray-500 font-medium tracking-wide">
                DATA UPDATED: <span id="lastUpdated" class="text-gray-400">Loading...</span>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="pt-24 max-w-7xl mx-auto px-6">

        <!-- Hero: Goal Setting -->
        <section class="mb-16 text-center animate-fade-in">
            <h2 class="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                Design your cash flow.
            </h2>
            <p class="text-gray-400 mb-10 text-lg">Set your monthly target and choose a strategy.</p>

            <div class="max-w-xl mx-auto glass-panel rounded-3xl p-1 inline-flex items-center gap-2">
                <span class="pl-6 text-gray-400 font-medium">₩</span>
                <input type="number" id="targetInput" value="1000000" step="100000"
                    class="bg-transparent border-none text-3xl font-bold text-white w-48 focus:ring-0 text-center placeholder-gray-600"
                    placeholder="1,000,000">
                <span class="text-gray-500 pr-6 text-sm font-medium">/ month</span>
            </div>

            <!-- Quick Select Pills -->
            <div class="flex justify-center gap-3 mt-6">
                <button onclick="setGoal(500000)"
                    class="px-4 py-2 rounded-full bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/20 text-sm transition">₩50만</button>
                <button onclick="setGoal(1000000)"
                    class="px-4 py-2 rounded-full bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/20 text-sm transition">₩100만</button>
                <button onclick="setGoal(3000000)"
                    class="px-4 py-2 rounded-full bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/20 text-sm transition">₩300만</button>
                <button onclick="setGoal(5000000)"
                    class="px-4 py-2 rounded-full bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/20 text-sm transition">₩500만</button>
            </div>

            <!-- Advanced Settings Toggle -->
            <div class="mt-6">
                <button onclick="document.getElementById('advSettings').classList.toggle('hidden')"
                    class="text-xs text-gray-500 hover:text-white transition flex items-center justify-center gap-1 mx-auto">
                    <i class="fas fa-sliders-h"></i> Advanced Settings
                </button>
                <div id="advSettings" class="hidden mt-4 glass-panel rounded-xl p-4 max-w-sm mx-auto flex gap-4 text-left">
                    <div class="flex-1">
                        <label class="block text-[10px] text-gray-400 uppercase tracking-wider mb-1">FX Rate (₩/$)</label>
                        <input type="number" id="fxRate" value="1420"
                            class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-1 text-sm text-white focus:border-apple-blue focus:outline-none">
                    </div>
                    <div class="flex-1">
                        <label class="block text-[10px] text-gray-400 uppercase tracking-wider mb-1">Tax Rate (%)</label>
                        <input type="number" id="taxRate" value="0.154" step="0.001"
                            class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-1 text-sm text-white focus:border-apple-blue focus:outline-none">
                    </div>
                </div>
            </div>
        </section>

        <!-- Theme Selector (Carousel) -->
        <section class="mb-12 animate-fade-in" style="animation-delay: 0.1s;">
            <div class="flex items-center justify-between mb-4 px-2">
                <h3 class="text-xl font-bold text-white">Choose a Strategy</h3>
                <div class="flex gap-2">
                    <button id="scrollLeft"
                        class="w-8 h-8 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center text-gray-400"><i
                            class="fas fa-chevron-left"></i></button>
                    <button id="scrollRight"
                        class="w-8 h-8 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center text-gray-400"><i
                            class="fas fa-chevron-right"></i></button>
                </div>
            </div>

            <div id="themeCarousel" class="flex gap-4 overflow-x-auto no-scrollbar py-2 scroll-smooth">
                <!-- Themes will be injected here -->
                <div class="animate-pulse flex gap-4 w-full">
                    <div class="h-24 w-60 bg-white/5 rounded-2xl"></div>
                    <div class="h-24 w-60 bg-white/5 rounded-2xl"></div>
                    <div class="h-24 w-60 bg-white/5 rounded-2xl"></div>
                </div>
            </div>
        </section>

        <!-- Result Grid -->
        <section id="resultsSection" class="mb-20 animate-fade-in" style="animation-delay: 0.2s;">
            <div id="loadingOverlay"
                class="hidden fixed inset-0 z-40 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                <div class="text-center">
                    <div class="inline-block w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin mb-4"></div>
                    <p class="text-sm font-medium text-gray-300">Optimizing Portfolio...</p>
                </div>
            </div>

            <div id="tierGrid" class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <!-- Tier Cards will be injected here -->
            </div>
        </section>

    </main>

    <!-- Detail Drawer (Slide-over) -->
    <div id="detailDrawer"
        class="fixed inset-y-0 right-0 w-full md:w-[480px] bg-[#1c1c1e] z-50 transform translate-x-full transition-transform duration-300 ease-in-out border-l border-white/10 shadow-2xl flex flex-col">
        <!-- Close Button -->
        <button onclick="closeDrawer()"
            class="absolute top-4 right-4 w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-gray-400 hover:bg-white/20 hover:text-white transition z-10">
            <i class="fas fa-times"></i>
        </button>

        <!-- Drawer Content -->
        <div id="drawerContent" class="h-full overflow-y-auto p-8 relative">
            <!-- Content injected by JS -->
        </div>

        <!-- Sticky Bottom Action -->
        <div class="p-6 border-t border-white/10 bg-[#1c1c1e]/90 backdrop-blur pb-8">
            <button
                class="w-full py-4 bg-apple-blue hover:bg-apple-blue_dark text-white rounded-xl font-bold text-lg transition shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2">
                <i class="fas fa-plus"></i> Add to Basket
            </button>
        </div>
    </div>

    <!-- Basket Floating Button -->
    <div class="fixed bottom-8 right-8 z-40">
        <button onclick="openBasket()"
            class="w-14 h-14 rounded-full bg-white text-black shadow-lg shadow-white/10 flex items-center justify-center hover:scale-105 transition-transform">
            <i class="fas fa-shopping-bag text-xl"></i>
            <span id="basketCount"
                class="absolute -top-1 -right-1 bg-apple-red text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full hidden">0</span>
        </button>
    </div>

    <!-- JavaScript는 FRONTEND_STEP4.md에 포함 -->

</body>
</html>
```

---

## 2. 핵심 CSS 클래스 설명

### Glassmorphism
```css
.glass-panel {
    background: rgba(28, 28, 30, 0.6);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.glass-card {
    background: rgba(44, 44, 46, 0.4);
    backdrop-filter: blur(15px);
    border: 1px solid rgba(255, 255, 255, 0.08);
}
```

### Apple 색상 팔레트
```javascript
colors: {
    apple: {
        gray: '#1c1c1e',
        blue: '#2997ff',     // 메인 액센트
        green: '#30d158',    // 방어형
        orange: '#ff9f0a',   // 공격형
        red: '#ff453a',
        purple: '#bf5af2',
    }
}
```

---

## 다음 단계

**FRONTEND_STEP4.md**에서 JavaScript 로직을 구현합니다.
