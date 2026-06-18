1|import { Routes, Route, Navigate } from 'react-router-dom'
2|import DashboardPage from '@/pages/DashboardPage'
3|import LoginPage from '@/pages/LoginPage'
4|import DocumentsPage from '@/pages/DocumentsPage'
5|import IngestPage from '@/pages/IngestPage'
6|import SettingsPage from '@/pages/SettingsPage'
7|
8|function ProtectedRoute({ children }: { children: React.ReactNode }) {
9|  const key = sessionStorage.getItem('rfr_api_key')
10|  if (!key) return <Navigate to="/login" replace />
11|  return <>{children}</>
12|}
13|
14|export default function App() {
15|  return (
16|    <AuthProvider>
17|      <div className="min-h-screen bg-background">
18|        <Routes>
19|          <Route path="/login" element={<LoginPage />} />
20|          <Route
21|            path="/"
22|            element={
23|              <ProtectedRoute>
24|                <DashboardPage />
25|              </ProtectedRoute>
26|            }
27|          />
28|          <Route
29|            path="/documents"
30|            element={
31|              <ProtectedRoute>
32|                <DocumentsPage />
33|              </ProtectedRoute>
34|            }
35|          />
36|          <Route
37|            path="/ingest"
38|            element={
39|              <ProtectedRoute>
40|                <IngestPage />
41|              </ProtectedRoute>
42|            }
43|          />
44|          <Route
45|            path="/settings"
46|            element={
47|              <ProtectedRoute>
48|                <SettingsPage />
49|              </ProtectedRoute>
50|            }
51|          />
52|          <Route path="*" element={<Navigate to="/" replace />} />
53|        </Routes>
54|      </div>
55|    </AuthProvider>
56|  )
57|}
58|