from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import (
    Etudiant, Stage, Presence, Document,
    Service, Etablissement, EnseignantReferent,
    StatutStageEnum, EtatPresenceEnum, TypeDocumentEnum
)
from datetime import date, timedelta
import random

def seed_more_data():
    db = SessionLocal()

    try:
        services = db.query(Service).all()
        etablissements = db.query(Etablissement).all()
        enseignants = db.query(EnseignantReferent).all()

        prenoms = [
            "Marie", "Thomas", "Léa", "Lucas", "Emma", "Hugo", "Chloé", "Nathan",
            "Camille", "Mathis", "Sarah", "Enzo", "Manon", "Louis", "Julie",
            "Alexandre", "Laura", "Maxime", "Océane", "Antoine", "Clara", "Théo",
            "Pauline", "Quentin", "Anaïs", "Romain", "Justine", "Kevin", "Morgane",
            "Dylan", "Marion", "Florian", "Mélanie", "Julien", "Audrey", "Pierre"
        ]

        noms = [
            "Martin", "Bernard", "Thomas", "Petit", "Robert", "Richard", "Durand",
            "Dubois", "Moreau", "Laurent", "Simon", "Michel", "Lefebvre", "Leroy",
            "Roux", "David", "Bertrand", "Morel", "Fournier", "Girard", "Bonnet",
            "Dupont", "Lambert", "Fontaine", "Rousseau", "Vincent", "Muller", "Lefevre",
            "Faure", "Andre", "Mercier", "Blanc", "Guerin", "Boyer", "Garnier"
        ]

        formations = [
            "Infirmier", "Aide-soignant", "Médecine", "Kinésithérapie",
            "Ergothérapie", "Psychomotricité", "Sage-femme", "Pharmacie",
            "Manipulateur radio", "Technicien de laboratoire"
        ]

        last_etudiant = db.query(Etudiant).order_by(Etudiant.id.desc()).first()
        start_code = int(last_etudiant.code_egis[4:]) + 1 if last_etudiant else 1

        print("Création de 30 étudiants supplémentaires...")
        new_etudiants = []
        for i in range(30):
            prenom = random.choice(prenoms)
            nom = random.choice(noms)
            etudiant = Etudiant(
                code_egis=f"EGIS{start_code + i:04d}",
                nom=nom,
                prenom=prenom,
                email=f"{prenom.lower()}.{nom.lower()}@email.com",
                telephone=f"06{random.randint(10000000, 99999999)}",
                formation=random.choice(formations),
                etablissement_id=random.choice(etablissements).id,
                date_naissance=date(random.randint(1998, 2004), random.randint(1, 12), random.randint(1, 28)),
                lieu_naissance=random.choice(["Gisors", "Rouen", "Évreux", "Paris", "Beauvais", "Vernon"])
            )
            db.add(etudiant)
            new_etudiants.append(etudiant)

        db.commit()
        for e in new_etudiants:
            db.refresh(e)

        print("Création de 50 stages avec différents statuts...")
        all_etudiants = db.query(Etudiant).all()
        statuts = [
            (StatutStageEnum.TERMINE, -120, -60),
            (StatutStageEnum.TERMINE, -90, -30),
            (StatutStageEnum.EN_COURS, -14, 14),
            (StatutStageEnum.EN_COURS, -7, 21),
            (StatutStageEnum.CONVENTIONNE, 7, 35),
            (StatutStageEnum.VALIDE, 14, 42),
            (StatutStageEnum.VALIDE, 21, 49),
            (StatutStageEnum.BROUILLON, 30, 58),
            (StatutStageEnum.REFUSE, 0, 28),
            (StatutStageEnum.ANNULE, -30, -2),
        ]

        motifs_refus = [
            "Pas de place disponible dans le service",
            "Période non compatible avec les besoins du service",
            "Formation non adaptée au service demandé",
            "Quota de stagiaires atteint",
            "Documents incomplets"
        ]

        new_stages = []
        for i in range(50):
            statut_info = random.choice(statuts)
            statut = statut_info[0]
            date_debut = date.today() + timedelta(days=statut_info[1] + random.randint(-5, 5))
            duree_semaines = random.choice([4, 6, 8, 10, 12])
            date_fin = date_debut + timedelta(weeks=duree_semaines)

            stage = Stage(
                etudiant_id=random.choice(all_etudiants).id,
                service_id=random.choice(services).id,
                etablissement_id=random.choice(etablissements).id,
                enseignant_referent_id=random.choice(enseignants).id if enseignants else None,
                formation=random.choice(formations),
                date_debut=date_debut,
                date_fin=date_fin,
                nombre_semaines=duree_semaines,
                statut=statut,
                motif_refus=random.choice(motifs_refus) if statut == StatutStageEnum.REFUSE else None,
                commentaire=f"Stage de {duree_semaines} semaines" if random.random() > 0.5 else None,
                created_by=1
            )
            db.add(stage)
            new_stages.append(stage)

        db.commit()
        for s in new_stages:
            db.refresh(s)

        print("Création des présences pour les stages en cours et terminés...")
        stages_avec_presences = db.query(Stage).filter(
            Stage.statut.in_([StatutStageEnum.EN_COURS, StatutStageEnum.TERMINE])
        ).all()

        etats_presence = [
            EtatPresenceEnum.PRESENT,
            EtatPresenceEnum.PRESENT,
            EtatPresenceEnum.PRESENT,
            EtatPresenceEnum.PRESENT,
            EtatPresenceEnum.ABSENT,
            EtatPresenceEnum.ABSENT_JUSTIFIE,
        ]

        for stage in stages_avec_presences:
            current_date = stage.date_debut
            end_date = min(stage.date_fin, date.today())

            while current_date <= end_date:
                if current_date.weekday() < 5:
                    presence = Presence(
                        stage_id=stage.id,
                        date_presence=current_date,
                        etat=random.choice(etats_presence),
                        updated_by=1
                    )
                    db.add(presence)
                current_date += timedelta(days=1)

        db.commit()

        print("\n=== Données de test créées avec succès ===")

        total_etudiants = db.query(Etudiant).count()
        total_stages = db.query(Stage).count()
        total_presences = db.query(Presence).count()

        print(f"\nStatistiques:")
        print(f"- Étudiants: {total_etudiants}")
        print(f"- Stages: {total_stages}")
        print(f"- Présences: {total_presences}")

        print(f"\nStages par statut:")
        for statut in StatutStageEnum:
            count = db.query(Stage).filter(Stage.statut == statut).count()
            if count > 0:
                print(f"  - {statut.value}: {count}")

        print(f"\nStages par service:")
        for service in services:
            count = db.query(Stage).filter(Stage.service_id == service.id).count()
            if count > 0:
                print(f"  - {service.nom_service}: {count}")

    except Exception as e:
        db.rollback()
        print(f"Erreur: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_more_data()
