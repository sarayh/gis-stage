"""
Module Presences - Règles SH appliquées
Criticité: C3 (STANDARD) - Gestion des présences
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.core.database import get_db
from app.core.sh import (
    sh_error, sh_generate_correlation_id, sh_bounded_loop, sh_get_config
)
from app.schemas.schemas import (
    PresenceCreate, PresenceUpdate, PresenceResponse,
    PresenceBulkUpdate, RoleEnum
)
from app.models.models import Presence, Stage, Utilisateur
from app.api.deps import get_current_user

router = APIRouter(prefix="/presences", tags=["Presences"])


@router.get("/stage/{stage_id}", response_model=List[PresenceResponse])
async def list_presences_stage(
    stage_id: int,
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Liste des présences d'un stage.
    Criticité: C3 (STANDARD)
    """
    correlation_id = sh_generate_correlation_id("PRESENCE", "C3")

    try:
        stage = db.query(Stage).filter(
            Stage.id == stage_id,
            Stage.deleted_at.is_(None)
        ).first()

        if not stage:
            sh_error(
                None,
                code_error="LIST_PRESENCES_STAGE_NOT_FOUND",
                type_p="WARNING",
                criticality="C3",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"stage_id": stage_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Stage non trouvé", "correlation_id": correlation_id}
            )

        if current_user.role == RoleEnum.CADRE and stage.service_id != current_user.service_id:
            sh_error(
                None,
                code_error="LIST_PRESENCES_ACCESS_DENIED",
                type_p="WARNING",
                criticality="C3",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"stage_id": stage_id}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"message": "Accès non autorisé", "correlation_id": correlation_id}
            )

        query = db.query(Presence).filter(Presence.stage_id == stage_id)

        if date_debut:
            query = query.filter(Presence.date_presence >= date_debut)
        if date_fin:
            query = query.filter(Presence.date_presence <= date_fin)

        # Règle 1 SH: Limite configurable
        max_presences = sh_get_config("SH_DEFAULT_MAX_ITEMS", 10000, int)
        presences = query.order_by(Presence.date_presence).limit(max_presences).all()

        return presences

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="LIST_PRESENCES_1",
            type_p="ERROR",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la récupération des présences", "correlation_id": correlation_id}
        )


