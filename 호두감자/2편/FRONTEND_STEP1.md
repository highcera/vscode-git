# Dividend System Blueprint - Frontend Step 1
# 랜딩 페이지 (index.html)

## 개요
이 문서는 대시보드로 진입하는 랜딩 페이지를 구현합니다.

---

## 1. index.html

`templates/index.html`:

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dividend Optimizer</title>
    
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
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #0a0a0a 100%);
            min-height: 100vh;
        }
        
        .gradient-text {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .glass-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .cta-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: all 0.3s ease;
        }
        
        .cta-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 40px rgba(102, 126, 234, 0.4);
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            border-color: rgba(102, 126, 234, 0.5);
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        
        .float-animation {
            animation: float 3s ease-in-out infinite;
        }
    </style>
</head>
<body class="text-white">
    
    <!-- Hero Section -->
    <section class="min-h-screen flex items-center justify-center px-6">
        <div class="max-w-4xl text-center">
            
            <!-- Logo Icon -->
            <div class="mb-8 float-animation">
                <div class="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-purple-500 to-indigo-600 shadow-2xl">
                    <i class="fas fa-chart-pie text-3xl"></i>
                </div>
            </div>
            
            <!-- Main Headline -->
            <h1 class="text-5xl md:text-7xl font-bold mb-6">
                <span class="gradient-text">Dividend</span>
                <span class="text-white">Optimizer</span>
            </h1>
            
            <!-- Subtitle -->
            <p class="text-xl md:text-2xl text-gray-400 mb-12 max-w-2xl mx-auto">
                AI 기반 배당 포트폴리오 최적화<br>
                <span class="text-gray-500">월 목표 수입에 맞는 최적의 배당 전략을 제안합니다</span>
            </p>
            
            <!-- CTA Buttons -->
            <div class="flex flex-col sm:flex-row gap-4 justify-center">
                <a href="/app" class="cta-button px-8 py-4 rounded-xl text-lg font-semibold shadow-xl flex items-center justify-center gap-3">
                    <i class="fas fa-rocket"></i>
                    대시보드 시작하기
                </a>
                <a href="/dividend" class="glass-card px-8 py-4 rounded-xl text-lg font-semibold hover:bg-white/10 transition flex items-center justify-center gap-3">
                    <i class="fas fa-coins"></i>
                    배당 최적화 바로가기
                </a>
            </div>
            
        </div>
    </section>
    
    
    <!-- Features Section -->
    <section class="py-20 px-6">
        <div class="max-w-6xl mx-auto">
            
            <h2 class="text-3xl font-bold text-center mb-16">
                <span class="gradient-text">핵심 기능</span>
            </h2>
            
            <div class="grid md:grid-cols-3 gap-8">
                
                <!-- Feature 1 -->
                <div class="glass-card feature-card p-8 rounded-2xl transition-all duration-300">
                    <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center mb-6">
                        <i class="fas fa-brain text-2xl"></i>
                    </div>
                    <h3 class="text-xl font-semibold mb-3">AI 포트폴리오 최적화</h3>
                    <p class="text-gray-400">
                        Risk Parity, Mean-Variance, Max Sharpe 등 
                        다양한 최적화 알고리즘으로 포트폴리오 구성
                    </p>
                </div>
                
                <!-- Feature 2 -->
                <div class="glass-card feature-card p-8 rounded-2xl transition-all duration-300">
                    <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center mb-6">
                        <i class="fas fa-calendar-alt text-2xl"></i>
                    </div>
                    <h3 class="text-xl font-semibold mb-3">월별 캐시플로우 예측</h3>
                    <p class="text-gray-400">
                        실제 배당 지급일 기반으로 
                        월별 예상 수입을 정확하게 시뮬레이션
                    </p>
                </div>
                
                <!-- Feature 3 -->
                <div class="glass-card feature-card p-8 rounded-2xl transition-all duration-300">
                    <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center mb-6">
                        <i class="fas fa-shield-alt text-2xl"></i>
                    </div>
                    <h3 class="text-xl font-semibold mb-3">배당 안정성 분석</h3>
                    <p class="text-gray-400">
                        Payout Ratio, 배당 성장률, 연속 지급 년수 등
                        지속 가능성을 A-F 등급으로 평가
                    </p>
                </div>
                
            </div>
        </div>
    </section>
    
    
    <!-- Footer -->
    <footer class="py-8 border-t border-white/10">
        <div class="max-w-6xl mx-auto px-6 text-center text-gray-500">
            <p>&copy; 2024 Dividend Optimizer. Built with Flask + Tailwind CSS</p>
        </div>
    </footer>
    
</body>
</html>
```

---

## 2. 핵심 요소

### 네비게이션 링크
```html
<!-- 대시보드로 이동 -->
<a href="/app">대시보드 시작하기</a>

<!-- 배당 페이지로 바로 이동 -->
<a href="/dividend">배당 최적화 바로가기</a>
```

### 스타일링 특징
- **Glassmorphism**: `backdrop-filter: blur()` + 반투명 배경
- **Gradient Text**: CSS gradient + clip
- **Float Animation**: 로고 아이콘 애니메이션
- **Dark Theme**: 전체 다크 모드 기반

---

## 다음 단계

**FRONTEND_STEP2.md**에서 대시보드 레이아웃과 배당 탭 연결을 구현합니다.
