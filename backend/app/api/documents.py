"""
Module Documents - Règles SH appliquées
Criticité: C2 (IMPORTANT) - Gestion documentaire
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import os
import uuid
import aiofiles
from app.core.database import get_db
from app.core.config import settings
from app.core.sh import (
    sh_error, sh_generate_correlation_id, sh_format,
    sh_bounded_loop, sh_get_config
)
from app.schemas.schemas import DocumentResponse, TypeDocumentEnum, RoleEnum
from app.models.models import Document, Stage, Utilisateur
from app.api.deps import get_current_user, get_coordinatrice_or_dsi

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/stage/{stage_id}", response_model=List[DocumentResponse])
async def list_documents_stage(
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Liste les documents d'un stage.
    Criticité: C2 (IMPORTANT)
    """
    correlation_id = sh_generate_correlation_id("DOC", "C2")

    try:
        stage = db.query(Stage).filter(
            Stage.id == stage_id,
            Stage.deleted_at.is_(None)
        ).first()

        if not stage:
            sh_error(
                None,
                code_error="LIST_DOCS_STAGE_NOT_FOUND",
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

        if current_user.role == RoleEnum.CADRE and stage.service_id != current_user.service_id:
            sh_error(
                None,
                code_error="LIST_DOCS_ACCESS_DENIED",
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

        max_docs = sh_get_config("MAX_DOCS_PER_STAGE", settings.MAX_DOCS_PER_STAGE, int)
        documents = db.query(Document).filter(
            Document.stage_id == stage_id,
            Document.deleted_at.is_(None)
        ).order_by(Document.created_at.desc()).limit(max_docs).all()

        return documents

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="LIST_DOCS_1",
            type_p="ERROR",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la récupération des documents", "correlation_id": correlation_id}
        )


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    stage_id: int = Form(...),
    type_document: TypeDocumentEnum = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_coordinatrice_or_dsi)
):
    """
    Upload d'un document.
    Criticité: C2 (IMPORTANT)
    """
    correlation_id = sh_generate_correlation_id("DOC", "C2")

    try:
        stage = db.query(Stage).filter(
            Stage.id == stage_id,
            Stage.deleted_at.is_(None)
        ).first()

        if not stage:
            sh_error(
                None,
                code_error="UPLOAD_DOC_STAGE_NOT_FOUND",
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

        doc_count = db.query(Document).filter(
            Document.stage_id == stage_id,
            Document.deleted_at.is_(None)
        ).count()

        max_docs = sh_get_config("MAX_DOCS_PER_STAGE", settings.MAX_DOCS_PER_STAGE, int)
        if doc_count >= max_docs:
            sh_error(
                None,
                code_error="UPLOAD_DOC_MAX_REACHED",
                type_p="WARNING",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"stage_id": stage_id, "count": doc_count, "max": max_docs}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": sh_format("Nombre maximum de documents atteint ({max})", max=max_docs),
                    "correlation_id": correlation_id
                }
            )

        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            sh_error(
                None,
                code_error="UPLOAD_DOC_INVALID_EXT",
                type_p="WARNING",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"extension": file_ext}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": sh_format("Extension non autorisée. Extensions acceptées: {ext}", ext=str(settings.ALLOWED_EXTENSIONS)),
                    "correlation_id": correlation_id
                }
            )

        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            max_mo = settings.MAX_UPLOAD_SIZE // (1024 * 1024)
            sh_error(
                None,
                code_error="UPLOAD_DOC_TOO_LARGE",
                type_p="WARNING",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"size": len(content), "max": settings.MAX_UPLOAD_SIZE}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": sh_format("Fichier trop volumineux (max {max_mo} Mo)", max_mo=max_mo),
                    "correlation_id": correlation_id
                }
            )

        filename = sh_format("{uuid}{ext}", uuid=str(uuid.uuid4()), ext=file_ext)
        upload_path = os.path.join(settings.UPLOAD_DIR, str(stage_id))
        os.makedirs(upload_path, exist_ok=True)
        file_path = os.path.join(upload_path, filename)

        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        document = Document(
            stage_id=stage_id,
            type_document=type_document,
            nom_document=file.filename,
            chemin_fichier=file_path,
            taille=len(content),
            mime_type=file.content_type,
            uploaded_by=current_user.id
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        sh_error(
            None,
            code_error="UPLOAD_DOC_SUCCESS",
            type_p="INFO",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id,
            action="upload_document",
            context={"document_id": document.id, "stage_id": stage_id, "type": type_document.value}
        )

        return document

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="UPLOAD_DOC_1",
            type_p="ERROR",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de l'upload du document", "correlation_id": correlation_id}
        )


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Téléchargement d'un document.
    Criticité: C2 (IMPORTANT)
    """
    correlation_id = sh_generate_correlation_id("DOC", "C2")

    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.deleted_at.is_(None)
        ).first()

        if not document:
            sh_error(
                None,
                code_error="DOWNLOAD_DOC_NOT_FOUND",
                type_p="WARNING",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"document_id": document_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Document non trouvé", "correlation_id": correlation_id}
            )

        stage = db.query(Stage).filter(Stage.id == document.stage_id).first()
        if current_user.role == RoleEnum.CADRE and stage.service_id != current_user.service_id:
            sh_error(
                None,
                code_error="DOWNLOAD_DOC_ACCESS_DENIED",
                type_p="WARNING",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"document_id": document_id}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"message": "Accès non autorisé", "correlation_id": correlation_id}
            )

        if not os.path.exists(document.chemin_fichier):
            sh_error(
                None,
                code_error="DOWNLOAD_DOC_FILE_MISSING",
                type_p="ERROR",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"document_id": document_id, "path": document.chemin_fichier}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Fichier non trouvé sur le serveur", "correlation_id": correlation_id}
            )

        sh_error(
            None,
            code_error="DOWNLOAD_DOC_SUCCESS",
            type_p="INFO",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id,
            action="download_document",
            context={"document_id": document_id}
        )

        return FileResponse(
            document.chemin_fichier,
            filename=document.nom_document,
            media_type=document.mime_type
        )

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="DOWNLOAD_DOC_1",
            type_p="ERROR",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors du téléchargement", "correlation_id": correlation_id}
        )


@router.patch("/{document_id}/validate", response_model=DocumentResponse)
async def validate_document(
    document_id: int,
    valide: bool = True,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_coordinatrice_or_dsi)
):
    """
    Validation d'un document.
    Criticité: C2 (IMPORTANT)
    """
    correlation_id = sh_generate_correlation_id("DOC", "C2")

    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.deleted_at.is_(None)
        ).first()

        if not document:
            sh_error(
                None,
                code_error="VALIDATE_DOC_NOT_FOUND",
                type_p="WARNING",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"document_id": document_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Document non trouvé", "correlation_id": correlation_id}
            )

        document.valide = valide
        db.commit()
        db.refresh(document)

        sh_error(
            None,
            code_error="VALIDATE_DOC_SUCCESS",
            type_p="INFO",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id,
            action="validate_document",
            context={"document_id": document_id, "valide": valide}
        )

        return document

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="VALIDATE_DOC_1",
            type_p="ERROR",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la validation", "correlation_id": correlation_id}
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_coordinatrice_or_dsi)
):
    """
    Suppression d'un document (soft delete).
    Criticité: C2 (IMPORTANT)
    """
    correlation_id = sh_generate_correlation_id("DOC", "C2")

    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.deleted_at.is_(None)
        ).first()

        if not document:
            sh_error(
                None,
                code_error="DELETE_DOC_NOT_FOUND",
                type_p="WARNING",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={"document_id": document_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Document non trouvé", "correlation_id": correlation_id}
            )

        document.deleted_at = func.now()
        db.commit()

        sh_error(
            None,
            code_error="DELETE_DOC_SUCCESS",
            type_p="INFO",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id,
            action="delete_document",
            context={"document_id": document_id}
        )

        return None

    except HTTPException:
        raise
    except Exception as e:
        sh_error(
            e,
            code_error="DELETE_DOC_1",
            type_p="ERROR",
            criticality="C2",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de la suppression", "correlation_id": correlation_id}
        )
