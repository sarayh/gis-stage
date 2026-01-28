import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { stagesApi } from '../services/api';
import StatusBadge from '../components/StatusBadge';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { Eye, Search, Filter } from 'lucide-react';

export default function HistoriquePage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatut, setSelectedStatut] = useState<string>('');
  const [selectedYear, setSelectedYear] = useState<number | ''>('');

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 10 }, (_, i) => currentYear - i);

  const { data: stages, isLoading } = useQuery({
    queryKey: ['historique-stages'],
    queryFn: () => stagesApi.list({ page_size: 500 }),
  });

  // Filtrer uniquement les stages terminés ou annulés
  const historicStages = stages?.filter(
    (stage) => stage.statut === 'termine' || stage.statut === 'annule'
  );

  const filteredStages = historicStages?.filter((stage) => {
    const matchSearch =
      !searchTerm ||
      stage.etudiant?.nom.toLowerCase().includes(searchTerm.toLowerCase()) ||
      stage.etudiant?.prenom.toLowerCase().includes(searchTerm.toLowerCase()) ||
      stage.etudiant?.code_egis.toLowerCase().includes(searchTerm.toLowerCase()) ||
      stage.service?.nom_service.toLowerCase().includes(searchTerm.toLowerCase());

    const matchStatut = !selectedStatut || stage.statut === selectedStatut;

    const matchYear =
      !selectedYear ||
      new Date(stage.date_debut).getFullYear() === selectedYear;

    return matchSearch && matchStatut && matchYear;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Historique des stages</h1>
      </div>

      <div className="card">
        <div className="p-4 border-b space-y-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Rechercher..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="input pl-10 w-full"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-5 w-5 text-gray-400" />
              <select
                value={selectedStatut}
                onChange={(e) => setSelectedStatut(e.target.value)}
                className="input w-40"
              >
                <option value="">Tous les statuts</option>
                <option value="termine">Terminé</option>
                <option value="annule">Annulé</option>
              </select>
              <select
                value={selectedYear}
                onChange={(e) =>
                  setSelectedYear(e.target.value ? Number(e.target.value) : '')
                }
                className="input w-32"
              >
                <option value="">Toutes les années</option>
                {years.map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
          </div>
        ) : filteredStages && filteredStages.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="table-header">Code EGIS</th>
                  <th className="table-header">Nom et Prénom</th>
                  <th className="table-header">Service</th>
                  <th className="table-header">Période</th>
                  <th className="table-header">Statut</th>
                  <th className="table-header">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredStages.map((stage) => (
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
                      Du{' '}
                      {format(new Date(stage.date_debut), 'dd/MM/yyyy', {
                        locale: fr,
                      })}
                      <br />
                      au{' '}
                      {format(new Date(stage.date_fin), 'dd/MM/yyyy', {
                        locale: fr,
                      })}
                    </td>
                    <td className="table-cell">
                      <StatusBadge status={stage.statut} />
                    </td>
                    <td className="table-cell">
                      <Link
                        to={`/stages/${stage.id}`}
                        className="inline-flex items-center text-primary-600 hover:text-primary-700"
                      >
                        <Eye className="h-4 w-4 mr-1" />
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
            Aucun stage dans l'historique
          </div>
        )}

        {filteredStages && (
          <div className="p-4 border-t bg-gray-50 text-sm text-gray-600">
            {filteredStages.length} stage{filteredStages.length > 1 ? 's' : ''} dans l'historique
          </div>
        )}
      </div>
    </div>
  );
}
