# Documentation Technique - GIS-Stage

## 1. Vue d'ensemble

**Projet** : GIS-Stage
**Description** : Système de gestion des stages hospitaliers pour le CH Gisors
**Version** : 1.0.0

### Stack Technologique

| Couche | Technologies |
|--------|-------------|
| **Backend** | FastAPI 0.109, Python 3.11, SQLAlchemy 2.0, PostgreSQL 15 |
| **Frontend** | React 18, TypeScript, Vite 5, Tailwind CSS 3.4 |
| **Auth** | JWT (python-jose), HS256 |
| **Infra** | Docker, Docker Compose |

### Ports

- Frontend : `3092`
- Backend API : `8080`
- PostgreSQL : `5432`

---

## 2. Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│    Backend      │────▶│   PostgreSQL    │
│   React/Vite    │     │    FastAPI      │     │    Database     │
│   Port 3092     │     │   Port 8080     │     │   Port 5432     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Structure des Dossiers

```
gis-stage/
├── backend/
│   ├── app/
│   │   ├── api/           # Endpoints REST
│   │   │   ├── auth.py
│   │   │   ├── stages.py
│   │   │   ├── etudiants.py
│   │   │   ├── documents.py
│   │   │   ├── presences.py
│   │   │   ├── services.py
│   │   │   ├── etablissements.py
│   │   │   ├── rapports.py
│   │   │   └── deps.py
│   │   ├── core/          # Configuration & utilitaires
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── security.py
│   │   │   └── sh.py
│   │   ├── models/        # Modèles SQLAlchemy
│   │   │   └── models.py
│   │   ├── schemas/       # Schémas Pydantic
│   │   │   └── schemas.py
│   │   └── services/      # Services métier
│   │       └── email_service.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/    # Composants React
│   │   ├── pages/         # Pages de l'application
│   │   ├── contexts/      # Contextes React (Auth)
│   │   ├── services/      # Clients API
│   │   └── types/         # Types TypeScript
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

---

## 3. Base de Données

### Schéma Entité-Relation

```
Utilisateur ──┬── Service ──── Stage ──┬── Document
              │                  │     │
              │                  │     └── Presence
              │                  │
              │                  └── Etudiant ── Etablissement
              │                           │
              │                           └── RepresentantLegal
              │
              └── EnseignantReferent
