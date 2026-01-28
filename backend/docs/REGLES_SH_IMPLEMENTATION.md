# Implémentation des Règles SH Mission-Critique

## Contexte

Ce document décrit l'implémentation des **Règles de Codage SH** (Safety & Hospital) dans l'application GIS-Stage. Ces règles sont inspirées des bonnes pratiques de l'aérospatial et du nucléaire, adaptées aux systèmes d'information hospitaliers.

## Date d'implémentation
- **Date** : 28 janvier 2026
- **Version** : 1.0.0

---

## 1. Architecture des Règles SH

### 1.1 Niveaux de Criticité

| Niveau | Nom | Description | Fichiers concernés |
|--------|-----|-------------|-------------------|
| **C1** | VITAL | Authentification, sécurité | `auth.py`, `deps.py` |
| **C2** | IMPORTANT | Données métier critiques | `stages.py`, `documents.py`, `etudiants.py` |
| **C3** | STANDARD | Fonctionnalités courantes | `rapports.py`, `presences.py`, `services.py`, `etablissements.py` |
| **C4** | CONFORT | Fonctionnalités non-critiques | Logout, préférences |

### 1.2 Bibliothèque Core SH

Fichier : `/app/core/sh.py`

```python
# Fonctions obligatoires
sh_get_val(data, key, default)      # Lecture sécurisée niveau 1
sh_format(template, **kwargs)        # Formatage sécurisé (remplace f-strings)
sh_error(e, code_error, ...)        # Log structuré complet
sh_bounded_loop(iterable, max, ...)  # Boucle bornée (Règle 1)
sh_get_config(key, default, cast)   # Configuration avec fallback
sh_generate_correlation_id(...)     # ID de corrélation unique
sh_sensitive(value)                 # Masquage RGPD
sh_load_json(path, default)         # Chargement JSON sécurisé
```

---

## 2. Règles Appliquées

### Règle 0 : Observer et Comprendre

**Principe** : Tout comportement anormal doit être tracé pour diagnostic.

```python
sh_error(
    None,
    code_error="LOGIN_USER_NOT_FOUND",
    type_p="WARNING",
    criticality="C1",
    correlation_id=correlation_id,
    context={"username": sh_sensitive(login_data.username)}
)
```

### Règle 1 : Tout Doit Être Borné par le Réel

**Principe** : Aucune boucle infinie, aucune requête sans limite.

```python
# Configuration des limites
max_services = sh_get_config("SH_MAX_SERVICES", 100, int)

# Boucle bornée
for service in sh_bounded_loop(services, max_services, "warn"):
    # Traitement...
```

**Limites configurées** (`config.py`) :
- `SH_DEFAULT_MAX_ITEMS` : 10000
- `SH_MAX_SERVICES` : 100
- `SH_MAX_ETABLISSEMENTS` : 200
- `SH_MAX_PRESENCES_BATCH` : 500

### Règle 3 : Machine à États Explicite

**Principe** : Les transitions d'état doivent être contrôlées et tracées.

```python
# Définition des transitions valides
TRANSITIONS_VALIDES = {
    StatutStageEnum.BROUILLON: [VALIDE, REFUSE, ANNULE],
    StatutStageEnum.VALIDE: [CONVENTIONNE, BROUILLON, ANNULE],
    StatutStageEnum.EN_COURS: [TERMINE, ANNULE],
    StatutStageEnum.TERMINE: [],  # État final
    # ...
}

# Validation avec sh_get_val
def check_transition(current, new):
    allowed = sh_get_val(TRANSITIONS_VALIDES, current, [])
    return new in allowed

# Log de la transition
sh_error(
    None,
    code_error="STAGE_STATE_TRANSITION",
    type_p="INFO",
    action="state_transition",
    context={
        "stage_id": stage_id,
        "from_status": old_status.value,
        "to_status": new_status.value
    }
)
```

### Règle 7 : Traçabilité Complète

**Principe** : Chaque action doit être traçable via un ID de corrélation.

