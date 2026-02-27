# Frontend Structure - FinDocAnalyzer

## Tech Stack

| Category | Technology | Purpose |
|----------|------------|---------|
| **Framework** | React 18 | Component-based UI |
| **Build Tool** | Vite 5 | Fast development & production builds |
| **Language** | TypeScript | Type safety |
| **Styling** | Tailwind CSS | Utility-first CSS |
| **UI Components** | shadcn/ui | Pre-built accessible components |
| **Icons** | Lucide React | Modern icon library |
| **State Management** | Zustand | Lightweight state management |
| **Data Fetching** | TanStack Query (React Query) | Server state management |
| **Forms** | React Hook Form + Zod | Form handling & validation |
| **Animations** | Framer Motion | Smooth transitions |
| **AI Copilot** | CopilotKit | AI-powered UI components |
| **Charts** | Recharts | Data visualization |

---

## Project Structure

```
frontend/src/
├── 📁 components/
│   ├── 📁 ui/                    # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── dialog.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── progress.tsx
│   │   ├── select.tsx
│   │   ├── tabs.tsx
│   │   ├── toast.tsx
│   │   └── ...
│   │
│   ├── 📁 auth/                  # Authentication components
│   │   ├── LoginForm.tsx
│   │   ├── RegisterForm.tsx
│   │   ├── ProtectedRoute.tsx
│   │   └── AuthProvider.tsx
│   │
│   ├── 📁 layout/              # Layout components
│   │   ├── MainLayout.tsx      # Sidebar + content area
│   │   ├── Header.tsx          # Top navigation
│   │   ├── Sidebar.tsx         # Left navigation
│   │   └── MobileNav.tsx       # Mobile bottom nav
│   │
│   ├── 📁 documents/           # Document management
│   │   ├── DocumentUpload.tsx  # File upload with drag-drop
│   │   ├── DocumentList.tsx    # List of user's documents
│   │   ├── DocumentCard.tsx    # Single document preview
│   │   └── DocumentFilters.tsx # Filter & search
│   │
│   ├── 📁 analysis/            # Analysis components
│   │   ├── AnalysisProgress.tsx  # Real-time progress tracking
│   │   ├── AnalysisResults.tsx   # Full results display
│   │   ├── ScoreCards.tsx        # Fundamental/Tech/Risk scores
│   │   ├── RecommendationCard.tsx # Buy/Hold/Sell card
│   │   ├── MetricCharts.tsx      # Charts & visualizations
│   │   ├── RiskFlags.tsx         # Alert flags display
│   │   └── ReportDownload.tsx    # PDF download button
│   │
│   ├── 📁 chat/               # AI Copilot components
│   │   ├── CopilotChat.tsx    # AI assistant sidebar
│   │   ├── SuggestedPrompts.tsx # Quick action prompts
│   │   └── ContextualHelp.tsx   # Inline AI help
│   │
│   └── 📁 dashboard/          # Dashboard components
│       ├── StatsOverview.tsx  # Key metrics summary
│       ├── RecentActivity.tsx # Recent analyses
│       └── QuickActions.tsx   # Quick upload buttons
│
├── 📁 hooks/
│   ├── useAuth.ts             # Authentication state
│   ├── useDocuments.ts        # Document CRUD operations
│   ├── useAnalysis.ts         # Analysis lifecycle
│   ├── useWebSocket.ts        # Real-time progress
│   └── useLocalStorage.ts     # Persist user preferences
│
├── 📁 services/
│   ├── api.ts                 # Axios instance with interceptors
│   ├── auth.service.ts        # Auth API calls
│   ├── document.service.ts    # Document API calls
│   ├── analysis.service.ts    # Analysis API calls
│   └── websocket.service.ts   # WebSocket connection
│
├── 📁 stores/
│   ├── authStore.ts           # Auth state (Zustand)
│   ├── documentStore.ts       # Document state
│   └── uiStore.ts             # UI state (theme, sidebar)
│
├── 📁 types/
│   ├── api.ts                 # API response types
│   ├── document.ts            # Document types
│   ├── analysis.ts            # Analysis types
│   └── user.ts                # User types
│
├── 📁 lib/
│   ├── utils.ts               # Utility functions
│   ├── constants.ts           # App constants
│   └── formatters.ts          # Data formatters
│
├── 📁 styles/
│   └── global.css              # Global styles + Tailwind
│
├── App.tsx                     # Main app component
├── main.tsx                    # Entry point
└── index.html                  # HTML template
```

