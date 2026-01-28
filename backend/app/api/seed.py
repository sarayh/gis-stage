"""
API de génération de données de test - GIS-Stage
Criticité: C4 (CONFORT)

Endpoints pour créer un jeu de données complet pour les tests et démonstrations.
ATTENTION: Ces endpoints ne doivent PAS être exposés en production.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List
from datetime import date, timedelta
import random

from app.api.deps import get_db, get_current_user
from app.models.models import (
    Utilisateur, Etudiant, Stage, Presence, Document, Service,
    Etablissement, EnseignantReferent, RepresentantLegal,
    RoleEnum, StatutStageEnum, EtatPresenceEnum, TypeDocumentEnum
)
from app.core.security import get_password_hash
from app.core.sh import (
    sh_error, sh_format, sh_generate_correlation_id,
    sh_bounded_loop, sh_get_config
)
from app.core.config import settings

router = APIRouter()


# ============================================================================
# DONNÉES DE RÉFÉRENCE POUR LA GÉNÉRATION
# ============================================================================

PRENOMS = [
    "Marie", "Thomas", "Léa", "Lucas", "Emma", "Hugo", "Chloé", "Nathan",
    "Camille", "Mathis", "Sarah", "Enzo", "Manon", "Louis", "Julie",
    "Alexandre", "Laura", "Maxime", "Océane", "Antoine", "Clara", "Théo",
    "Pauline", "Quentin", "Anaïs", "Romain", "Justine", "Kevin", "Morgane",
    "Dylan", "Marion", "Florian", "Mélanie", "Julien", "Audrey", "Pierre",
    "Sophie", "Nicolas", "Céline", "Mathieu", "Aurélie", "Guillaume", "Élodie"
]

NOMS = [
    "Martin", "Bernard", "Thomas", "Petit", "Robert", "Richard", "Durand",
    "Dubois", "Moreau", "Laurent", "Simon", "Michel", "Lefebvre", "Leroy",
    "Roux", "David", "Bertrand", "Morel", "Fournier", "Girard", "Bonnet",
    "Dupont", "Lambert", "Fontaine", "Rousseau", "Vincent", "Muller", "Lefevre",
    "Faure", "Andre", "Mercier", "Blanc", "Guerin", "Boyer", "Garnier",
    "Chevalier", "François", "Legrand", "Gauthier", "Garcia", "Perrin", "Robin"
]

FORMATIONS = [
    "Infirmier (IFSI)", "Aide-soignant (IFAS)", "Médecine générale",
    "Médecine spécialisée", "Kinésithérapie", "Ergothérapie",
    "Psychomotricité", "Sage-femme", "Pharmacie", "Manipulateur radio",
    "Technicien de laboratoire", "Diététique", "Orthophonie",
    "Psychologie clinique", "Travail social"
]

VILLES = [
    "Gisors", "Rouen", "Évreux", "Paris", "Beauvais", "Vernon",
    "Les Andelys", "Magny-en-Vexin", "Chaumont-en-Vexin", "Gournay-en-Bray"
]

SERVICES_DATA = [
    {"nom": "Médecine", "code": "MED"},
    {"nom": "Chirurgie", "code": "CHIR"},
    {"nom": "Urgences", "code": "URG"},
    {"nom": "Pédiatrie", "code": "PED"},
    {"nom": "Maternité", "code": "MAT"},
    {"nom": "Cardiologie", "code": "CARD"},
    {"nom": "Pneumologie", "code": "PNEU"},
    {"nom": "Gériatrie", "code": "GER"},
    {"nom": "Psychiatrie", "code": "PSY"},
    {"nom": "Radiologie", "code": "RAD"},
    {"nom": "Laboratoire", "code": "LAB"},
    {"nom": "Pharmacie", "code": "PHAR"},
    {"nom": "Rééducation", "code": "REED"},
    {"nom": "Soins palliatifs", "code": "PALL"},
    {"nom": "Bloc opératoire", "code": "BLOC"}
]

ETABLISSEMENTS_DATA = [
    {"nom": "IFSI - Institut de Formation en Soins Infirmiers de Rouen", "ville": "Rouen", "cp": "76000"},
    {"nom": "IFAS - Institut de Formation Aide-Soignant d'Évreux", "ville": "Évreux", "cp": "27000"},
    {"nom": "Université de Rouen - Faculté de Médecine", "ville": "Rouen", "cp": "76000"},
    {"nom": "IFMK - Institut de Formation en Masso-Kinésithérapie", "ville": "Rouen", "cp": "76000"},
    {"nom": "IFE - Institut de Formation en Ergothérapie", "ville": "Paris", "cp": "75013"},
    {"nom": "École de Sages-femmes de Rouen", "ville": "Rouen", "cp": "76000"},
    {"nom": "Faculté de Pharmacie de Rouen", "ville": "Rouen", "cp": "76000"},
    {"nom": "IFMEM - Institut de Formation Manipulateurs Électroradiologie", "ville": "Rouen", "cp": "76000"},
    {"nom": "IUT Génie Biologique - Université de Rouen", "ville": "Évreux", "cp": "27000"},
    {"nom": "Lycée professionnel Les Fontenelles", "ville": "Louviers", "cp": "27400"},
    {"nom": "IRTS - Institut Régional du Travail Social", "ville": "Canteleu", "cp": "76380"},
    {"nom": "Université Paris Cité - Faculté de Santé", "ville": "Paris", "cp": "75006"}
]

MOTIFS_REFUS = [
    "Pas de place disponible dans le service demandé",
    "Période non compatible avec les besoins du service",
    "Formation non adaptée au service demandé",
    "Quota de stagiaires atteint pour cette période",
    "Documents administratifs incomplets",
    "Niveau d'étude insuffisant pour ce type de stage",
    "Chevauchement avec un autre stagiaire du même établissement"
]

COMMENTAIRES_STAGES = [
    "Stage de découverte du milieu hospitalier",
    "Stage de mise en situation professionnelle",
    "Excellent contact avec l'équipe soignante",
    "Stagiaire motivé et impliqué",
    "Première expérience en milieu hospitalier",
    "Stage dans le cadre du mémoire de fin d'études",
    "Observation et participation aux soins",
    "Stage conventionné avec objectifs pédagogiques définis",
    None, None, None  # Certains stages sans commentaire
]


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def _generate_phone() -> str:
    """Génère un numéro de téléphone français fictif."""
    return sh_format("06{num}", num=random.randint(10000000, 99999999))


def _generate_email(prenom: str, nom: str, domain: str = "email.com") -> str:
    """Génère une adresse email fictive."""
    prenom_clean = prenom.lower().replace("é", "e").replace("è", "e").replace("ë", "e")
    prenom_clean = prenom_clean.replace("ï", "i").replace("ô", "o").replace("ç", "c")
    nom_clean = nom.lower().replace("é", "e").replace("è", "e")
    return sh_format("{prenom}.{nom}@{domain}", prenom=prenom_clean, nom=nom_clean, domain=domain)


def _generate_address(ville: str) -> str:
    """Génère une adresse fictive."""
    num = random.randint(1, 150)
    rues = ["rue de la République", "avenue Jean Jaurès", "rue Victor Hugo",
            "place de la Mairie", "boulevard Gambetta", "rue Pasteur",
            "rue des Écoles", "avenue de la Gare", "rue du Commerce"]
    return sh_format("{num} {rue}, {ville}", num=num, rue=random.choice(rues), ville=ville)


# ============================================================================
# ENDPOINTS API
# ============================================================================

@router.post("/generate", response_model=Dict[str, Any])
async def generate_test_data(
    nb_etudiants: int = 30,
    nb_stages: int = 50,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Génère un jeu de données de test complet.

    **Accès**: DSI uniquement (environnement de développement)

    **Paramètres**:
    - nb_etudiants: Nombre d'étudiants à créer (défaut: 30, max: 100)
    - nb_stages: Nombre de stages à créer (défaut: 50, max: 200)

    **Crée**:
    - Services hospitaliers
    - Établissements partenaires
    - Enseignants référents
    - Utilisateurs de test (coordinatrice, cadres, DSI)
    - Étudiants avec représentants légaux pour les mineurs
    - Stages avec différents statuts
    - Présences pour les stages en cours et terminés

    **Retourne**: Statistiques de création
    """
    correlation_id = sh_generate_correlation_id("SEED", "C4")

    # Vérification des droits (DSI uniquement)
    if current_user.role != RoleEnum.DSI:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Seul un utilisateur DSI peut générer des données de test",
                "correlation_id": correlation_id
            }
        )

    # Limiter les paramètres
    nb_etudiants = min(nb_etudiants, 100)
    nb_stages = min(nb_stages, 200)

    try:
        stats = {
            "services": 0,
            "etablissements": 0,
            "enseignants": 0,
            "utilisateurs": 0,
            "etudiants": 0,
            "stages": 0,
            "presences": 0,
            "stages_par_statut": {},
            "correlation_id": correlation_id
        }

        # ================================================================
        # 1. CRÉATION DES SERVICES
        # ================================================================
        services_crees = []
        for service_data in sh_bounded_loop(SERVICES_DATA, 20, "warn"):
            existing = db.query(Service).filter(Service.code == service_data["code"]).first()
            if not existing:
                service = Service(
                    nom_service=service_data["nom"],
                    code=service_data["code"],
                    actif=True
                )
                db.add(service)
                services_crees.append(service)
                stats["services"] += 1

        db.flush()
        all_services = db.query(Service).filter(Service.actif == True).all()

        # ================================================================
        # 2. CRÉATION DES ÉTABLISSEMENTS
        # ================================================================
        etablissements_crees = []
        for etab_data in sh_bounded_loop(ETABLISSEMENTS_DATA, 20, "warn"):
            existing = db.query(Etablissement).filter(Etablissement.nom == etab_data["nom"]).first()
            if not existing:
                etablissement = Etablissement(
                    nom=etab_data["nom"],
                    adresse=_generate_address(etab_data["ville"]),
                    ville=etab_data["ville"],
                    code_postal=etab_data["cp"],
                    telephone=_generate_phone(),
                    email=sh_format("contact@{dom}.fr", dom=etab_data["nom"].split()[0].lower()),
                    actif=True
                )
                db.add(etablissement)
                etablissements_crees.append(etablissement)
                stats["etablissements"] += 1

        db.flush()
        all_etablissements = db.query(Etablissement).filter(Etablissement.actif == True).all()

        # ================================================================
        # 3. CRÉATION DES ENSEIGNANTS RÉFÉRENTS
        # ================================================================
        existing_enseignants = db.query(EnseignantReferent).count()
        if existing_enseignants < 10:
            for i in range(10 - existing_enseignants):
                prenom = random.choice(PRENOMS)
                nom = random.choice(NOMS)
                enseignant = EnseignantReferent(
                    nom=nom,
                    prenom=prenom,
                    email=_generate_email(prenom, nom, "education.fr"),
                    telephone=_generate_phone(),
                    etablissement_id=random.choice(all_etablissements).id if all_etablissements else None,
                    actif=True
                )
                db.add(enseignant)
                stats["enseignants"] += 1

        db.flush()
        all_enseignants = db.query(EnseignantReferent).filter(EnseignantReferent.actif == True).all()

        # ================================================================
        # 4. CRÉATION DES UTILISATEURS DE TEST
        # ================================================================
        users_to_create = [
            {"username": "coordinatrice", "role": RoleEnum.COORDINATRICE, "nom": "Dupont", "prenom": "Marie"},
            {"username": "cadre_med", "role": RoleEnum.CADRE, "nom": "Martin", "prenom": "Pierre", "service_code": "MED"},
            {"username": "cadre_chir", "role": RoleEnum.CADRE, "nom": "Bernard", "prenom": "Sophie", "service_code": "CHIR"},
            {"username": "cadre_urg", "role": RoleEnum.CADRE, "nom": "Petit", "prenom": "Jean", "service_code": "URG"},
            {"username": "dsi_test", "role": RoleEnum.DSI, "nom": "Admin", "prenom": "Test"},
        ]

        for user_data in sh_bounded_loop(users_to_create, 10, "warn"):
            existing = db.query(Utilisateur).filter(Utilisateur.username == user_data["username"]).first()
            if not existing:
                service_id = None
                if "service_code" in user_data:
                    service = db.query(Service).filter(Service.code == user_data["service_code"]).first()
                    service_id = service.id if service else None

                user = Utilisateur(
                    username=user_data["username"],
                    email=sh_format("{user}@ch-gisors.fr", user=user_data["username"]),
                    nom=user_data["nom"],
                    prenom=user_data["prenom"],
                    role=user_data["role"],
                    service_id=service_id,
                    actif=True
                )
                db.add(user)
                stats["utilisateurs"] += 1

        db.flush()

        # ================================================================
        # 5. CRÉATION DES ÉTUDIANTS
        # ================================================================
        last_etudiant = db.query(Etudiant).order_by(Etudiant.id.desc()).first()
        start_code = int(last_etudiant.code_egis[4:]) + 1 if last_etudiant else 1

        etudiants_crees = []
        for i in sh_bounded_loop(range(nb_etudiants), nb_etudiants, "warn"):
            prenom = random.choice(PRENOMS)
            nom = random.choice(NOMS)

            # Date de naissance (18-25 ans, quelques mineurs 16-17 ans)
            age = random.choices([16, 17, 18, 19, 20, 21, 22, 23, 24, 25],
                                weights=[1, 2, 5, 8, 10, 10, 8, 5, 3, 2])[0]
            annee_naissance = date.today().year - age
            date_naissance = date(annee_naissance, random.randint(1, 12), random.randint(1, 28))

            # Représentant légal pour les mineurs
            representant_id = None
            if age < 18:
                rep_prenom = random.choice(PRENOMS)
                rep_nom = nom  # Même nom de famille
                representant = RepresentantLegal(
                    nom=rep_nom,
                    prenom=rep_prenom,
                    email=_generate_email(rep_prenom, rep_nom),
                    telephone=_generate_phone(),
                    adresse=_generate_address(random.choice(VILLES))
                )
                db.add(representant)
                db.flush()
                representant_id = representant.id

            etudiant = Etudiant(
                code_egis=sh_format("EGIS{num:04d}", num=start_code + i),
                nom=nom,
                prenom=prenom,
                date_naissance=date_naissance,
                lieu_naissance=random.choice(VILLES),
                email=_generate_email(prenom, nom),
                telephone=_generate_phone(),
                adresse=_generate_address(random.choice(VILLES)),
                formation=random.choice(FORMATIONS),
                etablissement_id=random.choice(all_etablissements).id if all_etablissements else None,
                representant_legal_id=representant_id,
                actif=True
            )
            db.add(etudiant)
            etudiants_crees.append(etudiant)
            stats["etudiants"] += 1

        db.flush()
        for e in etudiants_crees:
            db.refresh(e)

        all_etudiants = db.query(Etudiant).filter(Etudiant.actif == True).all()

        # ================================================================
        # 6. CRÉATION DES STAGES
        # ================================================================
        # Distribution des statuts (réaliste)
        statuts_distribution = [
            (StatutStageEnum.TERMINE, 25, -180, -30),      # 25% terminés (passés)
            (StatutStageEnum.EN_COURS, 15, -30, 30),       # 15% en cours
            (StatutStageEnum.CONVENTIONNE, 15, 7, 60),     # 15% conventionnés (à venir)
            (StatutStageEnum.VALIDE, 20, 14, 90),          # 20% validés (à venir)
            (StatutStageEnum.BROUILLON, 10, 30, 120),      # 10% brouillons
            (StatutStageEnum.REFUSE, 10, -60, 60),         # 10% refusés
            (StatutStageEnum.ANNULE, 5, -90, 30),          # 5% annulés
        ]

        stages_crees = []
        stage_index = 0

        for statut, pct, min_days, max_days in sh_bounded_loop(statuts_distribution, 10, "warn"):
            nb_for_status = max(1, int(nb_stages * pct / 100))

            for _ in sh_bounded_loop(range(nb_for_status), nb_for_status, "warn"):
                if stage_index >= nb_stages:
                    break

                # Dates
                offset_debut = random.randint(min_days, max_days)
                date_debut = date.today() + timedelta(days=offset_debut)
                duree_semaines = random.choice([2, 4, 6, 8, 10, 12])
                date_fin = date_debut + timedelta(weeks=duree_semaines)

                stage = Stage(
                    etudiant_id=random.choice(all_etudiants).id,
                    service_id=random.choice(all_services).id,
                    etablissement_id=random.choice(all_etablissements).id if all_etablissements else None,
                    enseignant_referent_id=random.choice(all_enseignants).id if all_enseignants else None,
                    formation=random.choice(FORMATIONS),
                    date_debut=date_debut,
                    date_fin=date_fin,
                    nombre_semaines=duree_semaines,
                    statut=statut,
                    motif_refus=random.choice(MOTIFS_REFUS) if statut == StatutStageEnum.REFUSE else None,
                    commentaire=random.choice(COMMENTAIRES_STAGES),
                    created_by=current_user.id
                )
                db.add(stage)
                stages_crees.append(stage)
                stats["stages"] += 1

                # Comptage par statut
                statut_key = statut.value
                stats["stages_par_statut"][statut_key] = stats["stages_par_statut"].get(statut_key, 0) + 1

                stage_index += 1

        db.flush()
        for s in stages_crees:
            db.refresh(s)

        # ================================================================
        # 7. CRÉATION DES PRÉSENCES
        # ================================================================
        stages_avec_presences = db.query(Stage).filter(
            Stage.statut.in_([StatutStageEnum.EN_COURS, StatutStageEnum.TERMINE])
        ).all()

        # Distribution réaliste des présences
        etats_distribution = [
            (EtatPresenceEnum.PRESENT, 85),
            (EtatPresenceEnum.ABSENT, 5),
            (EtatPresenceEnum.ABSENT_JUSTIFIE, 8),
            (EtatPresenceEnum.NON_RENSEIGNE, 2),
        ]

        for stage in sh_bounded_loop(stages_avec_presences, 200, "warn"):
            current_date = stage.date_debut
            end_date = min(stage.date_fin, date.today())

            day_count = 0
            max_days = 365  # Limite de sécurité

            while current_date <= end_date and day_count < max_days:
                # Seulement les jours de semaine
                if current_date.weekday() < 5:
                    # Choix pondéré de l'état
                    etat = random.choices(
                        [e[0] for e in etats_distribution],
                        weights=[e[1] for e in etats_distribution]
                    )[0]

                    presence = Presence(
                        stage_id=stage.id,
                        date_presence=current_date,
                        etat=etat,
                        commentaire="Absence pour maladie" if etat == EtatPresenceEnum.ABSENT_JUSTIFIE else None,
                        updated_by=current_user.id
                    )
                    db.add(presence)
                    stats["presences"] += 1

                current_date += timedelta(days=1)
                day_count += 1

        # ================================================================
        # COMMIT FINAL
        # ================================================================
        db.commit()

        # Log de succès
        sh_error(
            None,
            code_error="SEED_DATA_SUCCESS",
            type_p="INFO",
            criticality="C4",
            correlation_id=correlation_id,
            action="generate_test_data",
            context=stats
        )

        return {
            "success": True,
            "message": "Jeu de données de test créé avec succès",
            "statistics": stats
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        sh_error(
            e,
            code_error="SEED_DATA_ERROR",
            type_p="ERROR",
            criticality="C4",
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Erreur lors de la génération des données de test",
                "correlation_id": correlation_id
            }
        )


