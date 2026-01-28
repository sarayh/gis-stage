import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { stagesApi, rapportsApi } from '../services/api';
import StatusBadge from '../components/StatusBadge';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

export default function DashboardPage() {
  const { user } = useAuth();
  const currentYear = new Date().getFullYear();

  const { data: stats } = useQuery({
    queryKey: ['stats', currentYear],
    queryFn: () => rapportsApi.getStatistiquesAnnuelles(currentYear),
  });

  const { data: stagesEnCours } = useQuery({
    queryKey: ['stages', 'en_cours', user?.service_id],
    queryFn: () => stagesApi.list({
      statut: 'en_cours',
      service_id: user?.role === 'cadre' ? user.service_id || undefined : undefined,
      page_size: 10
    }),
  });

  const totalAcceptes = stats?.stages_acceptes || 0;
  const totalRefuses = stats?.stages_refuses || 0;
  const total = stats?.total_stages || 0;
  const pourcentageAcceptes = total > 0 ? Math.round((totalAcceptes / total) * 100) : 0;
  const pourcentageRefuses = total > 0 ? Math.round((totalRefuses / total) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Activité des stages */}
      <div className="card p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-6">Activité des stages</h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Total de stages */}
          <div className="border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-500 mb-1">Total de stages</p>
            <p className="text-3xl font-bold text-gray-900">{stats?.total_stages || 0}</p>
          </div>

          {/* Total de stages en cours */}
          <div className="border-2 border-blue-400 bg-blue-50 rounded-lg p-4">
            <p className="text-sm text-blue-600 mb-1">Total de stages en cours</p>
            <p className="text-3xl font-bold text-blue-600">{stats?.stages_en_cours || 0}</p>
          </div>

          {/* Total de stages acceptés */}
          <div className="border-2 border-green-400 bg-green-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-600 mb-1">Total de stages acceptés</p>
                <p className="text-3xl font-bold text-green-600">{totalAcceptes}</p>
              </div>
              <div className="relative w-14 h-14">
                <svg className="w-14 h-14 transform -rotate-90">
                  <circle
                    cx="28"
                    cy="28"
                    r="24"
                    stroke="#e5e7eb"
                    strokeWidth="4"
                    fill="none"
                  />
                  <circle
                    cx="28"
                    cy="28"
                    r="24"
                    stroke="#22c55e"
                    strokeWidth="4"
                    fill="none"
                    strokeDasharray={`${pourcentageAcceptes * 1.51} 151`}
                  />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-xs font-semibold text-green-600">
                  {pourcentageAcceptes}%
                </span>
              </div>
            </div>
          </div>

          {/* Total de stages refusés */}
          <div className="border-2 border-red-400 bg-red-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-600 mb-1">Total de stages refusés</p>
                <p className="text-3xl font-bold text-red-600">{totalRefuses}</p>
              </div>
              <div className="relative w-14 h-14">
                <svg className="w-14 h-14 transform -rotate-90">
                  <circle
                    cx="28"
                    cy="28"
                    r="24"
                    stroke="#e5e7eb"
                    strokeWidth="4"
                    fill="none"
                  />
                  <circle
                    cx="28"
                    cy="28"
                    r="24"
                    stroke="#ef4444"
                    strokeWidth="4"
                    fill="none"
                    strokeDasharray={`${pourcentageRefuses * 1.51} 151`}
                  />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-xs font-semibold text-red-600">
                  {pourcentageRefuses}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Aperçu des étudiants en stage */}
      <div className="card p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-6">
          Aperçu des étudiants en stage {user?.role === 'cadre' ? 'dans votre service' : ''}
        </h2>

        {stagesEnCours && stagesEnCours.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="table-header">Code</th>
                  <th className="table-header">Nom et Prénom</th>
                  <th className="table-header">Service</th>
                  <th className="table-header">Période</th>
                  <th className="table-header">Statut</th>
                  <th className="table-header">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {stagesEnCours.map((stage) => (
                  <tr key={stage.id} className="hover:bg-gray-50">
                    <td className="table-cell font-mono text-primary-600">
                      {stage.etudiant?.code_egis}
                    </td>
                    <td className="table-cell">
                      <div className="font-medium text-gray-900">
                        {stage.etudiant?.nom} {stage.etudiant?.prenom}
                      </div>
                      <div className="text-sm text-gray-500">
                        {stage.etudiant?.email}
                      </div>
                    </td>
                    <td className="table-cell text-gray-600">
                      {stage.service?.nom_service}
                    </td>
                    <td className="table-cell text-gray-600">
                      Du {format(new Date(stage.date_debut), 'dd/MM/yyyy', { locale: fr })}
                      <br />
                      au {format(new Date(stage.date_fin), 'dd/MM/yyyy', { locale: fr })}
                    </td>
                    <td className="table-cell">
                      <StatusBadge status={stage.statut} />
                    </td>
                    <td className="table-cell">
                      <Link
                        to={`/stages/${stage.id}`}
                        className="text-primary-600 hover:text-primary-700 font-medium"
                      >
                        Voir
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500">
            Aucun étudiant trouvé
          </div>
        )}
      </div>
    </div>
  );
}
