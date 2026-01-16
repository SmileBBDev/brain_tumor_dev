import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import M1InferencePage from './pages/M1InferencePage'
import MGInferencePage from './pages/MGInferencePage'
import MMInferencePage from './pages/MMInferencePage'
import DebugConsolePage from './pages/DebugConsolePage'

// Layout component with header
function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold text-gray-900">
              Brain Tumor CDSS
            </h1>
            <nav className="flex space-x-4">
              <Link
                to="/m1"
                className="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-100"
              >
                M1 MRI 분석
              </Link>
              <Link
                to="/mg"
                className="px-3 py-2 rounded-md text-sm font-medium text-purple-600 hover:bg-purple-50"
              >
                MG Gene Analysis
              </Link>
              <Link
                to="/mm"
                className="px-3 py-2 rounded-md text-sm font-medium text-teal-600 hover:bg-teal-50"
              >
                MM 멀티모달
              </Link>
              <span className="border-l border-gray-300 mx-2" />
              <Link
                to="/debug"
                className="px-3 py-2 rounded-md text-sm font-medium text-orange-600 hover:bg-orange-50"
              >
                Debug Console
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {children}
      </main>
    </div>
  )
}

function AppRoutes() {
  const location = useLocation()

  // Debug console is full-screen without layout
  if (location.pathname === '/debug') {
    return <DebugConsolePage />
  }

  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<M1InferencePage />} />
        <Route path="/m1" element={<M1InferencePage />} />
        <Route path="/mg" element={<MGInferencePage />} />
        <Route path="/mm" element={<MMInferencePage />} />
      </Routes>
    </MainLayout>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}

export default App
