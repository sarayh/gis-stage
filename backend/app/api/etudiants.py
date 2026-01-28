"""
Module Etudiants - Règles SH appliquées
Criticité: C2 (IMPORTANT) - Gestion des étudiants
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from typing import Optional, List
from app.core.database import get_db
from app.core.security import generate_egis_code
from app.core.sh import (
    sh_error, sh_generate_correlation_id, sh_format,
    sh_bounded_loop, sh_get_config, sh_sensitive
)
from app.schemas.schemas import (
    EtudiantCreate, EtudiantUpdate, EtudiantResponse,
    EtudiantListResponse, RoleEnum
)
from app.models.models import Etudiant, Utilisateur, Stage
from app.api.deps import get_current_user, get_coordinatrice_or_dsi

router = APIRouter(prefix="/etudiants", tags=["Etudiants"])


@router.get("", response_model=List[EtudiantListResponse])
async def list_etudiants(
    search: Optional[str] = Query(None, description="Recherche par nom, prénom ou code EGIS"),
    etablissement_id: Optional[int] = None,
    formation: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Liste des étudiants avec filtres et pagination.
    Criticité: C2 (IMPORTANT)
    """
    correlation_id = sh_generate_correlation_id("ETUDIANT", "C2")

    try:
        query = db.query(Etudiant).options(
            joinedload(Etudiant.etablissement)
        ).filter(Etudiant.deleted_at.is_(None))

        if search:
            # Règle SH: sh_format au lieu de f-string
            search_term = sh_format("%{search}%", search=search)
            query = query.filter(
                or_(
                    Etudiant.nom.ilike(search_term),
                    Etudiant.prenom.ilike(search_term),
                    Etudiant.code_egis.ilike(search_term),
                    Etudiant.email.ilike(search_term)
                )
            )

        if etablissement_id:
            query = query.filter(Etudiant.etablissement_id == etablissement_id)

        if formation:
            formation_term = sh_format("%{formation}%", formation=formation)
            query = query.filter(Etudiant.formation.ilike(formation_term))

        if current_user.role == RoleEnum.CADRE and current_user.service_id:
            etudiant_ids = db.query(Stage.etudiant_id).filter(
                Stage.service_id == current_user.service_id,
                Stage.deleted_at.is_(None)
            ).distinct()
            query = query.filter(Etudiant.id.in_(etudiant_ids))

        total = query.count()
        etudiants = query.order_by(Etudiant.nom, Etudiant.prenom)\
            .offset((page - 1) * page_size)\
            .limit(page_size)\
            .all()

        sh_error(
            None,
            code_error="LIST_ETUDIANTS_SUCCESS",
            type_p="INFO",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id,
            context={"total": total, "page": page}
        )

        return etudiants

    except Exception as e:
        sh_error(
            e,
            code_error="LIST_ETUDIANTS_1",
            type_p="ERROR",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la récupération des étudiants", "correlation_id": correlation_id}
        )


@router.get("/{etudiant_id}", response_model=EtudiantResponse)
async def get_etudiant(
    etudiant_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Récupère un étudiant par son ID.
    Criticité: C2 (IMPORTANT)
    """
    correlation_id = sh_generate_correlation_id("ETUDIANT", "C2")

    try:
        etudiant = db.query(Etudiant).options(
            joinedload(Etudiant.etablissement),
            joinedload(Etudiant.representant_legal)
        ).filter(
            Etudiant.id == etudiant_id,
            Etudiant.deleted_at.is_(None)
        ).first()

        if not etudiant:
            sh_error(
                None,
                code_error="GET_ETUDIANT_NOT_FOUND",
                type_p="WARNING",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"etudiant_id": etudiant_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Étudiant non trouvé", "correlation_id": correlation_id}
            )

        if current_user.role == RoleEnum.CADRE and current_user.service_id:
            has_stage = db.query(Stage).filter(
                Stage.etudiant_id == etudiant_id,
                Stage.service_id == current_user.service_id,
                Stage.deleted_at.is_(None)
            ).first()
            if not has_stage:
                sh_error(
                    None,
                    code_error="GET_ETUDIANT_ACCESS_DENIED",
                    type_p="WARNING",
                    criticality="C2",
                    correlation_id=correlation_id,
                    user_id=current_user.id,
                    context={"etudiant_id": etudiant_id}
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"message": "Accès non autorisé à cet étudiant", "correlation_id": correlation_id}
                )

        return etudiant

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="GET_ETUDIANT_1",
            type_p="ERROR",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la récupération de l'étudiant", "correlation_id": correlation_id}
        )


@router.get("/code/{code_egis}", response_model=EtudiantResponse)
async def get_etudiant_by_code(
    code_egis: str,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Récupère un étudiant par son code EGIS.
    Criticité: C2 (IMPORTANT)
    """
    correlation_id = sh_generate_correlation_id("ETUDIANT", "C2")

    try:
        etudiant = db.query(Etudiant).options(
            joinedload(Etudiant.etablissement),
            joinedload(Etudiant.representant_legal)
        ).filter(
            Etudiant.code_egis == code_egis.upper(),
            Etudiant.deleted_at.is_(None)
        ).first()

        if not etudiant:
            sh_error(
                None,
                code_error="GET_ETUDIANT_CODE_NOT_FOUND",
                type_p="WARNING",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"code_egis": code_egis}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Étudiant non trouvé", "correlation_id": correlation_id}
            )

        return etudiant

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="GET_ETUDIANT_CODE_1",
            type_p="ERROR",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la récupération de l'étudiant", "correlation_id": correlation_id}
        )


