import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { etudiantsApi, stagesApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import StatusBadge from '../components/StatusBadge';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import toast from 'react-hot-toast';
import {
  ArrowLeft,
  Edit,
  Trash2,
  User,
  Mail,
  Phone,
  MapPin,
  Building2,
  Calendar,
  Briefcase,
} from 'lucide-react';

export default function EtudiantDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { hasRole } = useAuth();
  const queryClient = useQueryClient();

  const { data: etudiant, isLoading } = useQuery({
    queryKey: ['etudiant', id],
    queryFn: () => etudiantsApi.get(Number(id)),
    enabled: !!id,
  });

  const { data: stages } = useQuery({
    queryKey: ['stages', { etudiant_id: id }],
    queryFn: () => stagesApi.list({ search: etudiant?.code_egis }),
    enabled: !!etudiant?.code_egis,
  });

  const deleteMutation = useMutation({
    mutationFn: (motif: string) => etudiantsApi.delete(Number(id), motif),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['etudiants'] });
      toast.success('Étudiant supprimé');
      navigate('/etudiants');
    },
    onError: () => {
      toast.error('Erreur lors de la suppression');
    },
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (!etudiant) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Étudiant non trouvé</p>
        <Link to="/etudiants" className="text-primary-600 hover:underline mt-4 inline-block">
          Retour aux étudiants
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link to="/etudiants" className="p-2 hover:bg-gray-100 rounded-lg">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div className="flex items-center">
            <div className="h-14 w-14 rounded-full bg-primary-100 flex items-center justify-center mr-4">
              <User className="h-7 w-7 text-primary-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {etudiant.prenom} {etudiant.nom}
              </h1>
              <p className="text-primary-600 font-mono">{etudiant.code_egis}</p>
            </div>
          </div>
        </div>
        {hasRole(['coordinatrice', 'dsi']) && (
          <div className="flex items-center space-x-3">
            <Link to={`/etudiants/${id}/modifier`} className="btn btn-secondary">
              <Edit className="h-4 w-4 mr-2" />
              Modifier
            </Link>
            <button
              onClick={() => {
                if (confirm('Voulez-vous vraiment supprimer cet étudiant ?')) {
                  const motif = prompt('Motif de suppression :');
                  if (motif) deleteMutation.mutate(motif);
                }
              }}
              className="btn btn-danger"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-semibold mb-4">Informations personnelles</h2>
            <dl className="grid grid-cols-2 gap-4">
              <div>
                <dt className="text-sm text-gray-500 flex items-center">
                  <User className="h-4 w-4 mr-1" />
                  Nom complet
                </dt>
                <dd className="font-medium">
                  {etudiant.prenom} {etudiant.nom}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500 flex items-center">
                  <Calendar className="h-4 w-4 mr-1" />
                  Date de naissance
                </dt>
                <dd>
                  {etudiant.date_naissance
                    ? format(new Date(etudiant.date_naissance), 'dd MMMM yyyy', { locale: fr })
                    : '-'}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500 flex items-center">
                  <MapPin className="h-4 w-4 mr-1" />
                  Lieu de naissance
                </dt>
                <dd>{etudiant.lieu_naissance || '-'}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500 flex items-center">
                  <Mail className="h-4 w-4 mr-1" />
                  Email
                </dt>
                <dd>{etudiant.email || '-'}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500 flex items-center">
                  <Phone className="h-4 w-4 mr-1" />
                  Téléphone
                </dt>
                <dd>{etudiant.telephone || '-'}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500 flex items-center">
                  <MapPin className="h-4 w-4 mr-1" />
                  Adresse
                </dt>
                <dd>{etudiant.adresse || '-'}</dd>
              </div>
            </dl>
          </div>

          <div className="card p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center">
              <Briefcase className="h-5 w-5 mr-2 text-gray-500" />
              Historique des stages
            </h2>
            {stages && stages.length > 0 ? (
              <div className="space-y-3">
                {stages.map((stage) => (
                  <Link
                    key={stage.id}
                    to={`/stages/${stage.id}`}
                    className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{stage.service?.nom_service}</p>
                        <p className="text-sm text-gray-600">
                          {format(new Date(stage.date_debut), 'dd/MM/yyyy')} -{' '}
                          {format(new Date(stage.date_fin), 'dd/MM/yyyy')}
                        </p>
                      </div>
                      <StatusBadge status={stage.statut} />
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">Aucun stage enregistré</p>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center">
              <Building2 className="h-5 w-5 mr-2 text-gray-500" />
              Formation
            </h2>
            <p className="font-medium">{etudiant.formation || '-'}</p>
            {etudiant.etablissement && (
              <div className="mt-4 pt-4 border-t">
                <p className="text-sm text-gray-500">Établissement</p>
                <p className="font-medium">{etudiant.etablissement.nom}</p>
                <p className="text-sm text-gray-600">{etudiant.etablissement.adresse}</p>
                <p className="text-sm text-gray-600">
                  {etudiant.etablissement.code_postal} {etudiant.etablissement.ville}
                </p>
              </div>
            )}
          </div>

          {etudiant.representant_legal && (
            <div className="card p-6">
              <h2 className="text-lg font-semibold mb-4">Représentant légal</h2>
              <p className="font-medium">
                {etudiant.representant_legal.prenom} {etudiant.representant_legal.nom}
              </p>
              {etudiant.representant_legal.email && (
                <p className="text-sm text-gray-600 flex items-center mt-2">
                  <Mail className="h-4 w-4 mr-1" />
                  {etudiant.representant_legal.email}
                </p>
              )}
              {etudiant.representant_legal.telephone && (
                <p className="text-sm text-gray-600 flex items-center mt-1">
                  <Phone className="h-4 w-4 mr-1" />
                  {etudiant.representant_legal.telephone}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
