"""
Module Stages - Règles SH appliquées
Criticité: C2 (IMPORTANT) - Gestion des stages
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func, extract
from typing import Optional, List
from datetime import date, datetime
from app.core.database import get_db
from app.core.sh import (
    sh_get_val, sh_error, sh_generate_correlation_id, sh_format,
    sh_bounded_loop, sh_get_config
)
from app.schemas.schemas import (
    StageCreate, StageUpdate, StageResponse, StageListResponse,
    StatutStageEnum, RoleEnum
)
from app.models.models import Stage, Etudiant, Utilisateur, Service
from app.api.deps import get_current_user, get_coordinatrice_or_dsi

router = APIRouter(prefix="/stages", tags=["Stages"])


# Règle 3 SH: Machine à états explicite avec transitions contrôlées
TRANSITIONS_VALIDES = {
    StatutStageEnum.BROUILLON: [StatutStageEnum.VALIDE, StatutStageEnum.REFUSE, StatutStageEnum.ANNULE],
    StatutStageEnum.VALIDE: [StatutStageEnum.CONVENTIONNE, StatutStageEnum.BROUILLON, StatutStageEnum.ANNULE],
    StatutStageEnum.CONVENTIONNE: [StatutStageEnum.EN_COURS, StatutStageEnum.VALIDE, StatutStageEnum.ANNULE],
    StatutStageEnum.EN_COURS: [StatutStageEnum.TERMINE, StatutStageEnum.ANNULE],
    StatutStageEnum.TERMINE: [],
    StatutStageEnum.ANNULE: [StatutStageEnum.BROUILLON, StatutStageEnum.VALIDE],
    StatutStageEnum.REFUSE: [StatutStageEnum.BROUILLON]
}


def check_transition(current_status: StatutStageEnum, new_status: StatutStageEnum) -> bool:
    """
    Vérifie si une transition d'état est valide.
    Règle 3 SH: Utilise sh_get_val pour accès sécurisé.
    """
    allowed = sh_get_val(TRANSITIONS_VALIDES, current_status, [])
    return new_status in allowed


@router.get("", response_model=List[StageListResponse])
async def list_stages(
    search: Optional[str] = None,
    service_id: Optional[int] = None,
    etablissement_id: Optional[int] = None,
    statut: Optional[StatutStageEnum] = None,
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
    annee: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("date_debut", description="Champ de tri"),
    sort_order: str = Query("desc", description="asc ou desc"),
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Liste des stages avec filtres et pagination.
    Criticité: C2 (IMPORTANT)
    """
    correlation_id = sh_generate_correlation_id("STAGE", "C2")

    try:
        query = db.query(Stage).options(
            joinedload(Stage.etudiant).joinedload(Etudiant.etablissement),
            joinedload(Stage.service)
        ).filter(Stage.deleted_at.is_(None))

        if current_user.role == RoleEnum.CADRE and current_user.service_id:
            query = query.filter(Stage.service_id == current_user.service_id)

        if search:
            # Règle SH: sh_format au lieu de f-string
            search_term = sh_format("%{search}%", search=search)
            query = query.join(Stage.etudiant).filter(
                or_(
                    Etudiant.nom.ilike(search_term),
                    Etudiant.prenom.ilike(search_term),
                    Etudiant.code_egis.ilike(search_term)
                )
            )

        if service_id:
            query = query.filter(Stage.service_id == service_id)

        if etablissement_id:
            query = query.filter(Stage.etablissement_id == etablissement_id)

        if statut:
            query = query.filter(Stage.statut == statut)

        if date_debut:
            query = query.filter(Stage.date_debut >= date_debut)

        if date_fin:
            query = query.filter(Stage.date_fin <= date_fin)

        if annee:
            query = query.filter(extract('year', Stage.date_debut) == annee)

        sort_column = getattr(Stage, sort_by, Stage.date_debut)
        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        total = query.count()
        stages = query.offset((page - 1) * page_size).limit(page_size).all()

        sh_error(
            None,
            code_error="LIST_STAGES_SUCCESS",
            type_p="INFO",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id,
            context={"total": total, "page": page}
        )

        return stages

    except Exception as e:
        # Règle SH: except Exception générique TOUJOURS en dernier
        sh_error(
            e,
            code_error="LIST_STAGES_1",
            type_p="ERROR",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la récupération des stages", "correlation_id": correlation_id}
        )