```

### Tables Principales

#### Utilisateur
```sql
- id (PK)
- username (UNIQUE)
- email (UNIQUE)
- nom, prenom
- role (ENUM: COORDINATRICE, CADRE, DSI)
- service_id (FK)
- actif (BOOLEAN)
- created_at, updated_at
```

#### Stage
```sql
- id (PK)
- etudiant_id (FK)
- service_id (FK)
- etablissement_id (FK)
- enseignant_referent_id (FK)
- formation
- date_demande, date_debut, date_fin
- nombre_semaines
- statut (ENUM)
- motif_refus
- commentaire
- actif, deleted_at
- created_at, updated_at, created_by
```

#### Etudiant
```sql
- id (PK)
- code_egis (UNIQUE)
- nom, prenom
- date_naissance, lieu_naissance
- email, telephone, adresse
- formation
- etablissement_id (FK)
- representant_legal_id (FK)
- actif, deleted_at
```

#### Document
```sql
- id (PK)
- stage_id (FK)
- type_document (ENUM)
- nom_document
- chemin_fichier
- taille, mime_type
- valide (BOOLEAN)
- deleted_at, created_at
- uploaded_by (FK)
```

#### Presence
```sql
- id (PK)
- stage_id (FK)
- date_presence
- etat (ENUM)
- commentaire
- updated_at, updated_by
```

---

## 4. API REST

### Authentification (`/api/auth`)

| Méthode | Endpoint | Description | Accès |
|---------|----------|-------------|-------|
| POST | `/auth/login` | Connexion | Public |
| POST | `/auth/refresh` | Rafraîchir token | Authentifié |
| GET | `/auth/me` | Utilisateur courant | Authentifié |
| POST | `/auth/logout` | Déconnexion | Authentifié |

### Stages (`/api/stages`)

| Méthode | Endpoint | Description | Accès |
|---------|----------|-------------|-------|
| GET | `/stages` | Liste des stages | Authentifié |
| GET | `/stages/{id}` | Détail d'un stage | Authentifié |
| POST | `/stages` | Créer un stage | Coordinatrice/DSI |
| PATCH | `/stages/{id}` | Modifier un stage | Authentifié* |
| DELETE | `/stages/{id}` | Supprimer un stage | Coordinatrice/DSI |
| GET | `/stages/calendrier/service/{id}` | Calendrier service | Authentifié |

*Les cadres ne peuvent modifier que le commentaire

### Étudiants (`/api/etudiants`)

| Méthode | Endpoint | Description | Accès |
|---------|----------|-------------|-------|
| GET | `/etudiants` | Liste des étudiants | Authentifié |
| GET | `/etudiants/{id}` | Détail étudiant | Authentifié |
| GET | `/etudiants/code/{code}` | Par code EGIS | Authentifié |
| POST | `/etudiants` | Créer étudiant | Coordinatrice/DSI |
| PATCH | `/etudiants/{id}` | Modifier étudiant | Coordinatrice/DSI |
| DELETE | `/etudiants/{id}` | Supprimer étudiant | Coordinatrice/DSI |

### Documents (`/api/documents`)

| Méthode | Endpoint | Description | Accès |
|---------|----------|-------------|-------|
| GET | `/documents/stage/{id}` | Documents d'un stage | Authentifié |
| POST | `/documents` | Upload document | Coordinatrice/DSI |
| GET | `/documents/{id}/download` | Télécharger | Authentifié |
| PATCH | `/documents/{id}/validate` | Valider document | Coordinatrice/DSI |
| DELETE | `/documents/{id}` | Supprimer document | Coordinatrice/DSI |

### Présences (`/api/presences`)

| Méthode | Endpoint | Description | Accès |
|---------|----------|-------------|-------|
| GET | `/presences/stage/{id}` | Présences d'un stage | Authentifié |
| POST | `/presences` | Créer/màj présence | Authentifié |
| POST | `/presences/bulk` | Màj en masse (max 500) | Authentifié |
| PATCH | `/presences/{id}` | Modifier présence | Authentifié |

### Rapports (`/api/rapports`)

| Méthode | Endpoint | Description | Accès |
|---------|----------|-------------|-------|
| GET | `/rapports/statistiques-annuelles` | Stats annuelles | Coordinatrice/DSI |
| GET | `/rapports/export-csv` | Export CSV | Coordinatrice/DSI |
| GET | `/rapports/stages-acceptes` | Stages acceptés | Authentifié |
| GET | `/rapports/stages-refuses` | Stages refusés | Coordinatrice/DSI |
| GET | `/rapports/rapport-services` | Rapport par service | Authentifié |

### Données de Test (`/api/seed`)

| Méthode | Endpoint | Description | Accès |
|---------|----------|-------------|-------|
| POST | `/seed/generate` | Générer un jeu de données complet | DSI |
| DELETE | `/seed/reset?confirm=true` | Supprimer les données de test | DSI |
| GET | `/seed/statistics` | Statistiques de la base | Authentifié |

**Note**: Ces endpoints sont destinés au développement et aux démonstrations uniquement.

---

## 5. Authentification JWT

### Configuration

```python
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
```

### Structure du Token

```json
{
  "sub": "username",
  "role": "COORDINATRICE",
  "service_id": 1,
  "user_id": 42,
  "type": "access",
  "exp": 1706472000
}
```

### Flux d'Authentification

```
1. POST /auth/login (username, password)
   ↓
2. Retour: { access_token, refresh_token, token_type }
   ↓
3. Requêtes avec Header: Authorization: Bearer <access_token>
   ↓
4. Token expiré → POST /auth/refresh avec refresh_token
```

---

## 6. Gestion des Fichiers

### Configuration

```python
UPLOAD_DIR = "/data/uploads"
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 Mo
MAX_DOCS_PER_STAGE = 10
ALLOWED_EXTENSIONS = [".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png"]
```

### Structure de Stockage

```
/data/uploads/
├── {stage_id}/
│   ├── {uuid}.pdf
│   ├── {uuid}.docx
│   └── ...
```

### Types de Documents

| Type | Description |
|------|-------------|
| CONVENTION | Convention de stage |
| EVALUATION | Évaluation du stagiaire |
| VACCINATION | Carnet de vaccination |
| ATTESTATION | Attestation diverse |
| AUTRE | Autre document |

---

## 7. Règles SH (Mission-Critique)

### Niveaux de Criticité

| Niveau | Description | Exemples |
|--------|-------------|----------|
| C1 | VITAL | Authentification, tokens |
| C2 | IMPORTANT | Stages, étudiants, documents |
| C3 | STANDARD | Présences, rapports, services |
| C4 | CONFORT | Logout, UI |

### Fonctions Obligatoires

```python
# Lecture sécurisée
sh_get_val(data, "key", default)

