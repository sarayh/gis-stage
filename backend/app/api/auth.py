"""
Module Authentification - Règles SH appliquées
Criticité: C1 (VITAL) - Authentification et tokens
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, decode_token, verify_password
from app.core.sh import (
    sh_get_val, sh_error, sh_generate_correlation_id, sh_sensitive
)
from app.schemas.schemas import Token, LoginRequest, UtilisateurResponse
from app.models.models import Utilisateur
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authentification utilisateur.
    Criticité: C1 (VITAL) - Point d'entrée principal.
    """
    correlation_id = sh_generate_correlation_id("AUTH", "C1")

    try:
        # Validation préventive (Phase 3 SH)
        if not login_data.username:
            sh_error(
                None,
                code_error="LOGIN_USERNAME_EMPTY",
                type_p="WARNING",
                criticality="C1",
                correlation_id=correlation_id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Nom d'utilisateur requis", "correlation_id": correlation_id}
            )

        user = db.query(Utilisateur).filter(
            Utilisateur.username == login_data.username
        ).first()

        if not user:
            # Log avec données sensibles masquées
            sh_error(
                None,
                code_error="LOGIN_USER_NOT_FOUND",
                type_p="WARNING",
                criticality="C1",
                correlation_id=correlation_id,
                context={"username": sh_sensitive(login_data.username)}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"message": "Identifiants incorrects", "correlation_id": correlation_id}
            )

        if not user.actif:
            sh_error(
                None,
                code_error="LOGIN_USER_DISABLED",
                type_p="WARNING",
                criticality="C1",
                correlation_id=correlation_id,
                user_id=user.id
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"message": "Compte désactivé", "correlation_id": correlation_id}
            )

        token_data = {
            "sub": user.username,
            "role": user.role.value,
            "service_id": user.service_id,
            "user_id": user.id
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # Log succès (traçabilité Règle 7)
        sh_error(
            None,
            code_error="LOGIN_SUCCESS",
            type_p="INFO",
            criticality="C1",
            correlation_id=correlation_id,
            user_id=user.id,
            action="login",
            context={"role": user.role.value}
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    except HTTPException:
        raise
    except Exception as e:
        # Règle SH: except Exception générique TOUJOURS en dernier
        sh_error(
            e,
            code_error="LOGIN_1",
            type_p="ERROR",
            criticality="C1",
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors de l'authentification", "correlation_id": correlation_id}
        )


@router.post("/refresh", response_model=Token)
async def refresh_token_endpoint(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Rafraîchissement du token.
    Criticité: C1 (VITAL)
    """
    correlation_id = sh_generate_correlation_id("AUTH", "C1")

    try:
        payload = decode_token(refresh_token)

        # Validation préventive
        if payload is None:
            sh_error(
                None,
                code_error="REFRESH_TOKEN_INVALID",
                type_p="WARNING",
                criticality="C1",
                correlation_id=correlation_id
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"message": "Token de rafraîchissement invalide", "correlation_id": correlation_id}
            )

        # Règle SH: sh_get_val au lieu de .get()
        token_type = sh_get_val(payload, "type", "")
        if token_type != "refresh":
            sh_error(
                None,
                code_error="REFRESH_TOKEN_TYPE_INVALID",
                type_p="WARNING",
                criticality="C1",
                correlation_id=correlation_id,
                context={"token_type": token_type}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"message": "Type de token invalide", "correlation_id": correlation_id}
            )

        username = sh_get_val(payload, "sub", "")
        if not username:
            sh_error(
                None,
                code_error="REFRESH_TOKEN_NO_SUB",
                type_p="WARNING",
                criticality="C1",
                correlation_id=correlation_id
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"message": "Token malformé", "correlation_id": correlation_id}
            )

        user = db.query(Utilisateur).filter(Utilisateur.username == username).first()

        if not user:
            sh_error(
                None,
                code_error="REFRESH_USER_NOT_FOUND",
                type_p="WARNING",
                criticality="C1",
                correlation_id=correlation_id,
                context={"username": username}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"message": "Utilisateur invalide", "correlation_id": correlation_id}
            )

        if not user.actif:
            sh_error(
                None,
                code_error="REFRESH_USER_DISABLED",
                type_p="WARNING",
                criticality="C1",
                correlation_id=correlation_id,
                user_id=user.id
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"message": "Compte désactivé", "correlation_id": correlation_id}
            )

        token_data = {
            "sub": user.username,
            "role": user.role.value,
            "service_id": user.service_id,
            "user_id": user.id
        }

        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)

        sh_error(
            None,
            code_error="REFRESH_SUCCESS",
            type_p="INFO",
            criticality="C1",
            correlation_id=correlation_id,
            user_id=user.id,
            action="refresh_token"
        )

        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )

    except HTTPException:
        raise
    except Exception as e:
        # Règle SH: except Exception générique TOUJOURS en dernier
        sh_error(
            e,
            code_error="REFRESH_1",
            type_p="ERROR",
            criticality="C1",
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Erreur lors du rafraîchissement", "correlation_id": correlation_id}
        )


@router.get("/me", response_model=UtilisateurResponse)
async def get_me(current_user: Utilisateur = Depends(get_current_user)):
    """Récupère l'utilisateur courant. Criticité: C2."""
    return current_user


@router.post("/logout")
async def logout(current_user: Utilisateur = Depends(get_current_user)):
    """Déconnexion. Criticité: C4 (CONFORT)."""
    correlation_id = sh_generate_correlation_id("AUTH", "C4")

    sh_error(
        None,
        code_error="LOGOUT_SUCCESS",
        type_p="INFO",
        criticality="C4",
        correlation_id=correlation_id,
        user_id=current_user.id,
        action="logout"
    )

    return {"message": "Déconnexion réussie", "correlation_id": correlation_id}
