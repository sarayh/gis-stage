export type Role = 'coordinatrice' | 'cadre' | 'dsi';

export type StatutStage =
  | 'brouillon'
  | 'valide'
  | 'conventionne'
  | 'en_cours'
  | 'termine'
  | 'annule'
  | 'refuse';

export type EtatPresence = 'present' | 'absent' | 'absent_justifie' | 'non_renseigne';

export type TypeDocument = 'convention' | 'evaluation' | 'vaccination' | 'attestation' | 'autre';

export interface User {
  id: number;
  username: string;
  email: string;
  nom: string;
  prenom: string;
  role: Role;
  service_id: number | null;
  actif: boolean;
  service?: Service;
}

export interface Service {
  id: number;
  nom_service: string;
  code: string;
  actif: boolean;
  created_at: string;
}

export interface Etablissement {
  id: number;
  nom: string;
  adresse: string;
  ville: string;
  code_postal: string;
  telephone: string;
  email: string;
  actif: boolean;
  created_at: string;
}

export interface RepresentantLegal {
  id: number;
  nom: string;
  prenom: string;
  email: string;
  telephone: string;
  adresse: string;
}

export interface EnseignantReferent {
  id: number;
  nom: string;
  prenom: string;
  telephone: string;
  email: string;
  etablissement_id: number;
  actif: boolean;
}

export interface Etudiant {
  id: number;
  code_egis: string;
  nom: string;
  prenom: string;
  date_naissance: string;
  lieu_naissance: string;
  email: string;
  telephone: string;
  adresse: string;
  formation: string;
  etablissement_id: number;
  representant_legal_id: number | null;
  actif: boolean;
  created_at: string;
  updated_at: string;
  etablissement?: Etablissement;
  representant_legal?: RepresentantLegal;
}

export interface Stage {
  id: number;
  etudiant_id: number;
  service_id: number;
  etablissement_id: number;
  enseignant_referent_id: number | null;
  formation: string;
  date_demande: string;
  date_debut: string;
  date_fin: string;
  nombre_semaines: number;
  date_rendu_dossier: string | null;
  date_finalisation_dossier: string | null;
  statut: StatutStage;
  motif_refus: string | null;
  commentaire: string;
  actif: boolean;
  created_at: string;
  updated_at: string;
  etudiant?: Etudiant;
  service?: Service;
  etablissement?: Etablissement;
  enseignant_referent?: EnseignantReferent;
}

export interface Document {
  id: number;
  stage_id: number;
  type_document: TypeDocument;
  nom_document: string;
  chemin_fichier: string;
  taille: number;
  mime_type: string;
  valide: boolean;
  created_at: string;
}

export interface Presence {
  id: number;
  stage_id: number;
  date_presence: string;
  etat: EtatPresence;
  commentaire: string;
  updated_at: string;
}

export interface StatistiquesAnnuelles {
  annee: number;
  total_stages: number;
  stages_acceptes: number;
  stages_refuses: number;
  stages_en_cours: number;
  stages_termines: number;
  stages_par_service: Record<string, number>;
  stages_par_etablissement: Record<string, number>;
  taux_acceptation: number;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
  meta: {
    correlation_id: string;
  };
}

export interface RapportService {
  service_id: number;
  service_nom: string;
  total: number;
  acceptes: number;
  refuses: number;
  en_attente: number;
  taux_acceptation: number;
}

export interface RapportPrevisionnel {
  service_id: number;
  service_nom: string;
  stages_planifies: number;
  en_attente_validation: number;
}

export interface StageAccepte {
  id: number;
  code_egis: string;
  nom: string;
  prenom: string;
  email: string;
  service: string;
  date_debut: string;
  date_fin: string;
  statut: string;
}

export interface StageRefuse {
  id: number;
  code_egis: string;
  nom: string;
  prenom: string;
  email: string;
  service: string;
  date_debut: string;
  date_fin: string;
  motif_refus: string | null;
}
