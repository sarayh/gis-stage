# GIS-Stage

Système de gestion des stages hospitaliers pour le Centre Hospitalier de Gisors.

## Fonctionnalités

- Gestion complète du cycle de vie des stages (demande, validation, convention, suivi, clôture)
- Gestion des étudiants avec code EGIS unique
- Suivi des présences quotidiennes
- Gestion documentaire (conventions, évaluations, attestations)
- Calendrier des stages par service
- Statistiques et export CSV
- Contrôle d'accès basé sur les rôles (Coordinatrice, Cadre, DSI)

## Stack Technologique

| Composant | Technologies |
|-----------|-------------|
| **Backend** | FastAPI 0.109, Python 3.11, SQLAlchemy 2.0, PostgreSQL 15 |
| **Frontend** | React 18, TypeScript, Vite 5, Tailwind CSS 3.4 |
| **Auth** | JWT (python-jose), HS256 |
| **Infra** | Docker, Docker Compose |

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│    Backend      │────▶│   PostgreSQL    │
│   React/Vite    │     │    FastAPI      │     │    Database     │
│   Port 3092     │     │   Port 8080     │     │   Port 5432     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Installation Rapide

### Prérequis

- Docker et Docker Compose v2
- 4 Go RAM minimum
- 20 Go disque

### 1. Cloner le dépôt

```bash
git clone https://github.com/sarayh/gis-stage.git
cd gis-stage
```

### 2. Configurer l'environnement

```bash
# Backend
cp backend/.env.example backend/.env
nano backend/.env
```

Variables essentielles à configurer :

```bash
# Base de données
DATABASE_URL=postgresql://gis_user:VOTRE_MOT_DE_PASSE@db:5432/gis_stage
POSTGRES_USER=gis_user
POSTGRES_PASSWORD=VOTRE_MOT_DE_PASSE
POSTGRES_DB=gis_stage

# JWT - IMPORTANT: Générer une clé unique
JWT_SECRET_KEY=VOTRE_CLE_SECRETE_64_CARACTERES
```

Générer une clé JWT sécurisée :

```bash
openssl rand -hex 32
```

### 3. Lancer l'application

```bash
docker compose build
docker compose up -d
```

### 4. Vérifier l'installation

```bash
# Vérifier que les containers tournent
docker compose ps

# Test du backend
curl http://localhost:8080/health

# Accéder à l'application
# Frontend: http://localhost:3092
# API: http://localhost:8080/docs
```

## Installation Complète sur un Serveur

### Prérequis Système

```bash
# Mise à jour du système (Ubuntu/Debian)
sudo apt update && sudo apt upgrade -y

# Installation Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Installation Docker Compose v2
sudo apt install -y docker-compose-plugin
```

### Configuration Firewall

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 3092/tcp  # Frontend (dev)
sudo ufw allow 8080/tcp  # Backend API (dev)
sudo ufw enable
```

### Variables d'Environnement Complètes

Fichier `backend/.env` :

```bash
# Application
APP_ENV=production
APP_PORT=8080
APP_DEBUG=false

# Database
DATABASE_URL=postgresql://gis_user:MOT_DE_PASSE_SECURISE@db:5432/gis_stage
POSTGRES_USER=gis_user
POSTGRES_PASSWORD=MOT_DE_PASSE_SECURISE
POSTGRES_DB=gis_stage

# JWT
JWT_SECRET_KEY=CLE_SECRETE_GENEREE_AVEC_OPENSSL
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Uploads
UPLOAD_DIR=/data/uploads
MAX_UPLOAD_SIZE=5242880

# Limites
MAX_STAGES_YEAR=2000
MAX_ETUDIANTS=5000
MAX_DOCS_PER_STAGE=10
RATE_LIMIT_REQUESTS=30

# SH Config (Mission-Critique)
SH_DEFAULT_MAX_ITEMS=10000
SH_MAX_SERVICES=100
SH_MAX_ETABLISSEMENTS=200
SH_MAX_PRESENCES_BATCH=500
SH_CORRELATION_DOMAIN=GIS
```

Fichier `frontend/.env` :

```bash
VITE_API_URL=http://ADRESSE_IP_SERVEUR:8080/api
```

### Créer le Premier Utilisateur Admin

```bash
docker exec -it gis-stage-backend python -c "
from app.core.database import SessionLocal
from app.models.models import Utilisateur, RoleEnum
from app.core.security import get_password_hash

