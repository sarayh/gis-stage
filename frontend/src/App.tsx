import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import StagesPage from './pages/StagesPage';
import StageDetailPage from './pages/StageDetailPage';
import StageFormPage from './pages/StageFormPage';
import EtudiantsPage from './pages/EtudiantsPage';
import EtudiantDetailPage from './pages/EtudiantDetailPage';
import EtudiantFormPage from './pages/EtudiantFormPage';
import CalendrierPage from './pages/CalendrierPage';
import StatistiquesPage from './pages/StatistiquesPage';
import StagesAcceptesPage from './pages/StagesAcceptesPage';
import StagesRefusesPage from './pages/StagesRefusesPage';
import HistoriquePage from './pages/HistoriquePage';
import LoadingSpinner from './components/LoadingSpinner';

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="stages" element={<StagesPage />} />
        <Route path="stages/nouveau" element={<StageFormPage />} />
        <Route path="stages/:id" element={<StageDetailPage />} />
        <Route path="stages/:id/modifier" element={<StageFormPage />} />
        <Route path="etudiants" element={<EtudiantsPage />} />
        <Route path="etudiants/nouveau" element={<EtudiantFormPage />} />
        <Route path="etudiants/:id" element={<EtudiantDetailPage />} />
        <Route path="etudiants/:id/modifier" element={<EtudiantFormPage />} />
        <Route path="stages-acceptes" element={<StagesAcceptesPage />} />
        <Route path="stages-refuses" element={<StagesRefusesPage />} />
        <Route path="calendrier" element={<CalendrierPage />} />
        <Route path="statistiques" element={<StatistiquesPage />} />
        <Route path="historique" element={<HistoriquePage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
