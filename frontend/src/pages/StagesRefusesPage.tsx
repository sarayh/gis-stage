import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { rapportsApi } from '../services/api';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { Eye, Search, XCircle } from 'lucide-react';
import { StageRefuse } from '../types';

export default function StagesRefusesPage() {
  const currentYear = new Date().getFullYear();
  const [selectedYear, setSelectedYear] = useState(currentYear);
  const [searchTerm, setSearchTerm] = useState('');

  const { data: stages, isLoading } = useQuery({
    queryKey: ['stages-refuses', selectedYear],
    queryFn: () => rapportsApi.getStagesRefuses(selectedYear),
  });

  const years = Array.from({ length: 5 }, (_, i) => currentYear - i + 1);

  const filteredStages = stages?.filter(
    (stage: StageRefuse) =>
      stage.nom.toLowerCase().includes(searchTerm.toLowerCase()) ||
      stage.prenom.toLowerCase().includes(searchTerm.toLowerCase()) ||
      stage.code_egis.toLowerCase().includes(searchTerm.toLowerCase()) ||
      stage.service.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Liste des stages refusés</h1>
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
      </div>

      <div className="card">
        <div className="p-4 border-b">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Rechercher par nom, prénom, code EGIS ou service..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-10 w-full"
            />
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
                  <th className="table-header">Période demandée</th>
                  <th className="table-header">Motif de refus</th>
                  <th className="table-header">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredStages.map((stage: StageRefuse) => (
                  <tr key={stage.id} className="hover:bg-gray-50">
                    <td className="table-cell font-mono text-primary-600">
                      {stage.code_egis}
                    </td>
                    <td className="table-cell">
                      <div className="font-medium text-gray-900">
                        {stage.nom} {stage.prenom}
                      </div>
                      <div className="text-sm text-gray-500">{stage.email}</div>
                    </td>
                    <td className="table-cell text-gray-600">{stage.service}</td>
                    <td className="table-cell text-gray-600">
                      Du {format(new Date(stage.date_debut), 'dd/MM/yyyy', { locale: fr })}
                      <br />
                      au {format(new Date(stage.date_fin), 'dd/MM/yyyy', { locale: fr })}
                    </td>
                    <td className="table-cell">
                      <div className="flex items-start">
                        <XCircle className="h-4 w-4 text-red-500 mr-2 mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-red-700">
                          {stage.motif_refus || 'Non spécifié'}
                        </span>
                      </div>
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
            Aucun stage refusé trouvé pour {selectedYear}
          </div>
        )}

        {filteredStages && (
          <div className="p-4 border-t bg-gray-50 text-sm text-gray-600">
            {filteredStages.length} stage{filteredStages.length > 1 ? 's' : ''} refusé{filteredStages.length > 1 ? 's' : ''}
          </div>
        )}
      </div>
    </div>
  );
}
