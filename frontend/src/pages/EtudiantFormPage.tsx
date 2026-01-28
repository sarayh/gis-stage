import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { etudiantsApi, etablissementsApi } from '../services/api';
import toast from 'react-hot-toast';
import { ArrowLeft, Save } from 'lucide-react';

const etudiantSchema = z.object({
  nom: z.string().min(1, 'Nom requis'),
  prenom: z.string().min(1, 'Prénom requis'),
  date_naissance: z.string().optional(),
  lieu_naissance: z.string().optional(),
  email: z.string().email('Email invalide').optional().or(z.literal('')),
  telephone: z.string().optional(),
  adresse: z.string().optional(),
  formation: z.string().optional(),
  etablissement_id: z.number().optional(),
});

type EtudiantForm = z.infer<typeof etudiantSchema>;

export default function EtudiantFormPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isEditing = !!id;

  const { data: etudiant, isLoading: etudiantLoading } = useQuery({
    queryKey: ['etudiant', id],
    queryFn: () => etudiantsApi.get(Number(id)),
    enabled: isEditing,
  });

  const { data: etablissements } = useQuery({
    queryKey: ['etablissements'],
    queryFn: () => etablissementsApi.list(),
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<EtudiantForm>({
    resolver: zodResolver(etudiantSchema),
    values: etudiant
      ? {
          nom: etudiant.nom,
          prenom: etudiant.prenom,
          date_naissance: etudiant.date_naissance || '',
          lieu_naissance: etudiant.lieu_naissance || '',
          email: etudiant.email || '',
          telephone: etudiant.telephone || '',
          adresse: etudiant.adresse || '',
          formation: etudiant.formation || '',
          etablissement_id: etudiant.etablissement_id || undefined,
        }
      : undefined,
  });

  const createMutation = useMutation({
    mutationFn: (data: EtudiantForm) => etudiantsApi.create(data),
    onSuccess: (newEtudiant) => {
      queryClient.invalidateQueries({ queryKey: ['etudiants'] });
      toast.success(`Étudiant créé - Code: ${newEtudiant.code_egis}`);
      navigate(`/etudiants/${newEtudiant.id}`);
    },
    onError: () => {
      toast.error('Erreur lors de la création');
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: EtudiantForm) => etudiantsApi.update(Number(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['etudiants'] });
      queryClient.invalidateQueries({ queryKey: ['etudiant', id] });
      toast.success('Étudiant mis à jour');
      navigate(`/etudiants/${id}`);
    },
    onError: () => {
      toast.error('Erreur lors de la mise à jour');
    },
  });

  const onSubmit = (data: EtudiantForm) => {
    const cleanData = {
      ...data,
      email: data.email || undefined,
    };
    if (isEditing) {
      updateMutation.mutate(cleanData);
    } else {
      createMutation.mutate(cleanData);
    }
  };

  if (isEditing && etudiantLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center space-x-4 mb-6">
        <Link to="/etudiants" className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">
          {isEditing ? 'Modifier l\'étudiant' : 'Nouvel étudiant'}
        </h1>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="card p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="label">Prénom *</label>
            <input
              type="text"
              {...register('prenom')}
              className={`input ${errors.prenom ? 'input-error' : ''}`}
            />
            {errors.prenom && (
              <p className="mt-1 text-sm text-red-600">{errors.prenom.message}</p>
            )}
          </div>

          <div>
            <label className="label">Nom *</label>
            <input
              type="text"
              {...register('nom')}
              className={`input ${errors.nom ? 'input-error' : ''}`}
            />
            {errors.nom && (
              <p className="mt-1 text-sm text-red-600">{errors.nom.message}</p>
            )}
          </div>

          <div>
            <label className="label">Date de naissance</label>
            <input type="date" {...register('date_naissance')} className="input" />
          </div>

          <div>
            <label className="label">Lieu de naissance</label>
            <input type="text" {...register('lieu_naissance')} className="input" />
          </div>

          <div>
            <label className="label">Email</label>
            <input
              type="email"
              {...register('email')}
              className={`input ${errors.email ? 'input-error' : ''}`}
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
            )}
          </div>

          <div>
            <label className="label">Téléphone</label>
            <input type="tel" {...register('telephone')} className="input" />
          </div>

          <div className="md:col-span-2">
            <label className="label">Adresse</label>
            <input type="text" {...register('adresse')} className="input" />
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
            <label className="label">Établissement</label>
            <select
              {...register('etablissement_id', { valueAsNumber: true })}
              className="input"
            >
              <option value="">Sélectionner un établissement</option>
              {etablissements?.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.nom}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex justify-end space-x-3 pt-4 border-t">
          <Link to="/etudiants" className="btn btn-secondary">
            Annuler
          </Link>
          <button
            type="submit"
            disabled={createMutation.isPending || updateMutation.isPending}
            className="btn btn-primary"
          >
            <Save className="h-4 w-4 mr-2" />
            {isEditing ? 'Enregistrer' : 'Créer l\'étudiant'}
          </button>
        </div>
      </form>
    </div>
  );
}
