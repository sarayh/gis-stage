"""
Module Services - Règles SH appliquées
Criticité: C3 (STANDARD) - Gestion des services
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.sh import (
    sh_error, sh_generate_correlation_id, sh_get_config
)
from app.schemas.schemas import ServiceCreate, ServiceResponse
from app.models.models import Service, Utilisateur
from app.api.deps import get_current_user, get_coordinatrice_or_dsi

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("", response_model=List[ServiceResponse])
async def list_services(
    actif_only: bool = True,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Liste des services.
    Criticité: C3 (STANDARD)
    """
    correlation_id = sh_generate_correlation_id("SERVICE", "C3")

    try:
        query = db.query(Service).filter(Service.deleted_at.is_(None))

        if actif_only:
            query = query.filter(Service.actif == True)

        # Règle 1 SH: Limite configurable
        max_services = sh_get_config("SH_MAX_SERVICES", 100, int)
        services = query.order_by(Service.nom_service).limit(max_services).all()

        return services

    except Exception as e:
        sh_error(
            e,
            code_error="LIST_SERVICES_1",
            type_p="ERROR",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la récupération des services", "correlation_id": correlation_id}
        )


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Récupère un service par son ID.
    Criticité: C3 (STANDARD)
    """
    correlation_id = sh_generate_correlation_id("SERVICE", "C3")

    try:
        service = db.query(Service).filter(
            Service.id == service_id,
            Service.deleted_at.is_(None)
        ).first()

        if not service:
            sh_error(
                None,
                code_error="GET_SERVICE_NOT_FOUND",
                type_p="WARNING",
                criticality="C3",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"service_id": service_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Service non trouvé", "correlation_id": correlation_id}
            )

        return service

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="GET_SERVICE_1",
            type_p="ERROR",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la récupération du service", "correlation_id": correlation_id}
        )


@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_data: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_coordinatrice_or_dsi)
):
    """
    Crée un nouveau service.
    Criticité: C3 (STANDARD)
    """
    correlation_id = sh_generate_correlation_id("SERVICE", "C3")

    try:
        existing = db.query(Service).filter(
            Service.nom_service == service_data.nom_service
        ).first()

        if existing:
            sh_error(
                None,
                code_error="CREATE_SERVICE_ALREADY_EXISTS",
                type_p="WARNING",
                criticality="C3",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"nom_service": service_data.nom_service}
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": "Un service avec ce nom existe déjà", "correlation_id": correlation_id}
            )

        service = Service(**service_data.model_dump())
        db.add(service)
        db.commit()
        db.refresh(service)

        sh_error(
            None,
            code_error="CREATE_SERVICE_SUCCESS",
            type_p="INFO",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id,
            action="create_service",
            context={"service_id": service.id, "nom": service_data.nom_service}
        )

        return service

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="CREATE_SERVICE_1",
            type_p="ERROR",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la création du service", "correlation_id": correlation_id}
        )


@router.patch("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: int,
    service_data: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_coordinatrice_or_dsi)
):
    """
    Met à jour un service.
    Criticité: C3 (STANDARD)
    """
    correlation_id = sh_generate_correlation_id("SERVICE", "C3")

    try:
        service = db.query(Service).filter(
            Service.id == service_id,
            Service.deleted_at.is_(None)
        ).first()

        if not service:
            sh_error(
                None,
                code_error="UPDATE_SERVICE_NOT_FOUND",
                type_p="WARNING",
                criticality="C3",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"service_id": service_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Service non trouvé", "correlation_id": correlation_id}
            )

        for field, value in service_data.model_dump(exclude_unset=True).items():
            setattr(service, field, value)

        db.commit()
        db.refresh(service)

        sh_error(
            None,
            code_error="UPDATE_SERVICE_SUCCESS",
            type_p="INFO",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id,
            action="update_service",
            context={"service_id": service_id}
        )

        return service

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="UPDATE_SERVICE_1",
            type_p="ERROR",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la mise à jour du service", "correlation_id": correlation_id}
        )