@router.get("/{stage_id}", response_model=StageResponse)
async def get_stage(
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Récupère un stage par son ID.
    Criticité: C2 (IMPORTANT)
    """
    correlation_id = sh_generate_correlation_id("STAGE", "C2")

    try:
        stage = db.query(Stage).options(
            joinedload(Stage.etudiant).joinedload(Etudiant.etablissement),
            joinedload(Stage.service),
            joinedload(Stage.etablissement),
            joinedload(Stage.enseignant_referent)
        ).filter(
            Stage.id == stage_id,
            Stage.deleted_at.is_(None)
        ).first()

        if not stage:
            sh_error(
                None,
                code_error="GET_STAGE_NOT_FOUND",
                type_p="WARNING",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"stage_id": stage_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Stage non trouvé", "correlation_id": correlation_id}
            )

        if current_user.role == RoleEnum.CADRE and current_user.service_id:
            if stage.service_id != current_user.service_id:
                sh_error(
                    None,
                    code_error="GET_STAGE_ACCESS_DENIED",
                    type_p="WARNING",
                    criticality="C2",
                    correlation_id=correlation_id,
                    user_id=current_user.id,
                    context={"stage_id": stage_id, "service_id": stage.service_id}
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"message": "Accès non autorisé à ce stage", "correlation_id": correlation_id}
                )

        return stage

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="GET_STAGE_1",
            type_p="ERROR",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la récupération du stage", "correlation_id": correlation_id}
        )


@router.post("", response_model=StageResponse, status_code=status.HTTP_201_CREATED)
async def create_stage(
    stage_data: StageCreate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_coordinatrice_or_dsi)
):
    """
    Crée un nouveau stage.
    Criticité: C2 (IMPORTANT)
    """
    correlation_id = sh_generate_correlation_id("STAGE", "C2")

    try:
        etudiant = db.query(Etudiant).filter(
            Etudiant.id == stage_data.etudiant_id,
            Etudiant.deleted_at.is_(None)
        ).first()
        if not etudiant:
            sh_error(
                None,
                code_error="CREATE_STAGE_ETUDIANT_NOT_FOUND",
                type_p="WARNING",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"etudiant_id": stage_data.etudiant_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Étudiant non trouvé", "correlation_id": correlation_id}
            )

        service = db.query(Service).filter(
            Service.id == stage_data.service_id,
            Service.deleted_at.is_(None)
        ).first()
        if not service:
            sh_error(
                None,
                code_error="CREATE_STAGE_SERVICE_NOT_FOUND",
                type_p="WARNING",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"service_id": stage_data.service_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Service non trouvé", "correlation_id": correlation_id}
            )

        if stage_data.date_fin < stage_data.date_debut:
            sh_error(
                None,
                code_error="CREATE_STAGE_INVALID_DATES",
                type_p="WARNING",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "La date de fin doit être postérieure à la date de début", "correlation_id": correlation_id}
            )

        nombre_semaines = (stage_data.date_fin - stage_data.date_debut).days // 7

        stage = Stage(
            **stage_data.model_dump(),
            nombre_semaines=nombre_semaines,
            created_by=current_user.id
        )

        db.add(stage)
        db.commit()
        db.refresh(stage)

        # Règle 3 SH: Log création avec état initial
        sh_error(
            None,
            code_error="CREATE_STAGE_SUCCESS",
            type_p="INFO",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id,
            action="create_stage",
            context={
                "stage_id": stage.id,
                "statut_initial": stage.statut.value,
                "etudiant_id": stage_data.etudiant_id,
                "service_id": stage_data.service_id
            }
        )

        return stage

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="CREATE_STAGE_1",
            type_p="ERROR",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la création du stage", "correlation_id": correlation_id}
        )


@router.patch("/{stage_id}", response_model=StageResponse)
async def update_stage(
    stage_id: int,
    stage_data: StageUpdate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Met à jour un stage.
    Criticité: C2 (IMPORTANT) - Inclut transitions d'état (Règle 3 SH)
    """
    correlation_id = sh_generate_correlation_id("STAGE", "C2")

    try:
        stage = db.query(Stage).filter(
            Stage.id == stage_id,
            Stage.deleted_at.is_(None)
        ).first()

        if not stage:
            sh_error(
                None,
                code_error="UPDATE_STAGE_NOT_FOUND",
                type_p="WARNING",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"stage_id": stage_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Stage non trouvé", "correlation_id": correlation_id}
            )

        if stage.statut == StatutStageEnum.TERMINE:
            sh_error(
                None,
                code_error="UPDATE_STAGE_ALREADY_TERMINATED",
                type_p="WARNING",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"stage_id": stage_id}
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": "Impossible de modifier un stage terminé", "correlation_id": correlation_id}
            )

        if current_user.role == RoleEnum.CADRE:
            if stage.service_id != current_user.service_id:
                sh_error(
                    None,
                    code_error="UPDATE_STAGE_ACCESS_DENIED",
                    type_p="WARNING",
                    criticality="C2",
                    correlation_id=correlation_id,
                    user_id=current_user.id,
                    context={"stage_id": stage_id}
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"message": "Accès non autorisé", "correlation_id": correlation_id}
                )
            allowed_fields = ["commentaire"]
            update_data = stage_data.model_dump(exclude_unset=True)
            for field in update_data:
                if field not in allowed_fields:
                    sh_error(
                        None,
                        code_error="UPDATE_STAGE_FIELD_DENIED",
                        type_p="WARNING",
                        criticality="C2",
                        correlation_id=correlation_id,
                        user_id=current_user.id,
                        context={"field": field}
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={
                            "message": sh_format("Modification du champ {field} non autorisée", field=field),
                            "correlation_id": correlation_id
                        }
                    )

        update_data = stage_data.model_dump(exclude_unset=True)

        # Règle 3 SH: Validation et log des transitions d'état
        if "statut" in update_data:
            new_status = sh_get_val(update_data, "statut", None)
            old_status = stage.statut

            if not check_transition(old_status, new_status):
                sh_error(
                    None,
                    code_error="UPDATE_STAGE_INVALID_TRANSITION",
                    type_p="WARNING",
                    criticality="C2",
                    correlation_id=correlation_id,
                    user_id=current_user.id,
                    context={
                        "stage_id": stage_id,
                        "from_status": old_status.value,
                        "to_status": new_status.value
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "message": sh_format(
                            "Transition de {from_status} vers {to_status} non autorisée",
                            from_status=old_status.value,
                            to_status=new_status.value
                        ),
                        "correlation_id": correlation_id
                    }
                )

            if new_status == StatutStageEnum.REFUSE and "motif_refus" not in update_data:
                sh_error(
                    None,
                    code_error="UPDATE_STAGE_MISSING_MOTIF",
                    type_p="WARNING",
                    criticality="C2",
                    correlation_id=correlation_id,
                    user_id=current_user.id,
                    context={"stage_id": stage_id}
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"message": "Le motif de refus est obligatoire", "correlation_id": correlation_id}
                )

            # Règle 3 SH: Log transition d'état
            sh_error(
                None,
                code_error="STAGE_STATE_TRANSITION",
                type_p="INFO",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=current_user.id,
                action="state_transition",
                context={
                    "stage_id": stage_id,
                    "from_status": old_status.value,
                    "to_status": new_status.value
                }
            )

        for field, value in update_data.items():
            setattr(stage, field, value)

        if "date_debut" in update_data or "date_fin" in update_data:
            stage.nombre_semaines = (stage.date_fin - stage.date_debut).days // 7

        db.commit()
        db.refresh(stage)

        sh_error(
            None,
            code_error="UPDATE_STAGE_SUCCESS",
            type_p="INFO",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id,
            context={"stage_id": stage_id}
        )

        return stage

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="UPDATE_STAGE_1",
            type_p="ERROR",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la mise à jour du stage", "correlation_id": correlation_id}
        )


