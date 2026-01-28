from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class RoleEnum(str, enum.Enum):
    COORDINATRICE = "coordinatrice"
    CADRE = "cadre"
    DSI = "dsi"


class StatutStageEnum(str, enum.Enum):
    BROUILLON = "brouillon"
    VALIDE = "valide"
    CONVENTIONNE = "conventionne"
    EN_COURS = "en_cours"
    TERMINE = "termine"
    ANNULE = "annule"
    REFUSE = "refuse"


class EtatPresenceEnum(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    ABSENT_JUSTIFIE = "absent_justifie"
    NON_RENSEIGNE = "non_renseigne"


class TypeDocumentEnum(str, enum.Enum):
    CONVENTION = "convention"
    EVALUATION = "evaluation"
    VACCINATION = "vaccination"
    ATTESTATION = "attestation"
    AUTRE = "autre"


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    actif = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    service = relationship("Service", back_populates="utilisateurs")
    logs = relationship("AuditLog", back_populates="utilisateur")


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    nom_service = Column(String(200), unique=True, nullable=False)
    code = Column(String(20), unique=True)
    actif = Column(Boolean, default=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    utilisateurs = relationship("Utilisateur", back_populates="service")
    stages = relationship("Stage", back_populates="service")


class Etablissement(Base):
    __tablename__ = "etablissements"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), nullable=False)
    adresse = Column(Text)
    ville = Column(String(100))
    code_postal = Column(String(10))
    telephone = Column(String(20))
    email = Column(String(255))
    actif = Column(Boolean, default=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    etudiants = relationship("Etudiant", back_populates="etablissement")
    stages = relationship("Stage", back_populates="etablissement")


class RepresentantLegal(Base):
    __tablename__ = "representants_legaux"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    email = Column(String(255))
    telephone = Column(String(20))
    adresse = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    etudiants = relationship("Etudiant", back_populates="representant_legal")


class Etudiant(Base):
    __tablename__ = "etudiants"

    id = Column(Integer, primary_key=True, index=True)
    code_egis = Column(String(20), unique=True, index=True, nullable=False)
    nom = Column(String(100), nullable=False, index=True)
    prenom = Column(String(100), nullable=False, index=True)
    date_naissance = Column(Date)
    lieu_naissance = Column(String(200))
    email = Column(String(255), index=True)
    telephone = Column(String(20))
    adresse = Column(Text)
    formation = Column(String(200))
    etablissement_id = Column(Integer, ForeignKey("etablissements.id"))
    representant_legal_id = Column(Integer, ForeignKey("representants_legaux.id"), nullable=True)
    actif = Column(Boolean, default=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    etablissement = relationship("Etablissement", back_populates="etudiants")
    representant_legal = relationship("RepresentantLegal", back_populates="etudiants")
    stages = relationship("Stage", back_populates="etudiant")


class EnseignantReferent(Base):
    __tablename__ = "enseignants_referents"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    telephone = Column(String(20))
    email = Column(String(255))
    etablissement_id = Column(Integer, ForeignKey("etablissements.id"), nullable=True)
    actif = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    stages = relationship("Stage", back_populates="enseignant_referent")


class Stage(Base):
    __tablename__ = "stages"

    id = Column(Integer, primary_key=True, index=True)
    etudiant_id = Column(Integer, ForeignKey("etudiants.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    etablissement_id = Column(Integer, ForeignKey("etablissements.id"), nullable=False)
    enseignant_referent_id = Column(Integer, ForeignKey("enseignants_referents.id"), nullable=True)

    formation = Column(String(200))
    date_demande = Column(Date, server_default=func.current_date())
    date_debut = Column(Date, nullable=False)
    date_fin = Column(Date, nullable=False)
    nombre_semaines = Column(Integer)
    date_rendu_dossier = Column(Date)
    date_finalisation_dossier = Column(Date)

    statut = Column(Enum(StatutStageEnum), default=StatutStageEnum.BROUILLON)
    motif_refus = Column(Text, nullable=True)
    commentaire = Column(Text)

    actif = Column(Boolean, default=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("utilisateurs.id"))

    etudiant = relationship("Etudiant", back_populates="stages")
    service = relationship("Service", back_populates="stages")
    etablissement = relationship("Etablissement", back_populates="stages")
    enseignant_referent = relationship("EnseignantReferent", back_populates="stages")
    documents = relationship("Document", back_populates="stage")
    presences = relationship("Presence", back_populates="stage")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    stage_id = Column(Integer, ForeignKey("stages.id"), nullable=False)
    type_document = Column(Enum(TypeDocumentEnum), nullable=False)
    nom_document = Column(String(255), nullable=False)
    chemin_fichier = Column(String(500), nullable=False)
    taille = Column(Integer)
    mime_type = Column(String(100))
    valide = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(Integer, ForeignKey("utilisateurs.id"))

    stage = relationship("Stage", back_populates="documents")


class Presence(Base):
    __tablename__ = "presences"

    id = Column(Integer, primary_key=True, index=True)
    stage_id = Column(Integer, ForeignKey("stages.id"), nullable=False)
    date_presence = Column(Date, nullable=False)
    etat = Column(Enum(EtatPresenceEnum), default=EtatPresenceEnum.NON_RENSEIGNE)
    commentaire = Column(Text)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("utilisateurs.id"))

    stage = relationship("Stage", back_populates="presences")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    correlation_id = Column(String(100), index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    level = Column(String(20))
    action = Column(String(100), nullable=False)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    old_values = Column(Text)
    new_values = Column(Text)
    client_ip = Column(String(50))
    result = Column(String(20))
    duration_ms = Column(Integer)

    utilisateur = relationship("Utilisateur", back_populates="logs")


class EmailQueue(Base):
    __tablename__ = "email_queue"

    id = Column(Integer, primary_key=True, index=True)
    to_email = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(20), default="pending")
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
