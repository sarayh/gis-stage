"""
Module Rapports - Règles SH appliquées
Criticité: C3 (STANDARD) - Statistiques et exports
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import Optional
from datetime import datetime, date
import csv
import io
from app.core.database import get_db
from app.core.config import settings
from app.core.sh import (
    sh_error, sh_generate_correlation_id, sh_format,
    sh_bounded_loop, sh_get_config
)
from app.schemas.schemas import StatistiquesAnnuelles, StatutStageEnum
from app.models.models import Stage, Etudiant, Service, Etablissement, Utilisateur
from app.api.deps import get_current_user, get_coordinatrice_or_dsi

router = APIRouter(prefix="/rapports", tags=["Rapports"])


@router.get("/statistiques-annuelles", response_model=StatistiquesAnnuelles)
async def get_statistiques_annuelles(
    annee: int = Query(..., description="Année des statistiques"),
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_coordinatrice_or_dsi)
):
    """
    Statistiques annuelles globales.
    Criticité: C3 (STANDARD)
    """
    correlation_id = sh_generate_correlation_id("STATS", "C3")

    try:
        base_query = db.query(Stage).filter(
            Stage.deleted_at.is_(None),
            extract('year', Stage.date_debut) == annee
        )

        total = base_query.count()

        acceptes = base_query.filter(
            Stage.statut.in_([
                StatutStageEnum.VALIDE,
                StatutStageEnum.CONVENTIONNE,
                StatutStageEnum.EN_COURS,
                StatutStageEnum.TERMINE
            ])
        ).count()

        refuses = base_query.filter(Stage.statut == StatutStageEnum.REFUSE).count()
        en_cours = base_query.filter(Stage.statut == StatutStageEnum.EN_COURS).count()
        termines = base_query.filter(Stage.statut == StatutStageEnum.TERMINE).count()

        # Règle 1: Boucle bornée avec limite configurable
        max_services = sh_get_config("SH_MAX_SERVICES", 100, int)
        services_stats = db.query(
            Service.nom_service,
            func.count(Stage.id)
        ).join(Stage, Stage.service_id == Service.id).filter(
            Stage.deleted_at.is_(None),
            extract('year', Stage.date_debut) == annee
        ).group_by(Service.nom_service).limit(max_services).all()

        stages_par_service = {s[0]: s[1] for s in services_stats}

        max_etabs = sh_get_config("SH_MAX_ETABLISSEMENTS", 200, int)
        etab_stats = db.query(
            Etablissement.nom,
            func.count(Stage.id)
        ).join(Stage, Stage.etablissement_id == Etablissement.id).filter(
            Stage.deleted_at.is_(None),
            extract('year', Stage.date_debut) == annee
        ).group_by(Etablissement.nom).limit(max_etabs).all()

        stages_par_etablissement = {e[0]: e[1] for e in etab_stats}

        taux_acceptation = (acceptes / total * 100) if total > 0 else 0

        # Log succès
        sh_error(
            None,
            code_error="STATS_ANNUELLES_SUCCESS",
            type_p="INFO",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id,
            context={"annee": annee, "total": total}
        )

        return StatistiquesAnnuelles(
            annee=annee,
            total_stages=total,
            stages_acceptes=acceptes,
            stages_refuses=refuses,
            stages_en_cours=en_cours,
            stages_termines=termines,
            stages_par_service=stages_par_service,
            stages_par_etablissement=stages_par_etablissement,
            taux_acceptation=round(taux_acceptation, 2)
        )

    except Exception as e:
        sh_error(
            e,
            code_error="STATS_ANNUELLES_1",
            type_p="ERROR",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Erreur lors du calcul des statistiques",
                "correlation_id": correlation_id
            }
        )


@router.get("/rapport-services")
async def get_rapport_services(
    annee: int = Query(..., description="Année des statistiques"),
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Rapport détaillé par service avec acceptés/refusés.
    Criticité: C3 (STANDARD)
    """
    correlation_id = sh_generate_correlation_id("RAPPORT", "C3")

    try:
        # Règle 1: Limite configurable pour les services
        max_services = sh_get_config("SH_MAX_SERVICES", 100, int)
        services = db.query(Service).filter(
            Service.deleted_at.is_(None)
        ).limit(max_services).all()

        rapport = []

        # Règle 1: Boucle bornée avec sh_bounded_loop
        for service in sh_bounded_loop(services, max_services, "warn"):
            base_query = db.query(Stage).filter(
                Stage.deleted_at.is_(None),
                Stage.service_id == service.id,
                extract('year', Stage.date_debut) == annee
            )

            total = base_query.count()

            acceptes = base_query.filter(
                Stage.statut.in_([
                    StatutStageEnum.VALIDE,
                    StatutStageEnum.CONVENTIONNE,
                    StatutStageEnum.EN_COURS,
                    StatutStageEnum.TERMINE
                ])
            ).count()

            refuses = base_query.filter(Stage.statut == StatutStageEnum.REFUSE).count()
            en_attente = base_query.filter(Stage.statut == StatutStageEnum.BROUILLON).count()
            taux_acceptation = round((acceptes / total * 100), 1) if total > 0 else 0

            rapport.append({
                "service_id": service.id,
                "service_nom": service.nom_service,
                "total": total,
                "acceptes": acceptes,
                "refuses": refuses,
                "en_attente": en_attente,
                "taux_acceptation": taux_acceptation
            })

        rapport.sort(key=lambda x: x["total"], reverse=True)

        sh_error(
            None,
            code_error="RAPPORT_SERVICES_SUCCESS",
            type_p="INFO",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id,
            context={"annee": annee, "nb_services": len(rapport)}
        )

        return rapport

    except Exception as e:
        sh_error(
            e,
            code_error="RAPPORT_SERVICES_1",
            type_p="ERROR",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Erreur lors de la génération du rapport",
                "correlation_id": correlation_id
            }
        )


