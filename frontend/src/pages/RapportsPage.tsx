import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { rapportsApi } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Download, FileText, TrendingUp } from 'lucide-react';
import toast from 'react-hot-toast';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export default function RapportsPage() {
  const currentYear = new Date().getFullYear();
  const [selectedYear, setSelectedYear] = useState(currentYear);

  const { data: stats, isLoading } = useQuery({
    queryKey: ['stats', selectedYear],
    queryFn: () => rapportsApi.getStatistiquesAnnuelles(selectedYear),
  });

  const handleExportCSV = async () => {
    try {
      const blob = await rapportsApi.exportCSV({ annee: selectedYear });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `export_stages_${selectedYear}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success('Export téléchargé');
    } catch {
      toast.error('Erreur lors de l\'export');
    }
  };

  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);

  const serviceData = stats
    ? Object.entries(stats.stages_par_service).map(([name, value]) => ({
        name,
        value,
      }))
    : [];

  const etablissementData = stats
    ? Object.entries(stats.stages_par_etablissement).map(([name, value]) => ({
        name: name.length > 20 ? name.substring(0, 20) + '...' : name,
        fullName: name,
        value,
      }))
    : [];

  const statusData = stats
    ? [
        { name: 'Acceptés', value: stats.stages_acceptes },
        { name: 'Refusés', value: stats.stages_refuses },
        { name: 'En cours', value: stats.stages_en_cours },
        { name: 'Terminés', value: stats.stages_termines },
      ].filter(d => d.value > 0)
    : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Rapports et statistiques</h1>
        <div className="flex items-center space-x-4">
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(Number(e.target.value))}
            className="input w-32"
          >
            {years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
          <button onClick={handleExportCSV} className="btn btn-primary">
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
        </div>
      ) : stats ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="card p-6">
              <div className="flex items-center">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <FileText className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm text-gray-600">Total stages</p>
                  <p className="text-2xl font-bold">{stats.total_stages}</p>
                </div>
              </div>
            </div>

            <div className="card p-6">
              <div className="flex items-center">
                <div className="p-3 bg-green-100 rounded-lg">
                  <TrendingUp className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm text-gray-600">Taux d'acceptation</p>
                  <p className="text-2xl font-bold">{stats.taux_acceptation}%</p>
                </div>
              </div>
            </div>

            <div className="card p-6">
              <p className="text-sm text-gray-600">Stages acceptés</p>
              <p className="text-2xl font-bold text-green-600">{stats.stages_acceptes}</p>
            </div>

            <div className="card p-6">
              <p className="text-sm text-gray-600">Stages refusés</p>
              <p className="text-2xl font-bold text-red-600">{stats.stages_refuses}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card p-6">
              <h3 className="font-semibold mb-4">Répartition par statut</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={statusData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {statusData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card p-6">
              <h3 className="font-semibold mb-4">Stages par service</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={serviceData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <h3 className="font-semibold mb-4">Stages par établissement</h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={etablissementData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip formatter={(value, _, props) => [value, props.payload.fullName]} />
                  <Bar dataKey="value" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      ) : (
        <div className="card p-12 text-center">
          <p className="text-gray-500">Aucune donnée disponible pour cette année</p>
        </div>
      )}
    </div>
  );
}