@router.delete("/reset", response_model=Dict[str, Any])
async def reset_test_data(
    confirm: bool = False,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Supprime toutes les données de test (ATTENTION: irréversible).

    **Accès**: DSI uniquement

    **Paramètres**:
    - confirm: Doit être True pour confirmer la suppression

    **Supprime**: Présences, Documents, Stages, Étudiants, Enseignants
    (Conserve: Services, Établissements, Utilisateurs)
    """
    correlation_id = sh_generate_correlation_id("SEED", "C4")

    if current_user.role != RoleEnum.DSI:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Seul un utilisateur DSI peut réinitialiser les données",
                "correlation_id": correlation_id
            }
        )

    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Ajoutez ?confirm=true pour confirmer la suppression",
                "correlation_id": correlation_id
            }
        )

    try:
        stats = {
            "presences_deleted": db.query(Presence).delete(),
            "documents_deleted": db.query(Document).delete(),
            "stages_deleted": db.query(Stage).delete(),
            "etudiants_deleted": db.query(Etudiant).delete(),
            "representants_deleted": db.query(RepresentantLegal).delete(),
            "enseignants_deleted": db.query(EnseignantReferent).delete(),
            "correlation_id": correlation_id
        }

        db.commit()

        sh_error(
            None,
            code_error="SEED_DATA_RESET",
            type_p="WARNING",
            criticality="C4",
            correlation_id=correlation_id,
            action="reset_test_data",
            context=stats,
            user_id=current_user.id
        )

        return {
            "success": True,
            "message": "Données de test supprimées avec succès",
            "statistics": stats
        }

    except Exception as e:
        db.rollback()
        sh_error(
            e,
            code_error="SEED_RESET_ERROR",
            type_p="ERROR",
            criticality="C4",
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Erreur lors de la réinitialisation",
                "correlation_id": correlation_id
            }
        )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_data_statistics(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Retourne les statistiques actuelles de la base de données.

    **Accès**: Tous les utilisateurs authentifiés
    """
    correlation_id = sh_generate_correlation_id("SEED", "C4")

    try:
        stats = {
            "utilisateurs": db.query(Utilisateur).filter(Utilisateur.actif == True).count(),
            "services": db.query(Service).filter(Service.actif == True).count(),
            "etablissements": db.query(Etablissement).filter(Etablissement.actif == True).count(),
            "enseignants": db.query(EnseignantReferent).filter(EnseignantReferent.actif == True).count(),
            "etudiants": db.query(Etudiant).filter(Etudiant.actif == True).count(),
            "stages": {
                "total": db.query(Stage).filter(Stage.actif == True).count(),
                "par_statut": {}
            },
            "presences": db.query(Presence).count(),
            "documents": db.query(Document).filter(Document.deleted_at == None).count(),
            "correlation_id": correlation_id
        }

        # Stages par statut
        for statut in StatutStageEnum:
            count = db.query(Stage).filter(
                Stage.actif == True,
                Stage.statut == statut
            ).count()
            if count > 0:
                stats["stages"]["par_statut"][statut.value] = count

        return stats

    except Exception as e:
        sh_error(
            e,
            code_error="SEED_STATS_ERROR",
            type_p="ERROR",
            criticality="C4",
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Erreur lors de la récupération des statistiques",
                "correlation_id": correlation_id
            }
        )
