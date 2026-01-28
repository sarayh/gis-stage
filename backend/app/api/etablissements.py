"""
Module Etablissements - Règles SH appliquées
Criticité: C3 (STANDARD) - Gestion des établissements
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.sh import (
    sh_error, sh_generate_correlation_id, sh_get_config
)
from app.schemas.schemas import EtablissementCreate, EtablissementResponse
from app.models.models import Etablissement, Utilisateur
from app.api.deps import get_current_user, get_coordinatrice_or_dsi

router = APIRouter(prefix="/etablissements", tags=["Etablissements"])


@router.get("", response_model=List[EtablissementResponse])
async def list_etablissements(
    actif_only: bool = True,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Liste des établissements.
    Criticité: C3 (STANDARD)
    """
    correlation_id = sh_generate_correlation_id("ETABLISSEMENT", "C3")

    try:
        query = db.query(Etablissement).filter(Etablissement.deleted_at.is_(None))

        if actif_only:
            query = query.filter(Etablissement.actif == True)

        # Règle 1 SH: Limite configurable
        max_etablissements = sh_get_config("SH_MAX_ETABLISSEMENTS", 200, int)
        etablissements = query.order_by(Etablissement.nom).limit(max_etablissements).all()

        return etablissements

    except Exception as e:
        sh_error(
            e,
            code_error="LIST_ETABLISSEMENTS_1",
            type_p="ERROR",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la récupération des établissements", "correlation_id": correlation_id}
        )


@router.get("/{etablissement_id}", response_model=EtablissementResponse)
async def get_etablissement(
    etablissement_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Récupère un établissement par son ID.
    Criticité: C3 (STANDARD)
    """
    correlation_id = sh_generate_correlation_id("ETABLISSEMENT", "C3")

    try:
        etablissement = db.query(Etablissement).filter(
            Etablissement.id == etablissement_id,
            Etablissement.deleted_at.is_(None)
        ).first()

        if not etablissement:
            sh_error(
                None,
                code_error="GET_ETABLISSEMENT_NOT_FOUND",
                type_p="WARNING",
                criticality="C3",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"etablissement_id": etablissement_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Établissement non trouvé", "correlation_id": correlation_id}
            )

        return etablissement

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="GET_ETABLISSEMENT_1",
            type_p="ERROR",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la récupération de l'établissement", "correlation_id": correlation_id}
        )


@router.post("", response_model=EtablissementResponse, status_code=status.HTTP_201_CREATED)
async def create_etablissement(
    etablissement_data: EtablissementCreate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_coordinatrice_or_dsi)
):
    """
    Crée un nouvel établissement.
    Criticité: C3 (STANDARD)
    """
    correlation_id = sh_generate_correlation_id("ETABLISSEMENT", "C3")

    try:
        etablissement = Etablissement(**etablissement_data.model_dump())
        db.add(etablissement)
        db.commit()
        db.refresh(etablissement)

        sh_error(
            None,
            code_error="CREATE_ETABLISSEMENT_SUCCESS",
            type_p="INFO",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id,
            action="create_etablissement",
            context={"etablissement_id": etablissement.id, "nom": etablissement_data.nom}
        )

        return etablissement

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="CREATE_ETABLISSEMENT_1",
            type_p="ERROR",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la création de l'établissement", "correlation_id": correlation_id}
        )


@router.patch("/{etablissement_id}", response_model=EtablissementResponse)
async def update_etablissement(
    etablissement_id: int,
    etablissement_data: EtablissementCreate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_coordinatrice_or_dsi)
):
    """
    Met à jour un établissement.
    Criticité: C3 (STANDARD)
    """
    correlation_id = sh_generate_correlation_id("ETABLISSEMENT", "C3")

    try:
        etablissement = db.query(Etablissement).filter(
            Etablissement.id == etablissement_id,
            Etablissement.deleted_at.is_(None)
        ).first()

        if not etablissement:
            sh_error(
                None,
                code_error="UPDATE_ETABLISSEMENT_NOT_FOUND",
                type_p="WARNING",
                criticality="C3",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"etablissement_id": etablissement_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Établissement non trouvé", "correlation_id": correlation_id}
            )

        for field, value in etablissement_data.model_dump(exclude_unset=True).items():
            setattr(etablissement, field, value)

        db.commit()
        db.refresh(etablissement)

        sh_error(
            None,
            code_error="UPDATE_ETABLISSEMENT_SUCCESS",
            type_p="INFO",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id,
            action="update_etablissement",
            context={"etablissement_id": etablissement_id}
        )

        return etablissement

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="UPDATE_ETABLISSEMENT_1",
            type_p="ERROR",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la mise à jour de l'établissement", "correlation_id": correlation_id}
        )