# Formatage sécurisé (pas de f-strings)
sh_format("Template {var}", var=value)

# Log structuré
sh_error(e, code_error="CODE", type_p="ERROR", criticality="C2")

# Boucle bornée
for item in sh_bounded_loop(items, max_items, "warn"):

# Configuration avec fallback
sh_get_config("KEY", default, int)

# ID de corrélation
correlation_id = sh_generate_correlation_id("DOMAIN", "C2")

# Masquage RGPD
sh_sensitive(data)  # -> [[data]]
```

### Pattern Exception Obligatoire

```python
try:
    # Code métier
except HTTPException:
    raise
except Exception as e:
    sh_error(e, code_error="FUNCTION_1", ...)
    raise HTTPException(500, {"message": "...", "correlation_id": correlation_id})
```

---

## 8. Configuration Docker

### docker-compose.yml

```yaml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: gis_user
      POSTGRES_PASSWORD: gis_password
      POSTGRES_DB: gis_stage
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U gis_user -d gis_stage"]

  backend:
    build: ./backend
    ports:
      - "8080:8080"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - uploads_data:/data/uploads

  frontend:
    build: ./frontend
    ports:
      - "3092:3092"
    depends_on:
      - backend
```

### Variables d'Environnement

```bash
# Application
APP_ENV=development
APP_PORT=8080

# Database
DATABASE_URL=postgresql://gis_user:gis_password@db:5432/gis_stage

# JWT
JWT_SECRET_KEY=<secret>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Uploads
UPLOAD_DIR=/data/uploads
MAX_UPLOAD_SIZE=5242880

# Limites
MAX_STAGES_YEAR=2000
MAX_ETUDIANTS=5000
MAX_DOCS_PER_STAGE=10
RATE_LIMIT_REQUESTS=30
```

---

## 9. Frontend

### Dépendances Principales

```json
{
  "react": "^18.2.0",
  "react-router-dom": "^6.21.0",
  "@tanstack/react-query": "^5.17.0",
  "axios": "^1.6.2",
  "react-hook-form": "^7.49.0",
  "zod": "^3.22.0",
  "tailwindcss": "^3.4.0",
  "recharts": "^2.10.3"
}
```

### Contexte d'Authentification

```typescript
interface AuthContextType {
  user: Utilisateur | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login(credentials: LoginCredentials): Promise<void>;
  logout(): void;
  hasRole(roles: RoleEnum[]): boolean;
  canAccessService(serviceId: number): boolean;
}
```

### Routes

| Route | Page | Accès |
|-------|------|-------|
| `/login` | Connexion | Public |
| `/` | Dashboard | Authentifié |
| `/stages` | Liste stages | Authentifié |
| `/stages/nouveau` | Créer stage | Coordinatrice/DSI |
| `/stages/:id` | Détail stage | Authentifié |
| `/etudiants` | Liste étudiants | Authentifié |
| `/etudiants/nouveau` | Créer étudiant | Coordinatrice/DSI |
| `/calendrier` | Calendrier | Authentifié |
| `/statistiques` | Statistiques | Coordinatrice/DSI |

---

## 10. Déploiement

### Développement

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080

# Frontend
cd frontend
npm install
npm run dev
```

### Production

```bash
docker-compose up --build -d
```

### Vérification

```bash
# Health check
curl http://localhost:8080/health

# API info
curl http://localhost:8080/
```

---

## 11. Guide d'Installation sur un Nouveau Serveur

### 11.1 Prérequis Système

#### Serveur Linux (Ubuntu/Debian recommandé)

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation des dépendances de base
sudo apt install -y curl git wget gnupg2 software-properties-common
```

#### Docker et Docker Compose

```bash
# Installation de Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Ajouter l'utilisateur au groupe docker
sudo usermod -aG docker $USER