---

## Key Components

### 1. Main Layout

```tsx
// components/layout/MainLayout.tsx
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { Outlet } from 'react-router-dom';

export const MainLayout = () => {
  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      <Sidebar className="hidden md:flex w-64 border-r" />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
```

### 2. Document Upload Component

```tsx
// components/documents/DocumentUpload.tsx
import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useDocuments } from '@/hooks/useDocuments';

export const DocumentUpload = () => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const { uploadDocument } = useDocuments();

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);
    setProgress(0);

    try {
      await uploadDocument(file, {
        onProgress: (percent) => setProgress(percent),
      });
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  }, [uploadDocument]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    maxFiles: 1,
  });

  return (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
        transition-colors duration-200
        ${isDragActive 
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
          : 'border-gray-300 hover:border-gray-400 dark:border-gray-700'
        }
      `}
    >
      <input {...getInputProps()} />
      
      {uploading ? (
        <div className="space-y-4">
          <div className="animate-pulse">
            <Upload className="w-12 h-12 mx-auto text-blue-500" />
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Uploading... {progress}%
          </p>
          <Progress value={progress} className="w-full" />
        </div>
      ) : (
        <>
          <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
          <p className="text-lg font-medium text-gray-700 dark:text-gray-300">
            {isDragActive ? 'Drop your file here' : 'Drag & drop your document'}
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
            Or click to browse. Supports PDF, DOCX, TXT (max 10MB)
          </p>
        </>
      )}
    </div>
  );
};
```

### 3. Analysis Progress Component

```tsx
// components/analysis/AnalysisProgress.tsx
import { useEffect, useState } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent } from '@/components/ui/card';
import { Bot, TrendingUp, Shield, FileSearch, CheckCircle } from 'lucide-react';

const AGENT_ICONS = {
  manager: Bot,
  fundamental: FileSearch,
  technical: TrendingUp,
  risk: Shield,
  synthesizer: CheckCircle,
};

interface AnalysisProgressProps {
  jobId: string;
  onComplete: () => void;
}

