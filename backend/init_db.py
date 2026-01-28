from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal, Base
from app.models.models import (
    Utilisateur, Service, Etablissement, Etudiant,
    EnseignantReferent, Stage, RoleEnum, StatutStageEnum
)
from datetime import date, timedelta


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if db.query(Utilisateur).count() > 0:
            print("Base de données déjà initialisée")
            return

        services = [
            Service(nom_service="Urgences", code="URG"),
            Service(nom_service="Cardiologie", code="CAR"),
            Service(nom_service="Pédiatrie", code="PED"),
            Service(nom_service="Chirurgie", code="CHI"),
            Service(nom_service="Radiologie", code="RAD"),
            Service(nom_service="Médecine Générale", code="MED"),
            Service(nom_service="Gériatrie", code="GER"),
            Service(nom_service="Psychiatrie", code="PSY"),
        ]
        for s in services:
            db.add(s)
        db.commit()
        print(f"Créé {len(services)} services")

        etablissements = [
            Etablissement(
                nom="IFSI de Gisors",
                adresse="10 rue de l'Hôpital",
                ville="Gisors",
                code_postal="27140",
                email="contact@ifsi-gisors.fr"
            ),
            Etablissement(
                nom="Université de Rouen - Faculté de Médecine",
                adresse="22 Boulevard Gambetta",
                ville="Rouen",
                code_postal="76000",
                email="medecine@univ-rouen.fr"
            ),
            Etablissement(
                nom="IUT Évreux - DUT Génie Biologique",
                adresse="55 rue Saint-Germain",
                ville="Évreux",
                code_postal="27000",
                email="iut-evreux@univ-rouen.fr"
            ),
            Etablissement(
                nom="Lycée Marc Bloch - Bac Pro ASSP",
                adresse="1 rue Albert Camus",
                ville="Val-de-Reuil",
                code_postal="27100",
                email="contact@lycee-marcbloch.fr"
            ),
        ]
        for e in etablissements:
            db.add(e)
        db.commit()
        print(f"Créé {len(etablissements)} établissements")

        service_urgences = db.query(Service).filter(Service.code == "URG").first()
        service_cardio = db.query(Service).filter(Service.code == "CAR").first()

        utilisateurs = [
            Utilisateur(
                username="coordinatrice",
                email="coordinatrice@ch-gisors.fr",
                nom="Martin",
                prenom="Sophie",
                role=RoleEnum.COORDINATRICE
            ),
            Utilisateur(
                username="cadre.urgences",
                email="cadre.urgences@ch-gisors.fr",
                nom="Durand",
                prenom="Pierre",
                role=RoleEnum.CADRE,
                service_id=service_urgences.id
            ),
            Utilisateur(
                username="cadre.cardio",
                email="cadre.cardio@ch-gisors.fr",
                nom="Leroy",
                prenom="Marie",
                role=RoleEnum.CADRE,
                service_id=service_cardio.id
            ),
            Utilisateur(
                username="dsi",
                email="dsi@ch-gisors.fr",
                nom="Bernard",
                prenom="Jean",
                role=RoleEnum.DSI
            ),
        ]
        for u in utilisateurs:
            db.add(u)
        db.commit()
        print(f"Créé {len(utilisateurs)} utilisateurs")

        ifsi = db.query(Etablissement).filter(Etablissement.nom.like("%IFSI%")).first()

        enseignants = [
            EnseignantReferent(
                nom="Petit",
                prenom="Claire",
                email="c.petit@ifsi-gisors.fr",
                telephone="0232123456",
                etablissement_id=ifsi.id
            ),
            EnseignantReferent(
                nom="Moreau",
                prenom="François",
                email="f.moreau@univ-rouen.fr",
                telephone="0235789012"
            ),
        ]
        for e in enseignants:
            db.add(e)
        db.commit()
        print(f"Créé {len(enseignants)} enseignants référents")

        etudiants_data = [
            ("Dupont", "Alice", "alice.dupont@email.com", "Infirmier", ifsi.id),
            ("Martin", "Lucas", "lucas.martin@email.com", "Infirmier", ifsi.id),
            ("Bernard", "Emma", "emma.bernard@email.com", "Aide-soignant", ifsi.id),
            ("Petit", "Hugo", "hugo.petit@email.com", "Médecine", etablissements[1].id),
            ("Robert", "Léa", "lea.robert@email.com", "Infirmier", ifsi.id),
        ]

        for i, (nom, prenom, email, formation, etab_id) in enumerate(etudiants_data, 1):
            etudiant = Etudiant(
                code_egis=f"EGIS{i:04d}",
                nom=nom,
                prenom=prenom,
                email=email,
                formation=formation,
                etablissement_id=etab_id,
                date_naissance=date(2000, 1, 15 + i),
                lieu_naissance="Gisors"
            )
            db.add(etudiant)
        db.commit()
        print(f"Créé {len(etudiants_data)} étudiants")

        etudiants = db.query(Etudiant).all()
        enseignant = db.query(EnseignantReferent).first()
        coordinatrice = db.query(Utilisateur).filter(Utilisateur.role == RoleEnum.COORDINATRICE).first()

        stages_data = [
            (etudiants[0].id, service_urgences.id, ifsi.id, StatutStageEnum.EN_COURS, 0, 8),
            (etudiants[1].id, service_cardio.id, ifsi.id, StatutStageEnum.VALIDE, 14, 10),
            (etudiants[2].id, service_urgences.id, ifsi.id, StatutStageEnum.TERMINE, -60, 6),
            (etudiants[3].id, service_cardio.id, etablissements[1].id, StatutStageEnum.BROUILLON, 30, 12),
            (etudiants[4].id, service_urgences.id, ifsi.id, StatutStageEnum.REFUSE, 7, 4),
        ]

        for etud_id, serv_id, etab_id, statut, offset, weeks in stages_data:
            debut = date.today() + timedelta(days=offset)
            fin = debut + timedelta(weeks=weeks)
            stage = Stage(
                etudiant_id=etud_id,
                service_id=serv_id,
                etablissement_id=etab_id,
                enseignant_referent_id=enseignant.id,
                formation="Stage pratique",
                date_debut=debut,
                date_fin=fin,
                nombre_semaines=weeks,
                statut=statut,
                motif_refus="Pas de place disponible" if statut == StatutStageEnum.REFUSE else None,
                created_by=coordinatrice.id
            )
            db.add(stage)
        db.commit()
        print(f"Créé {len(stages_data)} stages")

        print("\n=== Initialisation terminée ===")
        print("\nComptes utilisateurs de test :")
        print("- coordinatrice (Coordinatrice)")
        print("- cadre.urgences (Cadre - Service Urgences)")
        print("- cadre.cardio (Cadre - Service Cardiologie)")
        print("- dsi (DSI)")

    except Exception as e:
        db.rollback()
        print(f"Erreur lors de l'initialisation: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