# Installation de Docker Compose (v2)
sudo apt install -y docker-compose-plugin

# Vérification
docker --version
docker compose version
```

#### Configuration Firewall (optionnel)

```bash
# Ouvrir les ports nécessaires
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 3092/tcp  # Frontend (dev)
sudo ufw allow 8080/tcp  # Backend API (dev)
sudo ufw enable
```

### 11.2 Transfert du Projet

#### Option A : Cloner depuis Git

```bash
cd /opt
sudo git clone <URL_REPO> gis-stage
sudo chown -R $USER:$USER gis-stage
cd gis-stage
```

#### Option B : Transfert par SCP

```bash
# Depuis la machine source
scp -r gis-stage/ user@serveur:/opt/

# Ou avec rsync (plus efficace)
rsync -avz --progress gis-stage/ user@serveur:/opt/gis-stage/
```

#### Option C : Archive tar.gz

```bash
# Créer l'archive (machine source)
tar -czvf gis-stage.tar.gz gis-stage/

# Transférer
scp gis-stage.tar.gz user@serveur:/opt/

# Extraire (machine cible)
cd /opt
tar -xzvf gis-stage.tar.gz
```

### 11.3 Configuration de l'Environnement

#### Créer le fichier .env (Backend)

```bash
cd /opt/gis-stage/backend
cp .env.example .env  # Si existe, sinon créer manuellement
nano .env
```

Contenu du fichier `.env` :

```bash
# ===== APPLICATION =====
APP_ENV=production
APP_PORT=8080
APP_DEBUG=false

# ===== DATABASE =====
DATABASE_URL=postgresql://gis_user:VOTRE_MOT_DE_PASSE_SECURISE@db:5432/gis_stage
POSTGRES_USER=gis_user
POSTGRES_PASSWORD=VOTRE_MOT_DE_PASSE_SECURISE
POSTGRES_DB=gis_stage

# ===== JWT (IMPORTANT: Générer une clé unique) =====
JWT_SECRET_KEY=GENERER_UNE_CLE_SECRETE_UNIQUE_DE_64_CARACTERES
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ===== UPLOADS =====
UPLOAD_DIR=/data/uploads
MAX_UPLOAD_SIZE=5242880

# ===== LIMITES =====
MAX_STAGES_YEAR=2000
MAX_ETUDIANTS=5000
MAX_DOCS_PER_STAGE=10
RATE_LIMIT_REQUESTS=30

# ===== SH CONFIG =====
SH_DEFAULT_MAX_ITEMS=10000
SH_MAX_SERVICES=100
SH_MAX_ETABLISSEMENTS=200
SH_MAX_PRESENCES_BATCH=500
SH_CORRELATION_DOMAIN=GIS
```

#### Générer une clé JWT sécurisée

```bash
# Méthode 1 : OpenSSL
openssl rand -hex 32

# Méthode 2 : Python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

#### Créer le fichier .env (Frontend)

```bash
cd /opt/gis-stage/frontend
nano .env
```

Contenu :

```bash
VITE_API_URL=http://ADRESSE_IP_SERVEUR:8080/api
```

### 11.4 Configuration Docker Compose Production

