# Documentation Fonctionnelle - GIS-Stage

## 1. Présentation du Projet

### Objectif

GIS-Stage est une application web de gestion des stages hospitaliers pour le Centre Hospitalier de Gisors. Elle permet de :

- Gérer les demandes de stages des étudiants
- Suivre le cycle de vie complet d'un stage
- Gérer les documents administratifs
- Suivre les présences des stagiaires
- Générer des rapports et statistiques

### Utilisateurs Cibles

| Rôle | Description | Accès |
|------|-------------|-------|
| **Coordinatrice** | Coordinatrice des stages | Accès complet à toutes les fonctionnalités |
| **Cadre de service** | Responsable d'un service | Accès limité à son service |
| **DSI** | Direction des Systèmes d'Information | Accès administratif |

---

## 2. Entités Métier

### Étudiant

Un étudiant représente une personne effectuant un stage à l'hôpital.

**Informations** :
- Code EGIS (identifiant unique généré automatiquement)
- Nom, prénom
- Date et lieu de naissance
- Coordonnées (email, téléphone, adresse)
- Formation suivie
- Établissement d'origine
- Représentant légal (si mineur)

### Stage

Un stage représente une période de formation d'un étudiant dans un service.

**Informations** :
- Étudiant concerné
- Service d'accueil
- Établissement d'origine
- Enseignant référent
- Dates (début, fin, demande)
- Statut du stage
- Documents associés
- Suivi des présences

### Service

Un service représente un département de l'hôpital pouvant accueillir des stagiaires.

**Informations** :
- Nom du service
- Code
- Statut actif/inactif

### Établissement

Un établissement représente une école ou université partenaire.

**Informations** :
- Nom
- Adresse complète
- Coordonnées de contact

### Document

Un document est une pièce administrative liée à un stage.

**Types** :
- Convention de stage
- Évaluation
- Carnet de vaccination
- Attestation
- Autre

---

## 3. Cycle de Vie d'un Stage

### États Possibles

```
┌──────────────┐
│  BROUILLON   │ ← État initial
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│    VALIDÉ    │────▶│    REFUSÉ    │
└──────┬───────┘     └──────────────┘
       │                    │
       ▼                    │
┌──────────────┐            │
│ CONVENTIONNÉ │            │
└──────┬───────┘            │
       │                    │
       ▼                    │
┌──────────────┐            │
│   EN COURS   │            │
└──────┬───────┘            │
       │                    │
       ▼                    │
┌──────────────┐            │
│   TERMINÉ    │ (État final)
└──────────────┘            │
                            │
┌──────────────┐            │
│    ANNULÉ    │◀───────────┘
└──────────────┘
```

### Transitions Autorisées

| État actuel | Transitions possibles |
|-------------|----------------------|
| BROUILLON | → VALIDÉ, REFUSÉ, ANNULÉ |
| VALIDÉ | → CONVENTIONNÉ, BROUILLON, ANNULÉ |
| CONVENTIONNÉ | → EN_COURS, VALIDÉ, ANNULÉ |
| EN_COURS | → TERMINÉ, ANNULÉ |
| TERMINÉ | (aucune - état final) |
| ANNULÉ | → BROUILLON, VALIDÉ |
| REFUSÉ | → BROUILLON |

### Règles Métier

1. **Refus** : Un motif de refus est obligatoire
2. **Terminé** : Un stage terminé ne peut plus être modifié
3. **Dates** : La date de fin doit être postérieure à la date de début
4. **Documents** : Maximum 10 documents par stage
5. **Fichiers** : Taille max 5 Mo, formats PDF/DOC/DOCX/JPG/PNG

---

## 4. Gestion des Accès

### Permissions par Rôle

