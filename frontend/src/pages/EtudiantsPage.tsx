import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { etudiantsApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { Search, Plus, User } from 'lucide-react';

export default function EtudiantsPage() {
  const { hasRole } = useAuth();
  const [search, setSearch] = useState('');

  const { data: etudiants, isLoading } = useQuery({
    queryKey: ['etudiants', search],
    queryFn: () => etudiantsApi.list({ search: search || undefined }),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Étudiants</h1>
        {hasRole(['coordinatrice', 'dsi']) && (
          <Link to="/etudiants/nouveau" className="btn btn-primary flex items-center">
            <Plus className="mr-2 h-5 w-5" />
            Nouvel étudiant
          </Link>
        )}
      </div>

      <div className="card p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Rechercher par nom, prénom ou code EGIS..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input pl-10"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading ? (
          <div className="col-span-full flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
          </div>
        ) : etudiants && etudiants.length > 0 ? (
          etudiants.map((etudiant) => (
            <Link
              key={etudiant.id}
              to={`/etudiants/${etudiant.id}`}
              className="card p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start">
                <div className="h-12 w-12 rounded-full bg-primary-100 flex items-center justify-center">
                  <User className="h-6 w-6 text-primary-600" />
                </div>
                <div className="ml-4 flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">
                    {etudiant.prenom} {etudiant.nom}
                  </p>
                  <p className="text-sm text-primary-600 font-mono">{etudiant.code_egis}</p>
                  {etudiant.formation && (
                    <p className="text-sm text-gray-500 truncate">{etudiant.formation}</p>
                  )}
                  {etudiant.etablissement && (
                    <p className="text-xs text-gray-400 truncate mt-1">
                      {etudiant.etablissement.nom}
                    </p>
                  )}
                </div>
              </div>
            </Link>
          ))
        ) : (
          <div className="col-span-full text-center py-12">
            <User className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">Aucun étudiant trouvé</p>
          </div>
        )}
      </div>
    </div>
  );
}