@router.get("/rapport-previsionnel")
async def get_rapport_previsionnel(
    annee: int = Query(..., description="Année prévisionnelle"),
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Rapport prévisionnel des stages à venir.
    Criticité: C3 (STANDARD)
    """
    correlation_id = sh_generate_correlation_id("RAPPORT", "C3")

    try:
        max_services = sh_get_config("SH_MAX_SERVICES", 100, int)
        services = db.query(Service).filter(
            Service.deleted_at.is_(None)
        ).limit(max_services).all()

        rapport = []

        for service in sh_bounded_loop(services, max_services, "warn"):
            stages_planifies = db.query(Stage).filter(
                Stage.deleted_at.is_(None),
                Stage.service_id == service.id,
                extract('year', Stage.date_debut) == annee,
                Stage.date_debut > date.today(),
                Stage.statut.in_([
                    StatutStageEnum.VALIDE,
                    StatutStageEnum.CONVENTIONNE,
                    StatutStageEnum.BROUILLON
                ])
            ).count()

            en_attente = db.query(Stage).filter(
                Stage.deleted_at.is_(None),
                Stage.service_id == service.id,
                extract('year', Stage.date_debut) == annee,
                Stage.statut == StatutStageEnum.BROUILLON
            ).count()

            rapport.append({
                "service_id": service.id,
                "service_nom": service.nom_service,
                "stages_planifies": stages_planifies,
                "en_attente_validation": en_attente
            })

        rapport.sort(key=lambda x: x["stages_planifies"], reverse=True)

        sh_error(
            None,
            code_error="RAPPORT_PREVISIONNEL_SUCCESS",
            type_p="INFO",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id,
            context={"annee": annee}
        )

        return rapport

    except Exception as e:
        sh_error(
            e,
            code_error="RAPPORT_PREVISIONNEL_1",
            type_p="ERROR",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Erreur lors de la génération du rapport prévisionnel",
                "correlation_id": correlation_id
            }
        )


@router.get("/export-csv")
async def export_stages_csv(
    annee: Optional[int] = None,
    service_id: Optional[int] = None,
    statut: Optional[StatutStageEnum] = None,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_coordinatrice_or_dsi)
):
    """
    Export CSV des stages.
    Criticité: C3 (STANDARD)
    """
    correlation_id = sh_generate_correlation_id("EXPORT", "C3")

    try:
        query = db.query(Stage).join(Etudiant).join(Service).join(Etablissement).filter(
            Stage.deleted_at.is_(None)
        )

        if annee:
            query = query.filter(extract('year', Stage.date_debut) == annee)
        if service_id:
            query = query.filter(Stage.service_id == service_id)
        if statut:
            query = query.filter(Stage.statut == statut)

        # Règle 1: Limite configurable pour l'export
        max_export = sh_get_config("MAX_LIGNES_EXPORT", settings.MAX_LIGNES_EXPORT, int)
        stages = query.limit(max_export).all()

        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')

        writer.writerow([
            'Code EGIS', 'Nom', 'Prénom', 'Email', 'Formation',
            'Établissement', 'Service', 'Date début', 'Date fin',
            'Statut', 'Date création'
        ])

        # Règle 1: Boucle bornée
        for stage in sh_bounded_loop(stages, max_export, "warn"):
            writer.writerow([
                stage.etudiant.code_egis,
                stage.etudiant.nom,
                stage.etudiant.prenom,
                stage.etudiant.email or '',
                stage.formation or '',
                stage.etablissement.nom if stage.etablissement else '',
                stage.service.nom_service if stage.service else '',
                stage.date_debut.strftime('%d/%m/%Y'),
                stage.date_fin.strftime('%d/%m/%Y'),
                stage.statut.value,
                stage.created_at.strftime('%d/%m/%Y %H:%M')
            ])

        output.seek(0)

        # Règle SH: sh_format au lieu de f-string
        now = datetime.now()
        filename = sh_format(
            "export_stages_{date}.csv",
            date=now.strftime('%Y%m%d_%H%M%S')
        )

        sh_error(
            None,
            code_error="EXPORT_CSV_SUCCESS",
            type_p="INFO",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id,
            context={"nb_lignes": len(stages), "annee": annee}
        )

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": sh_format(
                    "attachment; filename={filename}",
                    filename=filename
                )
            }
        )

    except Exception as e:
        sh_error(
            e,
            code_error="EXPORT_CSV_1",
            type_p="ERROR",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Erreur lors de l'export CSV",
                "correlation_id": correlation_id
            }
        )


@router.get("/stages-acceptes")
async def list_stages_acceptes(
    annee: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """Liste des stages acceptés. Criticité: C3."""
    correlation_id = sh_generate_correlation_id("RAPPORT", "C3")

    try:
        query = db.query(Stage).join(Etudiant).join(Service).filter(
            Stage.deleted_at.is_(None),
            Stage.statut.in_([
                StatutStageEnum.VALIDE,
                StatutStageEnum.CONVENTIONNE,
                StatutStageEnum.EN_COURS,
                StatutStageEnum.TERMINE
            ])
        )

        if annee:
            query = query.filter(extract('year', Stage.date_debut) == annee)

        # Règle 1: Limite sur les résultats
        max_items = sh_get_config("SH_DEFAULT_MAX_ITEMS", 10000, int)
        stages = query.order_by(Stage.date_debut.desc()).limit(max_items).all()

        result = []
        for s in sh_bounded_loop(stages, max_items, "warn"):
            result.append({
                "id": s.id,
                "code_egis": s.etudiant.code_egis,
                "nom": s.etudiant.nom,
                "prenom": s.etudiant.prenom,
                "email": s.etudiant.email,
                "service": s.service.nom_service,
                "date_debut": s.date_debut.isoformat(),
                "date_fin": s.date_fin.isoformat(),
                "statut": s.statut.value
            })

        return result

    except Exception as e:
        sh_error(
            e,
            code_error="STAGES_ACCEPTES_1",
            type_p="ERROR",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Erreur lors de la récupération des stages acceptés",
                "correlation_id": correlation_id
            }
        )


@router.get("/stages-refuses")
async def list_stages_refuses(
    annee: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_coordinatrice_or_dsi)
):
    """Liste des stages refusés. Criticité: C3."""
    correlation_id = sh_generate_correlation_id("RAPPORT", "C3")

    try:
        query = db.query(Stage).join(Etudiant).join(Service).filter(
            Stage.deleted_at.is_(None),
            Stage.statut == StatutStageEnum.REFUSE
        )

        if annee:
            query = query.filter(extract('year', Stage.date_debut) == annee)

        max_items = sh_get_config("SH_DEFAULT_MAX_ITEMS", 10000, int)
        stages = query.order_by(Stage.date_debut.desc()).limit(max_items).all()

        result = []
        for s in sh_bounded_loop(stages, max_items, "warn"):
            result.append({
                "id": s.id,
                "code_egis": s.etudiant.code_egis,
                "nom": s.etudiant.nom,
                "prenom": s.etudiant.prenom,
                "email": s.etudiant.email,
                "service": s.service.nom_service,
                "date_debut": s.date_debut.isoformat(),
                "date_fin": s.date_fin.isoformat(),
                "motif_refus": s.motif_refus
            })

        return result

    except Exception as e:
        sh_error(
            e,
            code_error="STAGES_REFUSES_1",
            type_p="ERROR",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Erreur lors de la récupération des stages refusés",
                "correlation_id": correlation_id
            }
        )
