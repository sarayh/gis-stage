import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { stagesApi, servicesApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import StatusBadge from '../components/StatusBadge';
import { StatutStage } from '../types';
import { Search, Plus, Filter } from 'lucide-react';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

const statusOptions: { value: StatutStage | ''; label: string }[] = [
  { value: '', label: 'Tous les statuts' },
  { value: 'brouillon', label: 'Brouillon' },
  { value: 'valide', label: 'Validé' },
  { value: 'conventionne', label: 'Conventionné' },
  { value: 'en_cours', label: 'En cours' },
  { value: 'termine', label: 'Terminé' },
  { value: 'annule', label: 'Annulé' },
  { value: 'refuse', label: 'Refusé' },
];

export default function StagesPage() {
  const { hasRole } = useAuth();
  const [search, setSearch] = useState('');
  const [serviceId, setServiceId] = useState<number | ''>('');
  const [statut, setStatut] = useState<StatutStage | ''>('');
  const [showFilters, setShowFilters] = useState(false);

  const { data: stages, isLoading } = useQuery({
    queryKey: ['stages', { search, serviceId, statut }],
    queryFn: () =>
      stagesApi.list({
        search: search || undefined,
        service_id: serviceId || undefined,
        statut: statut || undefined,
      }),
  });

  const { data: services } = useQuery({
    queryKey: ['services'],
    queryFn: () => servicesApi.list(),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Stages</h1>
        {hasRole(['coordinatrice', 'dsi']) && (
          <Link to="/stages/nouveau" className="btn btn-primary flex items-center">
            <Plus className="mr-2 h-5 w-5" />
            Nouveau stage
          </Link>
        )}
      </div>

      <div className="card p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Rechercher un étudiant (nom, prénom, code EGIS)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input pl-10"
            />
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="btn btn-secondary flex items-center md:hidden"
          >
            <Filter className="mr-2 h-5 w-5" />
            Filtres
          </button>
          <div className={`flex flex-col md:flex-row gap-4 ${showFilters ? '' : 'hidden md:flex'}`}>
            <select
              value={serviceId}
              onChange={(e) => setServiceId(e.target.value ? Number(e.target.value) : '')}
              className="input"
            >
              <option value="">Tous les services</option>
              {services?.map((service) => (
                <option key={service.id} value={service.id}>
                  {service.nom_service}
                </option>
              ))}
            </select>
            <select
              value={statut}
              onChange={(e) => setStatut(e.target.value as StatutStage | '')}
              className="input"
            >
              {statusOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="table-header">Étudiant</th>
                <th className="table-header">Établissement</th>
                <th className="table-header">Service</th>
                <th className="table-header">Période</th>
                <th className="table-header">Statut</th>
                <th className="table-header">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="table-cell text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto" />
                  </td>
                </tr>
              ) : stages && stages.length > 0 ? (
                stages.map((stage) => (
                  <tr key={stage.id} className="hover:bg-gray-50">
                    <td className="table-cell">
                      <div>
                        <div className="font-medium text-gray-900">
                          {stage.etudiant?.prenom} {stage.etudiant?.nom}
                        </div>
                        <div className="text-gray-500 text-xs">
                          {stage.etudiant?.code_egis}
                        </div>
                      </div>
                    </td>
                    <td className="table-cell text-gray-600">
                      {stage.etudiant?.etablissement?.nom}
                    </td>
                    <td className="table-cell text-gray-600">
                      {stage.service?.nom_service}
                    </td>
                    <td className="table-cell text-gray-600">
                      <div>
                        {format(new Date(stage.date_debut), 'dd/MM/yyyy', { locale: fr })}
                      </div>
                      <div className="text-xs text-gray-500">
                        au {format(new Date(stage.date_fin), 'dd/MM/yyyy', { locale: fr })}
                      </div>
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
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="table-cell text-center text-gray-500">
                    Aucun stage trouvé
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
