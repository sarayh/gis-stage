import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { stagesApi, documentsApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import StatusBadge from '../components/StatusBadge';
import { StatutStage } from '../types';
import toast from 'react-hot-toast';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import {
  ArrowLeft,
  Edit,
  Trash2,
  FileText,
  Upload,
  Download,
  CheckCircle,
  XCircle,
  User,
  Building2,
  Calendar,
  Phone,
  Mail,
} from 'lucide-react';
import { useState, useRef } from 'react';

const statusTransitions: Record<StatutStage, { next: StatutStage; label: string }[]> = {
  brouillon: [
    { next: 'valide', label: 'Valider' },
    { next: 'refuse', label: 'Refuser' },
  ],
  valide: [
    { next: 'conventionne', label: 'Conventionner' },
    { next: 'annule', label: 'Annuler' },
  ],
  conventionne: [
    { next: 'en_cours', label: 'Démarrer' },
    { next: 'annule', label: 'Annuler' },
  ],
  en_cours: [
    { next: 'termine', label: 'Terminer' },
    { next: 'annule', label: 'Annuler' },
  ],
  termine: [],
  annule: [{ next: 'brouillon', label: 'Réactiver' }],
  refuse: [{ next: 'brouillon', label: 'Réexaminer' }],
};

export default function StageDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { hasRole } = useAuth();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadType, setUploadType] = useState('convention');
  const [refusMotif, setRefusMotif] = useState('');
  const [showRefusModal, setShowRefusModal] = useState(false);

  const { data: stage, isLoading } = useQuery({
    queryKey: ['stage', id],
    queryFn: () => stagesApi.get(Number(id)),
    enabled: !!id,
  });

  const { data: documents } = useQuery({
    queryKey: ['documents', id],
    queryFn: () => documentsApi.listByStage(Number(id)),
    enabled: !!id,
  });

  const updateMutation = useMutation({
    mutationFn: (data: { statut: StatutStage; motif_refus?: string }) =>
      stagesApi.update(Number(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stage', id] });
      toast.success('Statut mis à jour');
    },
    onError: () => {
      toast.error('Erreur lors de la mise à jour');
    },
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => documentsApi.upload(Number(id), uploadType, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', id] });
      toast.success('Document uploadé');
    },
    onError: () => {
      toast.error('Erreur lors de l\'upload');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (motif: string) => stagesApi.delete(Number(id), motif),
    onSuccess: () => {
      toast.success('Stage supprimé');
      navigate('/stages');
    },
    onError: () => {
      toast.error('Erreur lors de la suppression');
    },
  });

  const handleStatusChange = (newStatus: StatutStage) => {
    if (newStatus === 'refuse') {
      setShowRefusModal(true);
    } else {
      updateMutation.mutate({ statut: newStatus });
    }
  };

  const handleRefus = () => {
    if (!refusMotif.trim()) {
      toast.error('Le motif de refus est obligatoire');
      return;
    }
    updateMutation.mutate({ statut: 'refuse', motif_refus: refusMotif });
    setShowRefusModal(false);
    setRefusMotif('');
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        toast.error('Fichier trop volumineux (max 5 Mo)');
        return;
      }
      uploadMutation.mutate(file);
    }
  };

  const handleDownload = async (docId: number, filename: string) => {
    try {
      const blob = await documentsApi.download(docId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      toast.error('Erreur lors du téléchargement');
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (!stage) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Stage non trouvé</p>
        <Link to="/stages" className="text-primary-600 hover:underline mt-4 inline-block">
          Retour aux stages
        </Link>
      </div>
    );
  }

  const transitions = statusTransitions[stage.statut] || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link to="/stages" className="p-2 hover:bg-gray-100 rounded-lg">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Stage de {stage.etudiant?.prenom} {stage.etudiant?.nom}
            </h1>
            <p className="text-gray-600">{stage.etudiant?.code_egis}</p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <StatusBadge status={stage.statut} />
          {hasRole(['coordinatrice', 'dsi']) && stage.statut !== 'termine' && (
            <>
              <Link to={`/stages/${id}/modifier`} className="btn btn-secondary">
                <Edit className="h-4 w-4 mr-2" />
                Modifier
              </Link>
              <button
                onClick={() => {
                  if (confirm('Voulez-vous vraiment supprimer ce stage ?')) {
                    const motif = prompt('Motif de suppression :');
                    if (motif) deleteMutation.mutate(motif);
                  }
                }}
                className="btn btn-danger"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </>
          )}
        </div>
      </div>

      {hasRole(['coordinatrice', 'dsi']) && transitions.length > 0 && (
        <div className="card p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Actions disponibles</h3>
          <div className="flex flex-wrap gap-2">
            {transitions.map((t) => (
              <button
                key={t.next}
                onClick={() => handleStatusChange(t.next)}
                disabled={updateMutation.isPending}
                className={`btn ${
                  t.next === 'refuse' || t.next === 'annule'
                    ? 'btn-danger'
                    : 'btn-success'
                }`}
              >
                {t.next === 'refuse' || t.next === 'annule' ? (
                  <XCircle className="h-4 w-4 mr-2" />
                ) : (
                  <CheckCircle className="h-4 w-4 mr-2" />
                )}
                {t.label}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center">
              <User className="h-5 w-5 mr-2 text-gray-500" />
              Informations étudiant
            </h2>
            <dl className="grid grid-cols-2 gap-4">
              <div>
                <dt className="text-sm text-gray-500">Nom complet</dt>
                <dd className="font-medium">
                  {stage.etudiant?.prenom} {stage.etudiant?.nom}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Code EGIS</dt>
                <dd className="font-medium">{stage.etudiant?.code_egis}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Email</dt>
                <dd className="flex items-center">
                  <Mail className="h-4 w-4 mr-1 text-gray-400" />
                  {stage.etudiant?.email || '-'}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Téléphone</dt>
                <dd className="flex items-center">
                  <Phone className="h-4 w-4 mr-1 text-gray-400" />
                  {stage.etudiant?.telephone || '-'}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Formation</dt>
                <dd>{stage.formation || stage.etudiant?.formation || '-'}</dd>
              </div>
            </dl>
            <Link
              to={`/etudiants/${stage.etudiant_id}`}
              className="text-primary-600 hover:underline text-sm mt-4 inline-block"
            >
              Voir le dossier complet
            </Link>
          </div>

          <div className="card p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center">
              <Calendar className="h-5 w-5 mr-2 text-gray-500" />
              Informations du stage
            </h2>
            <dl className="grid grid-cols-2 gap-4">
              <div>
                <dt className="text-sm text-gray-500">Service</dt>
                <dd className="font-medium">{stage.service?.nom_service}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Durée</dt>
                <dd>{stage.nombre_semaines} semaines</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Date de début</dt>
                <dd>{format(new Date(stage.date_debut), 'dd MMMM yyyy', { locale: fr })}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Date de fin</dt>
                <dd>{format(new Date(stage.date_fin), 'dd MMMM yyyy', { locale: fr })}</dd>
              </div>
              {stage.motif_refus && (
                <div className="col-span-2">
                  <dt className="text-sm text-gray-500">Motif de refus</dt>
                  <dd className="text-red-600">{stage.motif_refus}</dd>
                </div>
              )}
              {stage.commentaire && (
                <div className="col-span-2">
                  <dt className="text-sm text-gray-500">Commentaire</dt>
                  <dd>{stage.commentaire}</dd>
                </div>
              )}
            </dl>
          </div>
        </div>

        <div className="space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center">
              <Building2 className="h-5 w-5 mr-2 text-gray-500" />
              Établissement
            </h2>
            <p className="font-medium">{stage.etablissement?.nom}</p>
            <p className="text-sm text-gray-600">{stage.etablissement?.adresse}</p>
            <p className="text-sm text-gray-600">
              {stage.etablissement?.code_postal} {stage.etablissement?.ville}
            </p>
          </div>

          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold flex items-center">
                <FileText className="h-5 w-5 mr-2 text-gray-500" />
                Documents
              </h2>
              {hasRole(['coordinatrice', 'dsi']) && (
                <div className="flex items-center space-x-2">
                  <select
                    value={uploadType}
                    onChange={(e) => setUploadType(e.target.value)}
                    className="input text-sm py-1"
                  >
                    <option value="convention">Convention</option>
                    <option value="evaluation">Évaluation</option>
                    <option value="vaccination">Vaccination</option>
                    <option value="attestation">Attestation</option>
                    <option value="autre">Autre</option>
                  </select>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="btn btn-primary btn-sm"
                  >
                    <Upload className="h-4 w-4" />
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden"
                    onChange={handleFileUpload}
                    accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                  />
                </div>
              )}
            </div>
            <div className="space-y-2">
              {documents && documents.length > 0 ? (
                documents.map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center justify-between p-2 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center">
                      <FileText className="h-4 w-4 text-gray-400 mr-2" />
                      <span className="text-sm truncate max-w-[150px]">{doc.nom_document}</span>
                    </div>
                    <button
                      onClick={() => handleDownload(doc.id, doc.nom_document)}
                      className="p-1 hover:bg-gray-200 rounded"
                    >
                      <Download className="h-4 w-4 text-gray-600" />
                    </button>
                  </div>
                ))
              ) : (
                <p className="text-sm text-gray-500 text-center py-4">Aucun document</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {showRefusModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Motif de refus</h3>
            <textarea
              value={refusMotif}
              onChange={(e) => setRefusMotif(e.target.value)}
              className="input h-32"
              placeholder="Saisissez le motif de refus..."
            />
            <div className="flex justify-end space-x-3 mt-4">
              <button
                onClick={() => setShowRefusModal(false)}
                className="btn btn-secondary"
              >
                Annuler
              </button>
              <button onClick={handleRefus} className="btn btn-danger">
                Confirmer le refus
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