@router.post("", response_model=EtudiantResponse, status_code=status.HTTP_201_CREATED)
async def create_etudiant(
    etudiant_data: EtudiantCreate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_coordinatrice_or_dsi)
):
    """
    Crée un nouvel étudiant.
    Criticité: C2 (IMPORTANT)
    """
    correlation_id = sh_generate_correlation_id("ETUDIANT", "C2")

    try:
        last_etudiant = db.query(Etudiant).order_by(Etudiant.id.desc()).first()
        last_code = last_etudiant.code_egis if last_etudiant else None
        new_code = generate_egis_code(last_code)

        etudiant = Etudiant(
            code_egis=new_code,
            **etudiant_data.model_dump()
        )

        db.add(etudiant)
        db.commit()
        db.refresh(etudiant)

        # Règle SH: Log avec données sensibles masquées (RGPD)
        sh_error(
            None,
            code_error="CREATE_ETUDIANT_SUCCESS",
            type_p="INFO",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id,
            action="create_etudiant",
            context={
                "etudiant_id": etudiant.id,
                "code_egis": new_code,
                "nom": sh_sensitive(etudiant.nom),
                "prenom": sh_sensitive(etudiant.prenom)
            }
        )

        return etudiant

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="CREATE_ETUDIANT_1",
            type_p="ERROR",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la création de l'étudiant", "correlation_id": correlation_id}
        )


@router.patch("/{etudiant_id}", response_model=EtudiantResponse)
async def update_etudiant(
    etudiant_id: int,
    etudiant_data: EtudiantUpdate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_coordinatrice_or_dsi)
):
    """
    Met à jour un étudiant.
    Criticité: C2 (IMPORTANT)
    """
    correlation_id = sh_generate_correlation_id("ETUDIANT", "C2")

    try:
        etudiant = db.query(Etudiant).filter(
            Etudiant.id == etudiant_id,
            Etudiant.deleted_at.is_(None)
        ).first()

        if not etudiant:
            sh_error(
                None,
                code_error="UPDATE_ETUDIANT_NOT_FOUND",
                type_p="WARNING",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"etudiant_id": etudiant_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Étudiant non trouvé", "correlation_id": correlation_id}
            )

        update_data = etudiant_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(etudiant, field, value)

        db.commit()
        db.refresh(etudiant)

        sh_error(
            None,
            code_error="UPDATE_ETUDIANT_SUCCESS",
            type_p="INFO",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id,
            action="update_etudiant",
            context={"etudiant_id": etudiant_id}
        )

        return etudiant

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="UPDATE_ETUDIANT_1",
            type_p="ERROR",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la mise à jour de l'étudiant", "correlation_id": correlation_id}
        )


@router.delete("/{etudiant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_etudiant(
    etudiant_id: int,
    motif: str = Query(..., description="Motif de suppression"),
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_coordinatrice_or_dsi)
):
    """
    Supprime un étudiant (soft delete).
    Criticité: C2 (IMPORTANT)
    """
    correlation_id = sh_generate_correlation_id("ETUDIANT", "C2")

    try:
        etudiant = db.query(Etudiant).filter(
            Etudiant.id == etudiant_id,
            Etudiant.deleted_at.is_(None)
        ).first()

        if not etudiant:
            sh_error(
                None,
                code_error="DELETE_ETUDIANT_NOT_FOUND",
                type_p="WARNING",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"etudiant_id": etudiant_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Étudiant non trouvé", "correlation_id": correlation_id}
            )

        etudiant.deleted_at = func.now()
        etudiant.actif = False

        db.commit()

        sh_error(
            None,
            code_error="DELETE_ETUDIANT_SUCCESS",
            type_p="INFO",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id,
            action="delete_etudiant",
            context={"etudiant_id": etudiant_id, "motif": motif}
        )

        return None

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="DELETE_ETUDIANT_1",
            type_p="ERROR",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la suppression de l'étudiant", "correlation_id": correlation_id}
        )
