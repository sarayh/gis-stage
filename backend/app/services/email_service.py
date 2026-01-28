import httpx
from typing import Optional
from app.core.config import settings
from app.models.models import EmailQueue
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    db: Optional[Session] = None
) -> bool:
    try:
        async with httpx.AsyncClient(timeout=settings.SMTP_TIMEOUT) as client:
            response = await client.post(
                settings.API_MAIL,
                json={
                    "to": to_email,
                    "from": settings.SMTP_FROM,
                    "subject": subject,
                    "body": body
                }
            )
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Erreur d'envoi email: {e}")
        if db:
            email_queue = EmailQueue(
                to_email=to_email,
                subject=subject,
                body=body,
                status="pending",
                error_message=str(e)
            )
            db.add(email_queue)
            db.commit()
        return False


async def send_egis_code_email(
    etudiant_email: str,
    etudiant_nom: str,
    etudiant_prenom: str,
    code_egis: str,
    db: Optional[Session] = None
) -> bool:
    subject = f"GIS-Stage - Votre code d'identification : {code_egis}"
    body = f"""
Bonjour {etudiant_prenom} {etudiant_nom},

Votre demande de stage a été validée.

Votre code d'identification unique est : {code_egis}

Ce code vous sera demandé pour votre accueil informatique.

Cordialement,
L'équipe de coordination des stages
Hôpital de Gisors
"""
    return await send_email(etudiant_email, subject, body, db)


async def send_validation_notification(
    cadre_email: str,
    etudiant_nom: str,
    etudiant_prenom: str,
    code_egis: str,
    service: str,
    date_debut: str,
    date_fin: str,
    db: Optional[Session] = None
) -> bool:
    subject = f"GIS-Stage - Nouveau stagiaire : {etudiant_prenom} {etudiant_nom}"
    body = f"""
Bonjour,

Un nouveau stage a été validé pour votre service.

Informations du stagiaire :
- Nom : {etudiant_nom}
- Prénom : {etudiant_prenom}
- Code EGIS : {code_egis}
- Service : {service}
- Période : du {date_debut} au {date_fin}

Cordialement,
L'équipe de coordination des stages
"""
    return await send_email(cadre_email, subject, body, db)


async def send_dsi_notification(
    code_egis: str,
    etudiant_nom: str,
    etudiant_prenom: str,
    service: str,
    date_debut: str,
    db: Optional[Session] = None
) -> bool:
    dsi_email = "dsi@ch-gisors.fr"
    subject = f"GIS-Stage - Création compte informatique : {code_egis}"
    body = f"""
Bonjour,

Merci de créer le compte informatique pour le stagiaire suivant :

- Code EGIS : {code_egis}
- Nom : {etudiant_nom}
- Prénom : {etudiant_prenom}
- Service : {service}
- Date de début : {date_debut}

Cordialement,
L'équipe de coordination des stages
"""
    return await send_email(dsi_email, subject, body, db)