| Fonctionnalité | Coordinatrice | Cadre | DSI |
|----------------|:-------------:|:-----:|:---:|
| Voir tous les stages | ✅ | ❌ (son service) | ✅ |
| Créer un stage | ✅ | ❌ | ✅ |
| Modifier un stage | ✅ | ⚠️ (commentaire) | ✅ |
| Supprimer un stage | ✅ | ❌ | ✅ |
| Créer un étudiant | ✅ | ❌ | ✅ |
| Modifier un étudiant | ✅ | ❌ | ✅ |
| Uploader un document | ✅ | ❌ | ✅ |
| Valider un document | ✅ | ❌ | ✅ |
| Saisir les présences | ✅ | ✅ (son service) | ✅ |
| Voir les statistiques | ✅ | ❌ | ✅ |
| Exporter CSV | ✅ | ❌ | ✅ |

### Restriction Cadre de Service

Un cadre de service a accès uniquement :
- Aux stages de son service
- Aux étudiants ayant un stage dans son service
- Aux présences de son service
- À la modification du commentaire des stages de son service

---

## 5. Fonctionnalités par Module

### 5.1 Tableau de Bord

**Accès** : Tous les utilisateurs authentifiés

**Contenu** :
- Nombre total de stages
- Stages en cours avec pourcentage
- Stages acceptés avec pourcentage
- Stages refusés avec pourcentage
- Liste des stages en cours actuellement
- Filtrage par service (pour les cadres : leur service uniquement)

### 5.2 Gestion des Stages

#### Liste des Stages
- Recherche par nom/prénom/code EGIS
- Filtres : service, établissement, statut, dates, année
- Tri par date de début (par défaut décroissant)
- Pagination (20 éléments par page)
- Badge de statut coloré

#### Détail d'un Stage
- Informations complètes de l'étudiant
- Service et établissement d'accueil
- Enseignant référent
- Dates et durée calculée en semaines
- Historique des statuts
- Actions : changer statut, ajouter commentaire

#### Création/Modification
- Sélection de l'étudiant
- Sélection du service
- Sélection de l'établissement (auto-complété si étudiant sélectionné)
- Sélection de l'enseignant référent
- Saisie des dates (validation : fin > début)
- Formation
- Commentaire

### 5.3 Gestion des Étudiants

#### Liste des Étudiants
- Recherche par nom/prénom/code EGIS/email
- Filtre par établissement
- Filtre par formation
- Pagination

#### Détail d'un Étudiant
- Informations personnelles
- Coordonnées
- Établissement d'origine
- Représentant légal (si renseigné)
- Liste des stages associés

#### Création/Modification
- Code EGIS généré automatiquement à la création
- Champs obligatoires : nom, prénom
- Champs optionnels : date de naissance, coordonnées, formation

### 5.4 Gestion des Documents

#### Documents d'un Stage
- Liste des documents avec type et statut de validation
- Téléchargement
- Upload (Coordinatrice/DSI)
- Validation (Coordinatrice/DSI)
- Suppression (Coordinatrice/DSI)

#### Upload de Document
- Sélection du type de document
- Sélection du fichier
- Validation :
  - Extensions autorisées : PDF, DOC, DOCX, JPG, JPEG, PNG
  - Taille max : 5 Mo
  - Limite : 10 documents par stage

### 5.5 Suivi des Présences

#### Présences d'un Stage
- Liste des présences par date
- États possibles :
  - Présent
  - Absent
  - Absent justifié
  - Non renseigné
- Commentaire optionnel

#### Saisie des Présences
- Saisie individuelle
- Saisie en masse (bulk update) - max 500 par requête
- Traçabilité : qui a modifié et quand

### 5.6 Calendrier

**Accès** : Tous les utilisateurs authentifiés

**Fonctionnalités** :
- Vue mensuelle des stages par service
- Sélection du mois et de l'année
- Filtrage par service
- Affichage des stages en cours, validés et conventionnés
- Couleurs selon le statut

### 5.7 Statistiques et Rapports

**Accès** : Coordinatrice et DSI

#### Statistiques Annuelles
- Total des stages
- Stages acceptés (validés + conventionnés + en cours + terminés)
- Stages refusés
- Stages en cours
- Stages terminés
- Répartition par service
- Répartition par établissement
- Taux d'acceptation

