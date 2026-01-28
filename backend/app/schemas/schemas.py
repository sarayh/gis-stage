from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class RoleEnum(str, Enum):
    COORDINATRICE = "coordinatrice"
    CADRE = "cadre"
    DSI = "dsi"


class StatutStageEnum(str, Enum):
    BROUILLON = "brouillon"
    VALIDE = "valide"
    CONVENTIONNE = "conventionne"
    EN_COURS = "en_cours"
    TERMINE = "termine"
    ANNULE = "annule"
    REFUSE = "refuse"


class EtatPresenceEnum(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    ABSENT_JUSTIFIE = "absent_justifie"
    NON_RENSEIGNE = "non_renseigne"


class TypeDocumentEnum(str, Enum):
    CONVENTION = "convention"
    EVALUATION = "evaluation"
    VACCINATION = "vaccination"
    ATTESTATION = "attestation"
    AUTRE = "autre"


# Token schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    role: str
    service_id: Optional[int] = None
    exp: datetime


# Login
class LoginRequest(BaseModel):
    username: str
    password: str


# Service schemas
class ServiceBase(BaseModel):
    nom_service: str
    code: Optional[str] = None


class ServiceCreate(ServiceBase):
    pass


class ServiceResponse(ServiceBase):
    id: int
    actif: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Etablissement schemas
class EtablissementBase(BaseModel):
    nom: str
    adresse: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[EmailStr] = None


class EtablissementCreate(EtablissementBase):
    pass


class EtablissementResponse(EtablissementBase):
    id: int
    actif: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Representant Legal schemas
class RepresentantLegalBase(BaseModel):
    nom: str
    prenom: str
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None


class RepresentantLegalCreate(RepresentantLegalBase):
    pass


class RepresentantLegalResponse(RepresentantLegalBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Enseignant Referent schemas
class EnseignantReferentBase(BaseModel):
    nom: str
    prenom: str
    telephone: Optional[str] = None
    email: Optional[EmailStr] = None
    etablissement_id: Optional[int] = None


class EnseignantReferentCreate(EnseignantReferentBase):
    pass


class EnseignantReferentResponse(EnseignantReferentBase):
    id: int
    actif: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Etudiant schemas
class EtudiantBase(BaseModel):
    nom: str = Field(..., min_length=1, max_length=100)
    prenom: str = Field(..., min_length=1, max_length=100)
    date_naissance: Optional[date] = None
    lieu_naissance: Optional[str] = None
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    formation: Optional[str] = None
    etablissement_id: Optional[int] = None
    representant_legal_id: Optional[int] = None


class EtudiantCreate(EtudiantBase):
    pass


class EtudiantUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    date_naissance: Optional[date] = None
    lieu_naissance: Optional[str] = None
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    formation: Optional[str] = None
    etablissement_id: Optional[int] = None
    representant_legal_id: Optional[int] = None


class EtudiantResponse(EtudiantBase):
    id: int
    code_egis: str
    actif: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    etablissement: Optional[EtablissementResponse] = None
    representant_legal: Optional[RepresentantLegalResponse] = None

    class Config:
        from_attributes = True


class EtudiantListResponse(BaseModel):
    id: int
    code_egis: str
    nom: str
    prenom: str
    email: Optional[str] = None
    formation: Optional[str] = None
    etablissement: Optional[EtablissementResponse] = None

    class Config:
        from_attributes = True


# Stage schemas
class StageBase(BaseModel):
    etudiant_id: int
    service_id: int
    etablissement_id: int
    enseignant_referent_id: Optional[int] = None
    formation: Optional[str] = None
    date_debut: date
    date_fin: date
    nombre_semaines: Optional[int] = None
    commentaire: Optional[str] = None

    @field_validator('date_fin')
    @classmethod
    def date_fin_after_debut(cls, v, info):
        if 'date_debut' in info.data and v < info.data['date_debut']:
            raise ValueError('La date de fin doit être postérieure à la date de début')
        return v


class StageCreate(StageBase):
    statut: Optional[StatutStageEnum] = StatutStageEnum.BROUILLON


class StageUpdate(BaseModel):
    service_id: Optional[int] = None
    enseignant_referent_id: Optional[int] = None
    formation: Optional[str] = None
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    nombre_semaines: Optional[int] = None
    date_rendu_dossier: Optional[date] = None
    date_finalisation_dossier: Optional[date] = None
    statut: Optional[StatutStageEnum] = None
    motif_refus: Optional[str] = None
    commentaire: Optional[str] = None


class StageResponse(BaseModel):
    id: int
    etudiant_id: int
    service_id: int
    etablissement_id: int
    enseignant_referent_id: Optional[int] = None
    formation: Optional[str] = None
    date_demande: Optional[date] = None
    date_debut: date
    date_fin: date
    nombre_semaines: Optional[int] = None
    date_rendu_dossier: Optional[date] = None
    date_finalisation_dossier: Optional[date] = None
    statut: StatutStageEnum
    motif_refus: Optional[str] = None
    commentaire: Optional[str] = None
    actif: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    etudiant: Optional[EtudiantListResponse] = None
    service: Optional[ServiceResponse] = None
    etablissement: Optional[EtablissementResponse] = None
    enseignant_referent: Optional[EnseignantReferentResponse] = None

    class Config:
        from_attributes = True


class StageListResponse(BaseModel):
    id: int
    etudiant: EtudiantListResponse
    service: ServiceResponse
    date_debut: date
    date_fin: date
    statut: StatutStageEnum
    created_at: datetime

    class Config:
        from_attributes = True


# Document schemas
class DocumentBase(BaseModel):
    stage_id: int
    type_document: TypeDocumentEnum
    nom_document: str


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    id: int
    chemin_fichier: str
    taille: Optional[int] = None
    mime_type: Optional[str] = None
    valide: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Presence schemas
class PresenceBase(BaseModel):
    stage_id: int
    date_presence: date
    etat: EtatPresenceEnum
    commentaire: Optional[str] = None


class PresenceCreate(PresenceBase):
    pass


class PresenceUpdate(BaseModel):
    etat: EtatPresenceEnum
    commentaire: Optional[str] = None


class PresenceBulkUpdate(BaseModel):
    presences: List[PresenceCreate]


class PresenceResponse(PresenceBase):
    id: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Utilisateur schemas
class UtilisateurBase(BaseModel):
    username: str
    email: EmailStr
    nom: str
    prenom: str
    role: RoleEnum
    service_id: Optional[int] = None


class UtilisateurCreate(UtilisateurBase):
    pass


class UtilisateurResponse(UtilisateurBase):
    id: int
    actif: bool
    created_at: datetime
    service: Optional[ServiceResponse] = None

    class Config:
        from_attributes = True


# Statistiques / Rapport
class StatistiquesAnnuelles(BaseModel):
    annee: int
    total_stages: int
    stages_acceptes: int
    stages_refuses: int
    stages_en_cours: int
    stages_termines: int
    stages_par_service: dict
    stages_par_etablissement: dict
    taux_acceptation: float


# Pagination
class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    page_size: int
    total_pages: int


# API Response
class APIResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[dict] = None
    meta: Optional[dict] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: dict
    meta: dict
