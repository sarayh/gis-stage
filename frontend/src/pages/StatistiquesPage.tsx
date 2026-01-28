import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { rapportsApi } from '../services/api';
import { Download } from 'lucide-react';
import toast from 'react-hot-toast';

export default function StatistiquesPage() {
  const currentYear = new Date().getFullYear();
  const [selectedYear, setSelectedYear] = useState(currentYear);
  const [activeTab, setActiveTab] = useState<'rapport' | 'previsionnel'>('rapport');

  const { data: rapportServices, isLoading: loadingRapport } = useQuery({
    queryKey: ['rapport-services', selectedYear],
    queryFn: () => rapportsApi.getRapportServices(selectedYear),
    enabled: activeTab === 'rapport',
  });

  const { data: rapportPrevisionnel, isLoading: loadingPrevisionnel } = useQuery({
    queryKey: ['rapport-previsionnel', selectedYear],
    queryFn: () => rapportsApi.getRapportPrevisionnel(selectedYear),
    enabled: activeTab === 'previsionnel',
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

  const years = Array.from({ length: 5 }, (_, i) => currentYear - i + 1);

  const totaux = rapportServices?.reduce(
    (acc, service) => ({
      total: acc.total + service.total,
      acceptes: acc.acceptes + service.acceptes,
      refuses: acc.refuses + service.refuses,
      en_attente: acc.en_attente + service.en_attente,
    }),
    { total: 0, acceptes: 0, refuses: 0, en_attente: 0 }
  );

  const tauxGlobal = totaux && totaux.total > 0
    ? Math.round((totaux.acceptes / totaux.total) * 100)
    : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Statistiques & Rapports</h1>
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

      {/* Onglets */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
        <button
          onClick={() => setActiveTab('rapport')}
          className={`px-6 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'rapport'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Rapport
        </button>
        <button
          onClick={() => setActiveTab('previsionnel')}
          className={`px-6 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'previsionnel'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Rapport Prévisionnel
        </button>
      </div>

      {/* Contenu des onglets */}
      {activeTab === 'rapport' && (
        <div className="card">
          <div className="p-6 border-b">
            <h2 className="text-lg font-semibold text-gray-800">
              Rapport des services - Année {selectedYear}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Statistiques détaillées par service
            </p>
          </div>

          {loadingRapport ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
            </div>
          ) : rapportServices && rapportServices.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="table-header">Service</th>
                    <th className="table-header text-center">Total</th>
                    <th className="table-header text-center">Acceptés</th>
                    <th className="table-header text-center">Refusés</th>
                    <th className="table-header text-center">En attente</th>
                    <th className="table-header text-center">Taux d'acceptation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {rapportServices.map((service) => (
                    <tr key={service.service_id} className="hover:bg-gray-50">
                      <td className="table-cell font-medium text-gray-900">
                        {service.service_nom}
                      </td>
                      <td className="table-cell text-center">
                        <span className="inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                          {service.total}
                        </span>
                      </td>
                      <td className="table-cell text-center">
                        <span className="inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-sm font-medium bg-green-100 text-green-800">
                          {service.acceptes}
                        </span>
                      </td>
                      <td className="table-cell text-center">
                        <span className="inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-sm font-medium bg-red-100 text-red-800">
                          {service.refuses}
                        </span>
                      </td>
                      <td className="table-cell text-center">
                        <span className="inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
                          {service.en_attente}
                        </span>
                      </td>
                      <td className="table-cell text-center">
                        <div className="flex items-center justify-center">
                          <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                            <div
                              className="bg-green-500 h-2 rounded-full"
                              style={{ width: `${service.taux_acceptation}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium text-gray-700">
                            {service.taux_acceptation}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
                {totaux && (
                  <tfoot className="bg-gray-100 font-semibold">
                    <tr>
                      <td className="table-cell text-gray-900">Total</td>
                      <td className="table-cell text-center">
                        <span className="inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-sm font-bold bg-gray-200 text-gray-900">
                          {totaux.total}
                        </span>
                      </td>
                      <td className="table-cell text-center">
                        <span className="inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-sm font-bold bg-green-200 text-green-900">
                          {totaux.acceptes}
                        </span>
                      </td>
                      <td className="table-cell text-center">
                        <span className="inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-sm font-bold bg-red-200 text-red-900">
                          {totaux.refuses}
                        </span>
                      </td>
                      <td className="table-cell text-center">
                        <span className="inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-sm font-bold bg-yellow-200 text-yellow-900">
                          {totaux.en_attente}
                        </span>
                      </td>
                      <td className="table-cell text-center">
                        <span className="text-sm font-bold text-gray-900">
                          {tauxGlobal}%
                        </span>
                      </td>
                    </tr>
                  </tfoot>
                )}
              </table>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              Aucune donnée disponible pour cette année
            </div>
          )}
        </div>
      )}

      {activeTab === 'previsionnel' && (
        <div className="card">
          <div className="p-6 border-b">
            <h2 className="text-lg font-semibold text-gray-800">
              Rapport Prévisionnel - Année {selectedYear}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Stages planifiés et en attente de validation par service
            </p>
          </div>

          {loadingPrevisionnel ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
            </div>
          ) : rapportPrevisionnel && rapportPrevisionnel.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="table-header">Service</th>
                    <th className="table-header text-center">Stages planifiés</th>
                    <th className="table-header text-center">En attente de validation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {rapportPrevisionnel.map((service) => (
                    <tr key={service.service_id} className="hover:bg-gray-50">
                      <td className="table-cell font-medium text-gray-900">
                        {service.service_nom}
                      </td>
                      <td className="table-cell text-center">
                        <span className="inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                          {service.stages_planifies}
                        </span>
                      </td>
                      <td className="table-cell text-center">
                        <span className="inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
                          {service.en_attente_validation}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              Aucune donnée prévisionnelle pour cette année
            </div>
          )}
        </div>
      )}
    </div>
  );
}