Créer/modifier `docker-compose.prod.yml` :

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: gis-stage-db
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - gis-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: gis-stage-backend
    restart: always
    env_file:
      - ./backend/.env
    ports:
      - "8080:8080"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - uploads_data:/data/uploads
      - ./backend/logs:/app/logs
    networks:
      - gis-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        VITE_API_URL: ${VITE_API_URL:-http://localhost:8080/api}
    container_name: gis-stage-frontend
    restart: always
    ports:
      - "3092:3092"
    depends_on:
      - backend
    networks:
      - gis-network

volumes:
  postgres_data:
    driver: local
  uploads_data:
    driver: local

networks:
  gis-network:
    driver: bridge
```

### 11.5 Lancement de l'Application

#### Première installation

```bash
cd /opt/gis-stage

# Construire les images
docker compose -f docker-compose.prod.yml build

# Démarrer les services
docker compose -f docker-compose.prod.yml up -d

# Vérifier les logs
docker compose -f docker-compose.prod.yml logs -f
```

#### Vérification du déploiement

```bash
# Vérifier que les containers tournent
docker compose -f docker-compose.prod.yml ps

# Test du backend
curl http://localhost:8080/health

# Test du frontend
curl http://localhost:3092
```

### 11.6 Initialisation de la Base de Données

#### Créer le premier utilisateur admin

```bash
# Accéder au container backend
docker exec -it gis-stage-backend bash

# Ou exécuter un script d'initialisation
docker exec -it gis-stage-backend python -c "
from app.core.database import SessionLocal
from app.models.models import Utilisateur, RoleEnum
from app.core.security import get_password_hash

db = SessionLocal()
admin = Utilisateur(
    username='admin',
    email='admin@ch-gisors.fr',
    hashed_password=get_password_hash('MotDePasseSecurise123!'),
    nom='Admin',
    prenom='Système',
    role=RoleEnum.DSI,
    actif=True
)
db.add(admin)
db.commit()
print('Utilisateur admin créé avec succès')
db.close()
"
```

#### Importer des données existantes (optionnel)

```bash
# Copier un dump SQL
scp backup.sql user@serveur:/tmp/

# Restaurer dans le container
docker exec -i gis-stage-db psql -U gis_user -d gis_stage < /tmp/backup.sql
```

### 11.7 Configuration Nginx (Reverse Proxy)

#### Installation de Nginx

```bash
sudo apt install -y nginx
```

#### Configuration du site

```bash
sudo nano /etc/nginx/sites-available/gis-stage
```

Contenu :

```nginx
server {
    listen 80;
    server_name gis-stage.ch-gisors.fr;

    # Redirection HTTPS (décommenter si SSL configuré)
    # return 301 https://$server_name$request_uri;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3092;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # API Backend
    location /api {
        proxy_pass http://127.0.0.1:8080/api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts pour les uploads
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
        client_max_body_size 10M;
    }
}
```

#### Activer le site

```bash
sudo ln -s /etc/nginx/sites-available/gis-stage /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 11.8 Configuration SSL avec Let's Encrypt

```bash
# Installation de Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtenir le certificat
sudo certbot --nginx -d gis-stage.ch-gisors.fr

# Renouvellement automatique (déjà configuré par défaut)
sudo systemctl status certbot.timer
```

### 11.9 Sauvegarde et Restauration

#### Script de sauvegarde automatique

Créer `/opt/gis-stage/backup.sh` :

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/gis-stage"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Sauvegarde base de données
docker exec gis-stage-db pg_dump -U gis_user gis_stage > $BACKUP_DIR/db_$DATE.sql

# Sauvegarde des uploads
tar -czvf $BACKUP_DIR/uploads_$DATE.tar.gz /opt/gis-stage/uploads_data/

# Nettoyage des sauvegardes > 30 jours
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Sauvegarde terminée: $DATE"
```

#### Planification cron

```bash
chmod +x /opt/gis-stage/backup.sh

# Ajouter au crontab (sauvegarde quotidienne à 2h)
crontab -e
# Ajouter : 0 2 * * * /opt/gis-stage/backup.sh >> /var/log/gis-backup.log 2>&1
```

### 11.10 Monitoring et Maintenance

#### Commandes utiles

```bash
# Voir les logs en temps réel
docker compose -f docker-compose.prod.yml logs -f backend

# Redémarrer un service
docker compose -f docker-compose.prod.yml restart backend

# Mettre à jour l'application
git pull
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Nettoyage Docker
docker system prune -a --volumes
```

#### Vérification de santé

```bash
# Script de health check
curl -s http://localhost:8080/health | jq .

# Espace disque
df -h

# Utilisation mémoire des containers
docker stats --no-stream
```

### 11.11 Checklist de Déploiement

- [ ] Serveur avec Docker et Docker Compose installés
- [ ] Projet transféré dans `/opt/gis-stage`
- [ ] Fichier `.env` backend configuré avec mot de passe sécurisé
- [ ] Fichier `.env` frontend avec URL API correcte
- [ ] Clé JWT unique générée
- [ ] Containers démarrés et fonctionnels
- [ ] Utilisateur admin créé
- [ ] Nginx configuré (optionnel)
- [ ] SSL Let's Encrypt (optionnel)
- [ ] Sauvegarde automatique configurée
- [ ] Firewall configuré
- [ ] Test de connexion réussi
