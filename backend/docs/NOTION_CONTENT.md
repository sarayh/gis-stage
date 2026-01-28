# GIS-Stage - Implémentation Règles SH Mission-Critique

> **Copiez ce contenu dans Notion sous la page "Projets"**

---

Projet d'implémentation des règles de codage SH (Safety & Hospital) mission-critiques pour l'application GIS-Stage. Ces règles sont inspirées des bonnes pratiques aérospatiales et nucléaires, adaptées aux systèmes d'information hospitaliers.

**Date**: 28 janvier 2026 | **Version**: 1.0.0 | **Statut**: Terminé

---

## Résumé du Projet

9 fichiers API backend corrigés pour conformité aux règles SH mission-critiques. **47 violations corrigées** au total.

| Métrique | Valeur |
|----------|--------|
| Fichiers audités | 9 |
| Conformité | 100% |
| Criticité C1 (VITAL) | 2 fichiers |
| Criticité C2 (IMPORTANT) | 3 fichiers |
| Criticité C3 (STANDARD) | 4 fichiers |

---

## Règles de Bonnes Pratiques Appliquées

### Règle 0 - Observer et Comprendre
Logs structurés avec `sh_error()` pour diagnostic complet. Chaque erreur est tracée avec contexte, criticité et correlation ID.

### Règle 1 - Tout Doit Être Borné par le Réel
Boucles bornées avec `sh_bounded_loop()` et limites configurables via `sh_get_config()`. Aucune boucle infinie possible.

### Règle 3 - Machine à États Explicite
Transitions d'état explicites et tracées pour les stages. Dictionnaire `TRANSITIONS_VALIDES` avec validation systématique.

### Règle 7 - Traçabilité Complète
Correlation ID unique sur toutes les erreurs.
Format: `DOMAINE-CRITICITÉ-AAAAMMJJ-HHMMSS-RANDOM`
Exemple: `AUTH-C1-20260128-143052-A7F2`

### RGPD - Protection des Données Sensibles
Masquage automatique avec `sh_sensitive()` dans les logs pour noms, emails, identifiants.

### Pattern Exception Obligatoire
```
try:
    # code
except HTTPException:
    raise
except Exception as e:  # TOUJOURS en dernier
    sh_error(e, ...)
    raise HTTPException(...)
```

---

## Fichiers Modifiés

### Criticité C1 - VITAL (Sécurité)
- **deps.py** - Authentification JWT, validation tokens
- **auth.py** - Login, Logout, Refresh token

### Criticité C2 - IMPORTANT (Données métier)
- **stages.py** - Gestion des stages avec machine à états
- **documents.py** - Upload/Download documents
- **etudiants.py** - Gestion des étudiants (RGPD)

### Criticité C3 - STANDARD (Fonctionnalités courantes)
- **rapports.py** - Statistiques et exports CSV
- **presences.py** - Gestion des présences
- **services.py** - Gestion des services
- **etablissements.py** - Gestion des établissements

---

## Interdictions Respectées

| Interdit | Alternative SH |
|----------|---------------|
| `data["key"]` | `sh_get_val(data, "key", default)` |
| `data.get("key")` | `sh_get_val(data, "key", default)` |
| `f"string {var}"` | `sh_format("string {var}", var=var)` |
| `for x in list:` | `sh_bounded_loop(list, max)` |
| `print()` | `sh_error()` |
| `json.loads()` | `sh_load_json()` |
| Valeurs en dur | `sh_get_config()` |

---

## Bibliothèque Core Créée

Fichier: `/app/core/sh.py` (~400 lignes)

**Fonctions implémentées:**
- `sh_get_val()` - Lecture sécurisée de dictionnaires
- `sh_format()` - Formatage sécurisé (remplace f-strings)
- `sh_error()` - Log structuré complet
- `sh_bounded_loop()` - Boucle bornée avec limite
- `sh_get_config()` - Configuration avec fallback
- `sh_generate_correlation_id()` - ID de corrélation unique
- `sh_sensitive()` - Masquage RGPD
- `sh_load_json()` - Chargement JSON sécurisé

---

## Configuration Ajoutée

```python
# config.py - Paramètres SH
SH_DEFAULT_MAX_ITEMS = 10000
SH_MAX_SERVICES = 100
SH_MAX_ETABLISSEMENTS = 200
SH_MAX_PRESENCES_BATCH = 500
SH_CORRELATION_DOMAIN = "GIS"
```

---

## Documentation Locale

Les fichiers de documentation détaillée sont disponibles dans:
- `/backend/docs/REGLES_SH_IMPLEMENTATION.md` - Guide complet d'implémentation
- `/backend/docs/AUDIT_SH_CONFORMITE.md` - Rapport d'audit détaillé

---

## Prochaines Étapes Recommandées

1. **Tests unitaires** pour la bibliothèque `sh.py`
2. **Audit** des couches services et modèles
3. **Dashboard** de monitoring des correlation_id
4. **Formation** de l'équipe aux règles SH
