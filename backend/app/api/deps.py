"""
Module de dépendances d'authentification - Règles SH appliquées
Criticité: C1 (VITAL) - Sécurité et authentification
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.security import decode_token
from app.core.sh import (
    sh_get_val, sh_error, sh_generate_correlation_id, sh_format
)
from app.models.models import Utilisateur, RoleEnum

security = HTTPBearer()


def _create_auth_error(
    status_code: int,
    detail: str,
    code_error: str,
    correlation_id: str,
    context: dict = None
) -> HTTPException:
    """
    Crée une erreur d'authentification avec log structuré.
    Règle 0: Observer et comprendre - Log complet pour diagnostic.
    """
    sh_error(
        None,
        code_error=code_error,
        type_p="WARNING",
        criticality="C1",
        correlation_id=correlation_id,
        context=context or {}
    )
    return HTTPException(
        status_code=status_code,
        detail={"message": detail, "correlation_id": correlation_id},
        headers={"WWW-Authenticate": "Bearer"} if status_code == 401 else None
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Utilisateur:
    """
    Récupère l'utilisateur courant depuis le token JWT.
    Criticité: C1 (VITAL) - Point d'entrée sécurité.
    """
    correlation_id = sh_generate_correlation_id("AUTH", "C1")

    try:
        token = credentials.credentials
        payload = decode_token(token)

        if payload is None:
            raise _create_auth_error(
                status.HTTP_401_UNAUTHORIZED,
                "Token invalide ou expiré",
                "AUTH_TOKEN_INVALID",
                correlation_id
            )

        # Règle SH: sh_get_val au lieu de .get()
        token_type = sh_get_val(payload, "type", "")
        if token_type != "access":
            raise _create_auth_error(
                status.HTTP_401_UNAUTHORIZED,
                "Type de token invalide",
                "AUTH_TOKEN_TYPE_INVALID",
                correlation_id,
                {"token_type": token_type}
            )

        username = sh_get_val(payload, "sub", "")
        if not username:
            raise _create_auth_error(
                status.HTTP_401_UNAUTHORIZED,
                "Token malformé",
                "AUTH_TOKEN_NO_SUB",
                correlation_id
            )

        user = db.query(Utilisateur).filter(Utilisateur.username == username).first()

        if user is None:
            raise _create_auth_error(
                status.HTTP_401_UNAUTHORIZED,
                "Utilisateur non trouvé",
                "AUTH_USER_NOT_FOUND",
                correlation_id,
                {"username": username}
            )

        if not user.actif:
            raise _create_auth_error(
                status.HTTP_403_FORBIDDEN,
                "Compte désactivé",
                "AUTH_USER_DISABLED",
                correlation_id,
                {"user_id": user.id}
            )

        # Log succès pour traçabilité
        sh_error(
            None,
            code_error="AUTH_SUCCESS",
            type_p="INFO",
            criticality="C1",
            correlation_id=correlation_id,
            user_id=user.id,
            context={"username": username}
        )

        return user

    except HTTPException:
        raise
    except Exception as e:
        # Règle SH: except Exception générique toujours en dernier
        sh_error(
            e,
            code_error="AUTH_1",
            type_p="ERROR",
            criticality="C1",
            correlation_id=correlation_id
        )
        raise _create_auth_error(
            status.HTTP_401_UNAUTHORIZED,
            "Erreur d'authentification",
            "AUTH_UNEXPECTED",
            correlation_id
        )


def require_role(allowed_roles: list[RoleEnum]):
    """
    Vérifie que l'utilisateur a un rôle autorisé.
    Criticité: C1 (VITAL) - Contrôle d'accès.
    """
    async def role_checker(current_user: Utilisateur = Depends(get_current_user)):
        correlation_id = sh_generate_correlation_id("AUTH", "C1")

        if current_user.role not in allowed_roles:
            sh_error(
                None,
                code_error="AUTH_ROLE_DENIED",
                type_p="WARNING",
                criticality="C1",
                correlation_id=correlation_id,
                user_id=current_user.id,
                context={
                    "user_role": current_user.role.value if current_user.role else None,
                    "allowed_roles": [r.value for r in allowed_roles]
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "Accès non autorisé pour ce rôle",
                    "correlation_id": correlation_id
                }
            )
        return current_user
    return role_checker


def get_coordinatrice(current_user: Utilisateur = Depends(get_current_user)) -> Utilisateur:
    """Accès réservé à la coordinatrice. Criticité: C1."""
    correlation_id = sh_generate_correlation_id("AUTH", "C1")

    if current_user.role != RoleEnum.COORDINATRICE:
        sh_error(
            None,
            code_error="AUTH_COORDINATRICE_ONLY",
            type_p="WARNING",
            criticality="C1",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Accès réservé à la coordinatrice",
                "correlation_id": correlation_id
            }
        )
    return current_user


def get_dsi(current_user: Utilisateur = Depends(get_current_user)) -> Utilisateur:
    """Accès réservé à la DSI. Criticité: C1."""
    correlation_id = sh_generate_correlation_id("AUTH", "C1")

    if current_user.role != RoleEnum.DSI:
        sh_error(
            None,
            code_error="AUTH_DSI_ONLY",
            type_p="WARNING",
            criticality="C1",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Accès réservé à la DSI",
                "correlation_id": correlation_id
            }
        )
    return current_user


def get_coordinatrice_or_dsi(current_user: Utilisateur = Depends(get_current_user)) -> Utilisateur:
    """Accès réservé à la coordinatrice ou DSI. Criticité: C1."""
    correlation_id = sh_generate_correlation_id("AUTH", "C1")

    if current_user.role not in [RoleEnum.COORDINATRICE, RoleEnum.DSI]:
        sh_error(
            None,
            code_error="AUTH_COORDINATRICE_DSI_ONLY",
            type_p="WARNING",
            criticality="C1",
            correlation_id=correlation_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Accès réservé à la coordinatrice ou DSI",
                "correlation_id": correlation_id
            }
        )
    return current_user