```python
# Format: DOMAINE-CRITICITE-AAAAMMJJ-HHMMSS-random4
correlation_id = sh_generate_correlation_id("AUTH", "C1")
# Exemple: AUTH-C1-20260128-143052-A7F2

# Toutes les erreurs incluent le correlation_id
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail={
        "message": "Token invalide",
        "correlation_id": correlation_id
    }
)
```

---

## 3. Patterns d'Exception

### Pattern Obligatoire

```python
try:
    # Code métier...

except HTTPException:
    # Re-raise les exceptions HTTP (déjà gérées)
    raise

except Exception as e:
    # TOUJOURS en dernier - filet de sécurité
    sh_error(
        e,
        code_error="FONCTION_1",  # Code unique
        type_p="ERROR",
        criticality="C2",
        correlation_id=correlation_id,
        user_id=current_user.id
    )
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "message": "Erreur lors de l'opération",
            "correlation_id": correlation_id
        }
    )
```

### Codes d'Erreur

Format : `FONCTION_DESCRIPTION` ou `FONCTION_N` pour les erreurs génériques.

Exemples :
- `LOGIN_USER_NOT_FOUND` - Utilisateur non trouvé lors du login
- `CREATE_STAGE_INVALID_DATES` - Dates invalides à la création
- `UPDATE_STAGE_1` - Erreur générique sur mise à jour stage

---

## 4. Conformité RGPD

### Masquage des Données Sensibles

```python
from app.core.sh import sh_sensitive

# Dans les logs
context={
    "username": sh_sensitive(login_data.username),  # -> [[username]]
    "nom": sh_sensitive(etudiant.nom),              # -> [[nom]]
    "email": sh_sensitive(etudiant.email)           # -> [[email]]
}
```

### Données Concernées
- Noms et prénoms
- Emails
- Numéros de téléphone
- Adresses
- Identifiants utilisateur

---

## 5. Interdictions

| Interdit | Alternative SH |
|----------|---------------|
| `data["key"]` | `sh_get_val(data, "key", default)` |
| `data.get("key")` | `sh_get_val(data, "key", default)` |
| `f"string {var}"` | `sh_format("string {var}", var=var)` |
| `json.loads()` | `sh_load_json()` |
| `print()` | `sh_error()` |
| `for x in list:` sans limite | `sh_bounded_loop(list, max)` |
| Valeurs en dur | `sh_get_config()` |

---

## 6. Fichiers Modifiés

### Backend API (9 fichiers)

| Fichier | Criticité | État |
|---------|-----------|------|
| `app/api/deps.py` | C1 | ✅ Conforme |
| `app/api/auth.py` | C1 | ✅ Conforme |
| `app/api/stages.py` | C2 | ✅ Conforme |
| `app/api/documents.py` | C2 | ✅ Conforme |
| `app/api/etudiants.py` | C2 | ✅ Conforme |
| `app/api/rapports.py` | C3 | ✅ Conforme |
| `app/api/presences.py` | C3 | ✅ Conforme |
| `app/api/services.py` | C3 | ✅ Conforme |
| `app/api/etablissements.py` | C3 | ✅ Conforme |

### Core (2 fichiers)

| Fichier | Description |
|---------|-------------|
| `app/core/sh.py` | Bibliothèque SH (créé) |
| `app/core/config.py` | Configuration SH ajoutée |

---

## 7. Checklist de Conformité

Avant chaque commit, vérifier :

- [ ] Pas de `data["key"]` → utiliser `sh_get_val()`
- [ ] Pas de f-strings → utiliser `sh_format()`
- [ ] Pas de boucle sans limite → utiliser `sh_bounded_loop()`
- [ ] `correlation_id` présent dans toutes les erreurs
- [ ] `except Exception` toujours en dernier
- [ ] Données sensibles masquées avec `sh_sensitive()`
- [ ] Criticité documentée dans la docstring
- [ ] Codes d'erreur uniques

---

## 8. Références

- Document source : `regles_codages.pdf` (18 pages)
- Inspiré des normes DO-178C (aéronautique) et IEC 62304 (médical)
- Adapté pour les SI hospitaliers français