export const AnalysisProgress = ({ jobId, onComplete }: AnalysisProgressProps) => {
  const [progress, setProgress] = useState(0);
  const [currentAgent, setCurrentAgent] = useState<string>('');
  const [agentLogs, setAgentLogs] = useState<string[]>([]);
  
  const { lastMessage } = useWebSocket(`wss://api.findoc-analyzer.railway.app/ws/analysis/${jobId}`);

  useEffect(() => {
    if (!lastMessage) return;

    const data = JSON.parse(lastMessage.data);
    
    switch (data.type) {
      case 'agent_start':
        setCurrentAgent(data.agent);
        setProgress(data.progress);
        break;
      case 'agent_complete':
        setAgentLogs(prev => [...prev, `${data.agent} completed`]);
        break;
      case 'progress':
        setProgress(data.progress);
        break;
      case 'complete':
        onComplete();
        break;
    }
  }, [lastMessage, onComplete]);

  const CurrentIcon = AGENT_ICONS[currentAgent as keyof typeof AGENT_ICONS] || Bot;

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardContent className="p-6 space-y-6">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-full">
            <CurrentIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold capitalize">
              {currentAgent ? `${currentAgent} Analysis` : 'Initializing...'}
            </h3>
            <p className="text-sm text-gray-500">
              {progress}% complete
            </p>
          </div>
        </div>

        <Progress value={progress} className="w-full" />

        <div className="space-y-2 max-h-48 overflow-y-auto">
          {agentLogs.map((log, index) => (
            <div 
              key={index}
              className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400"
            >
              <CheckCircle className="w-4 h-4 text-green-500" />
              {log}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
```

### 4. Recommendation Card

```tsx
// components/analysis/RecommendationCard.tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus, Target, AlertTriangle } from 'lucide-react';

interface RecommendationCardProps {
  recommendation: {
    action: 'buy' | 'hold' | 'sell' | 'watch';
    confidence: number;
    targetPrice?: number;
    stopLoss?: number;
    rationale: string;
  };
}

const RECOMMENDATION_CONFIG = {
  buy: {
    color: 'bg-green-500',
    icon: TrendingUp,
    label: 'BUY',
  },
  hold: {
    color: 'bg-yellow-500',
    icon: Minus,
    label: 'HOLD',
  },
  sell: {
    color: 'bg-red-500',
    icon: TrendingDown,
    label: 'SELL',
  },
  watch: {
    color: 'bg-blue-500',
    icon: AlertTriangle,
    label: 'WATCH',
  },
};

export const RecommendationCard = ({ recommendation }: RecommendationCardProps) => {
  const config = RECOMMENDATION_CONFIG[recommendation.action];
  const Icon = config.icon;

  return (
    <Card className="border-2">
      <CardHeader className={`${config.color} text-white`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Icon className="w-8 h-8" />
            <div>
              <CardTitle className="text-2xl">{config.label}</CardTitle>
              <p className="text-sm opacity-90">
                Confidence: {Math.round(recommendation.confidence * 100)}%
              </p>
            </div>
          </div>
          <Badge variant="secondary" className="text-lg font-bold">
            {Math.round(recommendation.confidence * 100)}%
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="p-6 space-y-4">
        <p className="text-gray-700 dark:text-gray-300">
          {recommendation.rationale}
        </p>

        {(recommendation.targetPrice || recommendation.stopLoss) && (
          <div className="flex gap-4 pt-4 border-t">
            {recommendation.targetPrice && (
              <div className="flex items-center gap-2">
                <Target className="w-5 h-5 text-green-600" />
                <div>
                  <p className="text-sm text-gray-500">Target Price</p>
                  <p className="font-semibold">${recommendation.targetPrice.toFixed(2)}</p>
                </div>
              </div>
            )}
            {recommendation.stopLoss && (
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-600" />
                <div>
                  <p className="text-sm text-gray-500">Stop Loss</p>
                  <p className="font-semibold">${recommendation.stopLoss.toFixed(2)}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
```

### 5. Score Cards

```tsx
// components/analysis/ScoreCards.tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface ScoreCardsProps {
  fundamentalScore: string;
  technicalScore: string;
  riskScore: number;
  compositeScore: number;
}

const SCORE_COLORS = {
  'A+': 'bg-green-600',
  'A': 'bg-green-500',
  'A-': 'bg-green-400',
  'B+': 'bg-blue-500',
  'B': 'bg-blue-400',
  'B-': 'bg-blue-300',
  'C+': 'bg-yellow-500',
  'C': 'bg-yellow-400',
  'C-': 'bg-yellow-300',
  'D': 'bg-orange-500',
  'F': 'bg-red-500',
};

export const ScoreCards = ({
  fundamentalScore,
  technicalScore,
  riskScore,
  compositeScore,
}: ScoreCardsProps) => {
  const ScoreBadge = ({ score }: { score: string }) => (
    <div className={`
      inline-flex items-center justify-center w-16 h-16 rounded-full
      text-white text-2xl font-bold
      ${SCORE_COLORS[score as keyof typeof SCORE_COLORS] || 'bg-gray-400'}
    `}>
      {score}
    </div>
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Fundamental Score */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-gray-600">
            Fundamental Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-between">
          <ScoreBadge score={fundamentalScore} />
          <div className="text-right">
            <p className="text-2xl font-bold">{fundamentalScore}</p>
            <p className="text-sm text-gray-500">Financial Health</p>
          </div>
        </CardContent>
      </Card>

      {/* Technical Score */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-gray-600">
            Technical Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-between">
          <ScoreBadge score={technicalScore} />
          <div className="text-right">
            <p className="text-2xl font-bold">{technicalScore}</p>
            <p className="text-sm text-gray-500">Market Position</p>
          </div>
        </CardContent>
      </Card>

      {/* Risk Score */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-gray-600">
            Risk Assessment
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold">{riskScore}/10</span>
            <span className={`
              text-sm font-medium
              ${riskScore <= 3 ? 'text-green-600' : riskScore <= 6 ? 'text-yellow-600' : 'text-red-600'}
            `}>
              {riskScore <= 3 ? 'Low' : riskScore <= 6 ? 'Moderate' : 'High'}
            </span>
          </div>
          <Progress 
            value={riskScore * 10} 
            className={`
              ${riskScore <= 3 ? '[&>div]:bg-green-500' : riskScore <= 6 ? '[&>div]:bg-yellow-500' : '[&>div]:bg-red-500'}
            `}
          />
        </CardContent>
      </Card>

      {/* Composite Score */}
      <Card className="md:col-span-3">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Composite Score</p>
              <p className="text-4xl font-bold">{compositeScore.toFixed(1)}/10</p>
            </div>
            <Progress 
              value={compositeScore * 10} 
              className="w-1/2 [&>div]:bg-blue-500"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
```

---

## CopilotKit Integration

```tsx
// components/chat/CopilotChat.tsx
import { CopilotChat } from '@copilotkit/react-ui';
import { useCopilotContext } from '@copilotkit/react-core';

export const AICopilotSidebar = () => {
  const { documentId, analysisResults } = useAnalysisContext();

  return (
    <div className="w-80 border-l bg-gray-50 dark:bg-gray-900 p-4">
      <h3 className="font-semibold mb-4">AI Assistant</h3>
      
      <CopilotChat
        className="h-[calc(100vh-200px)]"
        instructions={`
          You are a financial analysis assistant. The user is viewing an analysis 
          of ${analysisResults?.company_name || 'a company'}. 
          
          Key insights:
          - Recommendation: ${analysisResults?.recommendation?.action}
          - Risk Score: ${analysisResults?.scoring?.risk_score}/10
          
          Help them understand the analysis, explain metrics, and answer questions.
        `}
        
        context={{
          documentId,
          analysisResults,
        }}
        
        suggestedPrompts={[
          "Explain the risk score",
          "What are the main red flags?",
          "Compare to industry average",
          "Should I invest $10,000?",
        ]}
      />
    </div>
  );
};
```

---

## Routes Structure

```tsx
// App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

// Pages
import { LoginPage } from '@/pages/auth/Login';
import { RegisterPage } from '@/pages/auth/Register';
import { DashboardPage } from '@/pages/dashboard/Dashboard';
import { DocumentsPage } from '@/pages/documents/Documents';
import { AnalysisPage } from '@/pages/analysis/Analysis';
import { ResultsPage } from '@/pages/analysis/Results';
import { SettingsPage } from '@/pages/settings/Settings';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected Routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<MainLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/analysis/:documentId" element={<AnalysisPage />} />
            <Route path="/results/:jobId" element={<ResultsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

---

## State Management (Zustand)

```tsx
// stores/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'user' | 'admin';
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  
  setAuth: (user: User, accessToken: string) => void;
  clearAuth: () => void;
  updateUser: (user: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      
      setAuth: (user, accessToken) => 
        set({ user, accessToken, isAuthenticated: true }),
      
      clearAuth: () => 
        set({ user: null, accessToken: null, isAuthenticated: false }),
      
      updateUser: (userData) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...userData } : null,
        })),
    }),
    {
      name: 'auth-storage',
    }
  )
);
```

---

## Build Configuration

```ts
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
```

---

## Environment Variables

```env
# .env.development
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# .env.production
VITE_API_URL=https://api.findoc-analyzer.railway.app
VITE_WS_URL=wss://api.findoc-analyzer.railway.app
```

---

## Next Steps

1. **Initialize shadcn/ui:**
   ```bash
   npx shadcn-ui@latest init
   ```

2. **Install components:**
   ```bash
   npx shadcn-ui add button card input progress dialog tabs toast
   ```

3. **Install CopilotKit:**
   ```bash
   npm install @copilotkit/react-core @copilotkit/react-ui
   ```

4. **Build components** following the structure above

5. **Connect to backend** using the API services

---

**Ready to deploy?** See `/docs/DEPLOYMENT.md`! 🚀