@router.delete("/{stage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stage(
    stage_id: int,
    motif: str = Query(..., description="Motif de suppression"),
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_coordinatrice_or_dsi)
):
    """
    Supprime un stage (soft delete).
    Criticité: C2 (IMPORTANT)
    """
    correlation_id = sh_generate_correlation_id("STAGE", "C2")

    try:
        stage = db.query(Stage).filter(
            Stage.id == stage_id,
            Stage.deleted_at.is_(None)
        ).first()

        if not stage:
            sh_error(
                None,
                code_error="DELETE_STAGE_NOT_FOUND",
                type_p="WARNING",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"stage_id": stage_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Stage non trouvé", "correlation_id": correlation_id}
            )

        if stage.statut == StatutStageEnum.TERMINE:
            sh_error(
                None,
                code_error="DELETE_STAGE_ALREADY_TERMINATED",
                type_p="WARNING",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"stage_id": stage_id}
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": "Impossible de supprimer un stage terminé", "correlation_id": correlation_id}
            )

        stage.deleted_at = func.now()
        stage.actif = False

        db.commit()

        sh_error(
            None,
            code_error="DELETE_STAGE_SUCCESS",
            type_p="INFO",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id,
            action="delete_stage",
            context={"stage_id": stage_id, "motif": motif}
        )

        return None

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="DELETE_STAGE_1",
            type_p="ERROR",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la suppression du stage", "correlation_id": correlation_id}
        )


