# Dividend System Blueprint - Frontend Step 2
# 대시보드 레이아웃 + 배당 탭 연결

## 개요
이 문서는 대시보드 기본 레이아웃과 배당 탭 연결을 구현합니다.

---

## 1. dashboard.html 기본 구조

`templates/dashboard.html`:

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Dividend Optimizer</title>
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        body {
            background-color: #09090b;
        }
        
        .sidebar {
            background: linear-gradient(180deg, #0f0f12 0%, #0a0a0c 100%);
        }
        
        .nav-item {
            transition: all 0.2s ease;
        }
        
        .nav-item:hover {
            background: rgba(255, 255, 255, 0.05);
        }
        
        .nav-item.active {
            background: rgba(102, 126, 234, 0.1);
            border-left: 3px solid #667eea;
        }
        
        .content-section {
            display: none;
        }
        
        .content-section.active {
            display: block;
        }
    </style>
</head>
<body class="text-white flex h-screen overflow-hidden">
    
    <!-- Sidebar -->
    <aside class="sidebar w-64 flex flex-col border-r border-white/10">
        
        <!-- Logo -->
        <div class="p-6 border-b border-white/10">
            <a href="/" class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center">
                    <i class="fas fa-chart-pie"></i>
                </div>
                <span class="font-bold text-lg">Dividend</span>
            </a>
        </div>
        
        <!-- Navigation -->
        <nav class="flex-1 py-4">
            <ul class="space-y-1 px-3">
                
                <li>
                    <button onclick="switchTab('overview')" 
                            id="nav-overview"
                            class="nav-item w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left">
                        <i class="fas fa-home w-5 text-gray-400"></i>
                        <span>Overview</span>
                    </button>
                </li>
                
                <li>
                    <button onclick="switchTab('dividend')" 
                            id="nav-dividend"
                            class="nav-item active w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left">
                        <i class="fas fa-coins w-5 text-purple-400"></i>
                        <span>배당 최적화</span>
                    </button>
                </li>
                
                <li>
                    <button onclick="switchTab('analysis')" 
                            id="nav-analysis"
                            class="nav-item w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left">
                        <i class="fas fa-chart-line w-5 text-gray-400"></i>
                        <span>분석</span>
                    </button>
                </li>
                
                <li>
                    <button onclick="switchTab('settings')" 
                            id="nav-settings"
                            class="nav-item w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left">
                        <i class="fas fa-cog w-5 text-gray-400"></i>
                        <span>설정</span>
                    </button>
                </li>
                
            </ul>
        </nav>
        
        <!-- Footer -->
        <div class="p-4 border-t border-white/10 text-xs text-gray-500">
            <p>v1.0.0 | © 2024</p>
        </div>
        
    </aside>
    
    
    <!-- Main Content Area -->
    <main class="flex-1 overflow-y-auto">
        
        <!-- Overview Section -->
        <div id="content-overview" class="content-section p-8">
            <h1 class="text-2xl font-bold mb-6">Overview</h1>
            <p class="text-gray-400">대시보드 개요 페이지입니다.</p>
        </div>
        
        <!-- Dividend Section (iframe) -->
        <div id="content-dividend" class="content-section active h-full">
            <iframe 
                src="/dividend" 
                class="w-full h-full border-0"
                title="Dividend Optimizer"
            ></iframe>
        </div>
        
        <!-- Analysis Section -->
        <div id="content-analysis" class="content-section p-8">
            <h1 class="text-2xl font-bold mb-6">분석</h1>
            <p class="text-gray-400">분석 페이지입니다.</p>
        </div>
        
        <!-- Settings Section -->
        <div id="content-settings" class="content-section p-8">
            <h1 class="text-2xl font-bold mb-6">설정</h1>
            <p class="text-gray-400">설정 페이지입니다.</p>
        </div>
        
    </main>
    
    
    <script>
        // Tab switching logic
        function switchTab(tabId) {
            // Hide all content sections
            document.querySelectorAll('.content-section').forEach(section => {
                section.classList.remove('active');
            });
            
            // Remove active from all nav items
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
            });
            
            // Show selected content
            const content = document.getElementById('content-' + tabId);
            if (content) {
                content.classList.add('active');
            }
            
            // Activate nav item
            const nav = document.getElementById('nav-' + tabId);
            if (nav) {
                nav.classList.add('active');
            }
        }
        
        // Initialize with dividend tab active
        document.addEventListener('DOMContentLoaded', () => {
            switchTab('dividend');
        });
    </script>
    
</body>
</html>
```

---

## 2. 핵심 개념: iframe 통합

배당 페이지를 대시보드에 통합하는 방법:

```html
<!-- 배당 페이지를 iframe으로 포함 -->
<div id="content-dividend" class="content-section active h-full">
    <iframe 
        src="/dividend" 
        class="w-full h-full border-0"
        title="Dividend Optimizer"
    ></iframe>
</div>
```

### 장점
1. **스타일 격리**: 배당 페이지 스타일이 대시보드와 충돌하지 않음
2. **독립적 로딩**: 배당 페이지만 단독으로도 접근 가능
3. **쉬운 업데이트**: 배당 UI 수정 시 대시보드 영향 없음

---

## 3. 탭 전환 로직

```javascript
function switchTab(tabId) {
    // 모든 콘텐츠 숨김
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // 모든 네비게이션 비활성화
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // 선택된 콘텐츠 표시
    document.getElementById('content-' + tabId).classList.add('active');
    
    // 네비게이션 활성화
    document.getElementById('nav-' + tabId).classList.add('active');
}
```

---

## 4. 사이드바 네비게이션 구조

```html
<nav>
    <ul>
        <li>
            <button onclick="switchTab('overview')">
                <i class="fas fa-home"></i>
                Overview
            </button>
        </li>
        <li>
            <button onclick="switchTab('dividend')">
                <i class="fas fa-coins"></i>
                배당 최적화
            </button>
        </li>
        <!-- 추가 메뉴 -->
    </ul>
</nav>
```

---

## 다음 단계

**FRONTEND_STEP3.md**에서 배당 UI의 HTML/CSS 구조를 구현합니다.