#### Export CSV
- Export des stages avec filtres
- Colonnes : Code EGIS, Nom, Prénom, Email, Formation, Établissement, Service, Dates, Statut

#### Rapports
- Stages acceptés
- Stages refusés (avec motif)
- Rapport par service
- Rapport prévisionnel

---

## 6. Types de Documents

| Type | Description | Usage |
|------|-------------|-------|
| **CONVENTION** | Convention de stage signée | Obligatoire pour passer en CONVENTIONNÉ |
| **EVALUATION** | Fiche d'évaluation | À la fin du stage |
| **VACCINATION** | Carnet de vaccination | Selon les services |
| **ATTESTATION** | Attestation diverse | Variable |
| **AUTRE** | Tout autre document | Variable |

---

## 7. États de Présence

| État | Description | Couleur |
|------|-------------|---------|
| **PRESENT** | L'étudiant était présent | Vert |
| **ABSENT** | L'étudiant était absent | Rouge |
| **ABSENT_JUSTIFIE** | Absence justifiée (maladie, etc.) | Orange |
| **NON_RENSEIGNE** | Pas encore saisi | Gris |

---

## 8. Scénarios d'Utilisation

### Scénario 1 : Création d'un nouveau stage

1. La coordinatrice crée l'étudiant s'il n'existe pas
2. Elle crée un nouveau stage (statut BROUILLON)
3. Elle complète les informations et passe en VALIDÉ
4. L'étudiant fournit les documents nécessaires
5. Une fois la convention signée, passage en CONVENTIONNÉ
6. Au démarrage effectif, passage en EN_COURS
7. À la fin du stage, passage en TERMINÉ

### Scénario 2 : Refus d'un stage

1. Un stage en BROUILLON est examiné
2. La coordinatrice décide de refuser
3. Elle saisit un motif de refus obligatoire
4. Le stage passe en REFUSÉ
5. Si reconsidération, possibilité de repasser en BROUILLON

### Scénario 3 : Suivi quotidien par un cadre

1. Le cadre se connecte
2. Il voit uniquement les stages de son service
3. Il saisit les présences du jour
4. Il peut ajouter des commentaires sur les stages
5. Il ne peut pas modifier les autres informations

### Scénario 4 : Génération de rapports

1. La coordinatrice accède aux statistiques
2. Elle sélectionne l'année
3. Elle consulte les métriques globales
4. Elle exporte les données en CSV pour traitement externe

---

## 9. Notifications et Alertes

### Système d'Emails

L'application dispose d'une file d'attente d'emails pour :
- Notifications de changement de statut
- Alertes de documents manquants
- Rappels de fin de stage

### Messages d'Interface

- **Succès** : Toast vert en haut à droite
- **Erreur** : Toast rouge avec message explicite
- **Confirmation** : Modal avant actions critiques

---

## 10. Limites et Contraintes

| Limite | Valeur | Description |
|--------|--------|-------------|
| Stages par an | 2000 | Maximum de stages créés par année |
| Étudiants | 5000 | Maximum d'étudiants dans le système |
| Documents/stage | 10 | Maximum de documents par stage |
| Taille fichier | 5 Mo | Taille maximale d'un document |
| Présences/batch | 500 | Maximum de présences en mise à jour groupée |
| Export CSV | 10000 | Maximum de lignes exportables |
| Requêtes/minute | 30 | Limite de débit par utilisateur |
| Token accès | 60 min | Durée de validité du token d'accès |
| Token refresh | 7 jours | Durée de validité du token de rafraîchissement |

---

## 11. Glossaire

| Terme | Définition |
|-------|------------|
| **EGIS** | Identifiant unique étudiant (format: EGIS-XXXX) |
| **Convention** | Document officiel formalisant le stage |
| **Cadre** | Responsable d'un service hospitalier |
| **Coordinatrice** | Personne en charge de la gestion des stages |
| **Soft delete** | Suppression logique (données conservées mais masquées) |
| **Correlation ID** | Identifiant de traçabilité des requêtes |