db = SessionLocal()
admin = Utilisateur(
    username='admin',
    email='admin@ch-gisors.fr',
    hashed_password=get_password_hash('VotreMotDePasse123!'),
    nom='Admin',
    prenom='Système',
    role=RoleEnum.DSI,
    actif=True
)
db.add(admin)
db.commit()
print('Utilisateur admin créé')
db.close()
"
```

### Configuration Nginx (Production)

```bash
sudo apt install -y nginx
sudo nano /etc/nginx/sites-available/gis-stage
```

```nginx
server {
    listen 80;
    server_name gis-stage.votre-domaine.fr;

    location / {
        proxy_pass http://127.0.0.1:3092;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://127.0.0.1:8080/api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 10M;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/gis-stage /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### SSL avec Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d gis-stage.votre-domaine.fr
```

### Sauvegarde Automatique

Script `/opt/gis-stage/backup.sh` :

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/gis-stage"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Sauvegarde base de données
docker exec gis-stage-db pg_dump -U gis_user gis_stage > $BACKUP_DIR/db_$DATE.sql

# Sauvegarde uploads
tar -czvf $BACKUP_DIR/uploads_$DATE.tar.gz /opt/gis-stage/uploads_data/

# Nettoyage > 30 jours
find $BACKUP_DIR -type f -mtime +30 -delete
```

```bash
chmod +x /opt/gis-stage/backup.sh
# Crontab: 0 2 * * * /opt/gis-stage/backup.sh
```

## Entités Métier

### Stage

Période de formation d'un étudiant dans un service hospitalier.

**Cycle de vie :**

```
BROUILLON → VALIDÉ → CONVENTIONNÉ → EN_COURS → TERMINÉ
                ↘ REFUSÉ
            (tous) → ANNULÉ
```

### Étudiant

Personne effectuant un stage, identifiée par un code EGIS unique (format: EGIS-XXXX).

### Service

Département hospitalier pouvant accueillir des stagiaires.

### Établissement

École ou université partenaire.

### Document

Pièce administrative liée à un stage :
- Convention de stage
- Évaluation
- Carnet de vaccination
- Attestation

### Présence

Suivi quotidien : PRESENT, ABSENT, ABSENT_JUSTIFIE, NON_RENSEIGNE

## Rôles et Permissions

| Fonctionnalité | Coordinatrice | Cadre | DSI |
|----------------|:-------------:|:-----:|:---:|
| Voir tous les stages | ✅ | ❌ (son service) | ✅ |
| Créer/Modifier stage | ✅ | ❌ | ✅ |
| Supprimer stage | ✅ | ❌ | ✅ |
| Gérer étudiants | ✅ | ❌ | ✅ |
| Upload documents | ✅ | ❌ | ✅ |
| Saisir présences | ✅ | ✅ (son service) | ✅ |
| Voir statistiques | ✅ | ❌ | ✅ |
| Export CSV | ✅ | ❌ | ✅ |

## API REST

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/login` | Authentification |
| `GET /api/stages` | Liste des stages |
| `POST /api/stages` | Créer un stage |
| `GET /api/etudiants` | Liste des étudiants |
| `POST /api/documents` | Upload document |
| `GET /api/presences/stage/{id}` | Présences d'un stage |
| `GET /api/rapports/statistiques-annuelles` | Statistiques |
| `GET /api/rapports/export-csv` | Export CSV |
| `POST /api/seed/generate` | Générer données de test (DSI) |
| `GET /api/seed/statistics` | Statistiques base de données |

Documentation API complète : `http://localhost:8080/docs`

## Collection Postman

Une collection Postman complète est disponible dans le dossier `postman/`.

### Import dans Postman

1. Ouvrir Postman
2. Cliquer sur **Import**
3. Importer les deux fichiers :
   - `postman/GIS-Stage.postman_collection.json` (Collection)
   - `postman/GIS-Stage.postman_environment.json` (Environnement)
4. Sélectionner l'environnement **GIS-Stage Environment** (coin supérieur droit)
5. Configurer les variables d'environnement :
   - `username` : Nom d'utilisateur
   - `password` : Mot de passe

### Variables d'environnement

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `base_url` | URL de l'API | `http://localhost:8080/api` |
| `username` | Nom d'utilisateur | `admin` |
| `password` | Mot de passe | (à configurer) |
| `access_token` | Token JWT (auto-rempli) | - |
| `refresh_token` | Token refresh (auto-rempli) | - |
| `stage_id` | ID du stage courant | `1` |
| `etudiant_id` | ID de l'étudiant courant | `1` |
| `service_id` | ID du service courant | `1` |
| `etablissement_id` | ID de l'établissement | `1` |

### Utilisation

1. Exécuter **Auth > Login** pour obtenir un token (automatiquement sauvegardé)
2. Les autres requêtes utilisent automatiquement le token
3. Les IDs sont automatiquement sauvegardés après création d'entités

### Endpoints inclus

- **Auth** : Login, Refresh, Me, Logout
- **Stages** : CRUD complet, changement de statut, calendrier
- **Étudiants** : CRUD complet, recherche par code EGIS
- **Documents** : Upload, download, validation
- **Présences** : Création, mise à jour, bulk update
- **Services** : Liste, détail
- **Établissements** : Liste, détail
- **Rapports** : Statistiques, export CSV
- **Seed** : Génération de données de test
- **Health** : Vérification de l'état de l'API

## Génération de Données de Test

L'API inclut des endpoints pour générer un jeu de données de test complet, utile pour les démonstrations et les tests.

### Générer les données

```bash
# Authentification (obtenir un token)
TOKEN=$(curl -s -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"VotreMotDePasse"}' | jq -r '.access_token')

# Générer les données de test (30 étudiants, 50 stages par défaut)
curl -X POST "http://localhost:8080/api/seed/generate" \
  -H "Authorization: Bearer $TOKEN"

# Générer avec paramètres personnalisés
curl -X POST "http://localhost:8080/api/seed/generate?nb_etudiants=50&nb_stages=100" \
  -H "Authorization: Bearer $TOKEN"
```

### Données générées

L'endpoint `/api/seed/generate` crée :

| Entité | Quantité | Description |
|--------|----------|-------------|
| **Services** | 15 | Médecine, Chirurgie, Urgences, Pédiatrie, etc. |
| **Établissements** | 12 | IFSI, IFAS, Facultés de médecine, etc. |
| **Enseignants** | 10 | Enseignants référents avec emails |
| **Utilisateurs** | 5 | coordinatrice, cadre_med, cadre_chir, cadre_urg, dsi_test |
| **Étudiants** | 30 (param) | Avec formations, établissements, représentants légaux |
| **Stages** | 50 (param) | Distribution réaliste des statuts |
| **Présences** | Auto | Pour les stages en cours et terminés |

### Distribution des stages

| Statut | Pourcentage | Description |
|--------|-------------|-------------|
| TERMINE | 25% | Stages passés |
| EN_COURS | 15% | Stages actuels |
| CONVENTIONNE | 15% | Convention signée, à venir |
| VALIDE | 20% | Validés, en attente de convention |
| BROUILLON | 10% | En cours de création |
| REFUSE | 10% | Refusés avec motif |
| ANNULE | 5% | Annulés |

### Utilisateurs de test créés

| Username | Rôle | Mot de passe |
|----------|------|--------------|
| `coordinatrice` | COORDINATRICE | (à définir) |
| `cadre_med` | CADRE (Médecine) | (à définir) |
| `cadre_chir` | CADRE (Chirurgie) | (à définir) |
| `cadre_urg` | CADRE (Urgences) | (à définir) |
| `dsi_test` | DSI | (à définir) |

**Note** : Les utilisateurs de test sont créés sans mot de passe. Utilisez le script d'initialisation pour définir leurs mots de passe.

### Réinitialiser les données

```bash
# Supprimer toutes les données de test (irréversible)
curl -X DELETE "http://localhost:8080/api/seed/reset?confirm=true" \
  -H "Authorization: Bearer $TOKEN"
```

### Voir les statistiques

```bash
curl "http://localhost:8080/api/seed/statistics" \
  -H "Authorization: Bearer $TOKEN"
```

## Limites Système

| Limite | Valeur |
|--------|--------|
| Stages par an | 2000 |
| Étudiants | 5000 |
| Documents par stage | 10 |
| Taille fichier | 5 Mo |
| Présences par batch | 500 |
| Export CSV | 10000 lignes |
| Requêtes/minute | 30 |

## Conformité Mission-Critique (SH)

Le backend implémente les règles de codage SH (Safety & Hospital), inspirées des normes aérospatiales et nucléaires :

- **Règle 0** : Logs structurés avec correlation_id unique
- **Règle 1** : Boucles bornées, limites configurables
- **Règle 3** : Machine à états explicite pour les stages
- **RGPD** : Masquage automatique des données sensibles

## Structure du Projet

```
gis-stage/
├── backend/
│   ├── app/
│   │   ├── api/           # Endpoints REST
│   │   ├── core/          # Config, sécurité, SH
│   │   ├── models/        # Modèles SQLAlchemy
│   │   ├── schemas/       # Schémas Pydantic
│   │   └── services/      # Services métier
│   ├── tests/
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/    # Composants React
│   │   ├── pages/         # Pages
│   │   ├── contexts/      # Auth context
│   │   ├── services/      # Clients API
│   │   └── types/         # Types TypeScript
│   └── Dockerfile
├── docs/
│   ├── DOCUMENTATION_TECHNIQUE.md
│   └── DOCUMENTATION_FONCTIONNELLE.md
└── docker-compose.yml
```

## Documentation

- [Documentation Technique](docs/DOCUMENTATION_TECHNIQUE.md)
- [Documentation Fonctionnelle](docs/DOCUMENTATION_FONCTIONNELLE.md)

## Checklist de Déploiement

- [ ] Docker et Docker Compose installés
- [ ] Projet cloné/transféré
- [ ] Fichier `.env` backend configuré
- [ ] Clé JWT unique générée
- [ ] Containers démarrés (`docker compose up -d`)
- [ ] Health check OK (`curl localhost:8080/health`)
- [ ] Utilisateur admin créé
- [ ] Test de connexion réussi
- [ ] (Optionnel) Nginx configuré
- [ ] (Optionnel) SSL Let's Encrypt
- [ ] (Optionnel) Sauvegarde automatique

## Licence

Propriétaire - Centre Hospitalier de Gisors