@router.post("", response_model=PresenceResponse, status_code=status.HTTP_201_CREATED)
async def create_presence(
    presence_data: PresenceCreate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Crée ou met à jour une présence.
    Criticité: C3 (STANDARD)
    """
    correlation_id = sh_generate_correlation_id("PRESENCE", "C3")

    try:
        stage = db.query(Stage).filter(
            Stage.id == presence_data.stage_id,
            Stage.deleted_at.is_(None)
        ).first()

        if not stage:
            sh_error(
                None,
                code_error="CREATE_PRESENCE_STAGE_NOT_FOUND",
                type_p="WARNING",
                criticality="C3",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"stage_id": presence_data.stage_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Stage non trouvé", "correlation_id": correlation_id}
            )

        if current_user.role == RoleEnum.CADRE and stage.service_id != current_user.service_id:
            sh_error(
                None,
                code_error="CREATE_PRESENCE_ACCESS_DENIED",
                type_p="WARNING",
                criticality="C3",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"stage_id": presence_data.stage_id}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"message": "Accès non autorisé", "correlation_id": correlation_id}
            )

        existing = db.query(Presence).filter(
            Presence.stage_id == presence_data.stage_id,
            Presence.date_presence == presence_data.date_presence
        ).first()

        if existing:
            existing.etat = presence_data.etat
            existing.commentaire = presence_data.commentaire
            existing.updated_by = current_user.id
            db.commit()
            db.refresh(existing)

            sh_error(
                None,
                code_error="UPDATE_PRESENCE_SUCCESS",
                type_p="INFO",
                criticality="C3",
                correlation_id=correlation_id,
                user_id=current_user.id,
                action="update_presence",
                context={"presence_id": existing.id, "date": str(presence_data.date_presence)}
            )

            return existing

        presence = Presence(
            **presence_data.model_dump(),
            updated_by=current_user.id
        )
        db.add(presence)
        db.commit()
        db.refresh(presence)

        sh_error(
            None,
            code_error="CREATE_PRESENCE_SUCCESS",
            type_p="INFO",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id,
            action="create_presence",
            context={"presence_id": presence.id, "stage_id": presence_data.stage_id}
        )

        return presence

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="CREATE_PRESENCE_1",
            type_p="ERROR",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la création de la présence", "correlation_id": correlation_id}
        )


@router.post("/bulk", response_model=List[PresenceResponse])
async def bulk_update_presences(
    data: PresenceBulkUpdate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Mise à jour en masse des présences.
    Criticité: C3 (STANDARD)
    """
    correlation_id = sh_generate_correlation_id("PRESENCE", "C3")

    try:
        results = []

        # Règle 1 SH: Boucle bornée
        max_presences = sh_get_config("SH_MAX_PRESENCES_BATCH", 500, int)

        for presence_data in sh_bounded_loop(data.presences, max_presences, "warn"):
            stage = db.query(Stage).filter(
                Stage.id == presence_data.stage_id,
                Stage.deleted_at.is_(None)
            ).first()

            if not stage:
                continue

            if current_user.role == RoleEnum.CADRE and stage.service_id != current_user.service_id:
                continue

            existing = db.query(Presence).filter(
                Presence.stage_id == presence_data.stage_id,
                Presence.date_presence == presence_data.date_presence
            ).first()

            if existing:
                existing.etat = presence_data.etat
                existing.commentaire = presence_data.commentaire
                existing.updated_by = current_user.id
                results.append(existing)
            else:
                presence = Presence(
                    **presence_data.model_dump(),
                    updated_by=current_user.id
                )
                db.add(presence)
                results.append(presence)

        db.commit()

        for r in results:
            db.refresh(r)

        sh_error(
            None,
            code_error="BULK_PRESENCES_SUCCESS",
            type_p="INFO",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id,
            action="bulk_update_presences",
            context={"count": len(results)}
        )

        return results

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="BULK_PRESENCES_1",
            type_p="ERROR",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la mise à jour en masse", "correlation_id": correlation_id}
        )


@router.patch("/{presence_id}", response_model=PresenceResponse)
async def update_presence(
    presence_id: int,
    presence_data: PresenceUpdate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Met à jour une présence.
    Criticité: C3 (STANDARD)
    """
    correlation_id = sh_generate_correlation_id("PRESENCE", "C3")

    try:
        presence = db.query(Presence).filter(Presence.id == presence_id).first()

        if not presence:
            sh_error(
                None,
                code_error="UPDATE_PRESENCE_NOT_FOUND",
                type_p="WARNING",
                criticality="C3",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"presence_id": presence_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Présence non trouvée", "correlation_id": correlation_id}
            )

        stage = db.query(Stage).filter(Stage.id == presence.stage_id).first()

        if current_user.role == RoleEnum.CADRE and stage.service_id != current_user.service_id:
            sh_error(
                None,
                code_error="UPDATE_PRESENCE_ACCESS_DENIED",
                type_p="WARNING",
                criticality="C3",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"presence_id": presence_id}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"message": "Accès non autorisé", "correlation_id": correlation_id}
            )

        for field, value in presence_data.model_dump(exclude_unset=True).items():
            setattr(presence, field, value)

        presence.updated_by = current_user.id
        db.commit()
        db.refresh(presence)

        sh_error(
            None,
            code_error="PATCH_PRESENCE_SUCCESS",
            type_p="INFO",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id,
            action="update_presence",
            context={"presence_id": presence_id}
        )

        return presence

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="PATCH_PRESENCE_1",
            type_p="ERROR",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la mise à jour de la présence", "correlation_id": correlation_id}
        )
