import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { stagesApi, etudiantsApi, servicesApi, etablissementsApi } from '../services/api';
import toast from 'react-hot-toast';
import { ArrowLeft, Save } from 'lucide-react';

const stageSchema = z.object({
  etudiant_id: z.number({ required_error: 'Étudiant requis' }),
  service_id: z.number({ required_error: 'Service requis' }),
  etablissement_id: z.number({ required_error: 'Établissement requis' }),
  formation: z.string().optional(),
  date_debut: z.string().min(1, 'Date de début requise'),
  date_fin: z.string().min(1, 'Date de fin requise'),
  commentaire: z.string().optional(),
  statut: z.enum(['brouillon', 'valide', 'refuse']).default('brouillon'),
});

type StageForm = z.infer<typeof stageSchema>;

export default function StageFormPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isEditing = !!id;

  const { data: stage, isLoading: stageLoading } = useQuery({
    queryKey: ['stage', id],
    queryFn: () => stagesApi.get(Number(id)),
    enabled: isEditing,
  });

  const { data: etudiants } = useQuery({
    queryKey: ['etudiants'],
    queryFn: () => etudiantsApi.list({ page_size: 100 }),
  });

  const { data: services } = useQuery({
    queryKey: ['services'],
    queryFn: () => servicesApi.list(),
  });

  const { data: etablissements } = useQuery({
    queryKey: ['etablissements'],
    queryFn: () => etablissementsApi.list(),
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<StageForm>({
    resolver: zodResolver(stageSchema),
    values: stage
      ? {
          etudiant_id: stage.etudiant_id,
          service_id: stage.service_id,
          etablissement_id: stage.etablissement_id,
          formation: stage.formation || '',
          date_debut: stage.date_debut,
          date_fin: stage.date_fin,
          commentaire: stage.commentaire || '',
          statut: stage.statut as 'brouillon' | 'valide' | 'refuse',
        }
      : undefined,
  });

  const createMutation = useMutation({
    mutationFn: (data: StageForm) => stagesApi.create(data),
    onSuccess: (newStage) => {
      queryClient.invalidateQueries({ queryKey: ['stages'] });
      toast.success('Stage créé avec succès');
      navigate(`/stages/${newStage.id}`);
    },
    onError: () => {
      toast.error('Erreur lors de la création');
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: StageForm) => stagesApi.update(Number(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stages'] });
      queryClient.invalidateQueries({ queryKey: ['stage', id] });
      toast.success('Stage mis à jour');
      navigate(`/stages/${id}`);
    },
    onError: () => {
      toast.error('Erreur lors de la mise à jour');
    },
  });

  const onSubmit = (data: StageForm) => {
    if (isEditing) {
      updateMutation.mutate(data);
    } else {
      createMutation.mutate(data);
    }
  };

  if (isEditing && stageLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center space-x-4 mb-6">
        <Link to="/stages" className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">
          {isEditing ? 'Modifier le stage' : 'Nouveau stage'}
        </h1>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="card p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="label">Étudiant *</label>
            <select
              {...register('etudiant_id', { valueAsNumber: true })}
              className={`input ${errors.etudiant_id ? 'input-error' : ''}`}
              disabled={isEditing}
            >
              <option value="">Sélectionner un étudiant</option>
              {etudiants?.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.prenom} {e.nom} ({e.code_egis})
                </option>
              ))}
            </select>
            {errors.etudiant_id && (
              <p className="mt-1 text-sm text-red-600">{errors.etudiant_id.message}</p>
            )}
          </div>

          <div>
            <label className="label">Établissement *</label>
            <select
              {...register('etablissement_id', { valueAsNumber: true })}
              className={`input ${errors.etablissement_id ? 'input-error' : ''}`}
            >
              <option value="">Sélectionner un établissement</option>
              {etablissements?.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.nom}
                </option>
              ))}
            </select>
            {errors.etablissement_id && (
              <p className="mt-1 text-sm text-red-600">{errors.etablissement_id.message}</p>
            )}
          </div>

          <div>
            <label className="label">Service *</label>
            <select
              {...register('service_id', { valueAsNumber: true })}
              className={`input ${errors.service_id ? 'input-error' : ''}`}
            >
              <option value="">Sélectionner un service</option>
              {services?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nom_service}
                </option>
              ))}
            </select>
            {errors.service_id && (
              <p className="mt-1 text-sm text-red-600">{errors.service_id.message}</p>
            )}
          </div>

          <div>
            <label className="label">Formation</label>
            <input
              type="text"
              {...register('formation')}
              className="input"
              placeholder="Ex: Infirmier, Aide-soignant..."
            />
          </div>

          <div>
            <label className="label">Date de début *</label>
            <input
              type="date"
              {...register('date_debut')}
              className={`input ${errors.date_debut ? 'input-error' : ''}`}
            />
            {errors.date_debut && (
              <p className="mt-1 text-sm text-red-600">{errors.date_debut.message}</p>
            )}
          </div>

          <div>
            <label className="label">Date de fin *</label>
            <input
              type="date"
              {...register('date_fin')}
              className={`input ${errors.date_fin ? 'input-error' : ''}`}
            />
            {errors.date_fin && (
              <p className="mt-1 text-sm text-red-600">{errors.date_fin.message}</p>
            )}
          </div>

          {!isEditing && (
            <div>
              <label className="label">Statut initial</label>
              <select {...register('statut')} className="input">
                <option value="brouillon">Brouillon</option>
                <option value="valide">Validé</option>
                <option value="refuse">Refusé</option>
              </select>
            </div>
          )}
        </div>

        <div>
          <label className="label">Commentaire</label>
          <textarea
            {...register('commentaire')}
            className="input h-24"
            placeholder="Informations complémentaires..."
          />
        </div>

        <div className="flex justify-end space-x-3 pt-4 border-t">
          <Link to="/stages" className="btn btn-secondary">
            Annuler
          </Link>
          <button
            type="submit"
            disabled={createMutation.isPending || updateMutation.isPending}
            className="btn btn-primary"
          >
            <Save className="h-4 w-4 mr-2" />
            {isEditing ? 'Enregistrer' : 'Créer le stage'}
          </button>
        </div>
      </form>
    </div>
  );
}