@router.get("/calendrier/service/{service_id}")
async def get_calendrier_service(
    service_id: int,
    mois: Optional[int] = None,
    annee: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Calendrier des stages par service.
    Criticité: C3 (STANDARD)
    """
    correlation_id = sh_generate_correlation_id("STAGE", "C3")

    try:
        if current_user.role == RoleEnum.CADRE and current_user.service_id != service_id:
            sh_error(
                None,
                code_error="CALENDRIER_ACCESS_DENIED",
                type_p="WARNING",
                criticality="C3",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"service_id": service_id}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"message": "Accès non autorisé à ce service", "correlation_id": correlation_id}
            )

        query = db.query(Stage).options(
            joinedload(Stage.etudiant)
        ).filter(
            Stage.service_id == service_id,
            Stage.deleted_at.is_(None),
            Stage.statut.in_([
                StatutStageEnum.VALIDE,
                StatutStageEnum.CONVENTIONNE,
                StatutStageEnum.EN_COURS
            ])
        )

        if annee:
            query = query.filter(extract('year', Stage.date_debut) == annee)

        if mois and annee:
            query = query.filter(
                or_(
                    and_(
                        extract('month', Stage.date_debut) <= mois,
                        extract('month', Stage.date_fin) >= mois
                    )
                )
            )

        # Règle 1 SH: Limite configurable
        max_stages = sh_get_config("SH_DEFAULT_MAX_ITEMS", 10000, int)
        stages = query.order_by(Stage.date_debut).limit(max_stages).all()

        result = []
        # Règle 1 SH: Boucle bornée
        for s in sh_bounded_loop(stages, max_stages, "warn"):
            result.append({
                "id": s.id,
                # Règle SH: sh_format au lieu de f-string
                "etudiant": sh_format("{prenom} {nom}", prenom=s.etudiant.prenom, nom=s.etudiant.nom),
                "code_egis": s.etudiant.code_egis,
                "date_debut": s.date_debut.isoformat(),
                "date_fin": s.date_fin.isoformat(),
                "statut": s.statut.value
            })

        sh_error(
            None,
            code_error="CALENDRIER_SUCCESS",
            type_p="INFO",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id,
            context={"service_id": service_id, "nb_stages": len(result)}
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="CALENDRIER_1",
            type_p="ERROR",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la récupération du calendrier", "correlation_id": correlation_id}
        )
