"""
Bibliothèque SH - Fonctions mission-critiques
Version 1.0 - Janvier 2026

Règles de codage pour systèmes hospitaliers.
Le code métier n'accède JAMAIS directement aux fonctions natives ou libs externes.
"""

import json
import logging
import random
import string
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Union
from functools import wraps

# Configuration du logger structuré
logger = logging.getLogger("sh")

T = TypeVar('T')

# =============================================================================
# CONFIGURATION GLOBALE
# =============================================================================

_config: Dict[str, Any] = {}

def sh_init_config(config: Dict[str, Any]) -> None:
    """Initialise la configuration SH."""
    global _config
    _config = config


def sh_get_config(key: str, default: T, expected_type: type = None) -> T:
    """
    Lecture d'une valeur de configuration.
    Règle: Tout ce qui varie selon établissement/contexte → config, pas en dur.

    Args:
        key: Clé de configuration
        default: Valeur par défaut (OBLIGATOIRE)
        expected_type: Type attendu pour validation

    Returns:
        Valeur de configuration ou default
    """
    value = _config.get(key, default)

    if expected_type is not None and value is not None:
        if not isinstance(value, expected_type):
            sh_error(
                None,
                code_error="SH_CONFIG_TYPE_MISMATCH",
                type_p="WARNING",
                criticality="C4",
                context={"key": key, "expected": str(expected_type), "got": str(type(value))}
            )
            return default

    return value


# =============================================================================
# CORRELATION ID
# =============================================================================

def sh_generate_correlation_id(domaine: str = "GIS", criticality: str = "C3") -> str:
    """
    Génère un correlation_id unique.
    Format: DOMAINE-CRITICITE-AAAAMMJJ-HHMMSS-random4

    Args:
        domaine: Domaine applicatif (ex: GIS, RX, ADM)
        criticality: Niveau de criticité (C1-C4)

    Returns:
        Correlation ID unique
    """
    now = datetime.now()
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{domaine}-{criticality}-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}-{random_part}"


# =============================================================================
# ACCÈS AUX DONNÉES - LECTURE
# =============================================================================

def sh_get_val(data: Any, key: str, default: T) -> T:
    """
    Lecture sécurisée niveau 1.
    INTERDIT: data["key"]
    OBLIGATOIRE: sh_get_val(data, "key", default)

    Args:
        data: Dictionnaire source
        key: Clé à lire
        default: Valeur par défaut (OBLIGATOIRE - force le dev à réfléchir)

    Returns:
        Valeur ou default (toujours le même type que default)
    """
    if data is None:
        return default

    if not isinstance(data, dict):
        return default

    value = data.get(key)

    if value is None:
        return default

    # Vérification du type si default n'est pas None
    if default is not None and not isinstance(value, type(default)):
        return default

    return value


def sh_get_val_x(default: T, data: Any, *keys: str) -> T:
    """
    Lecture sécurisée niveau N (imbriqué).
    INTERDIT: data["a"]["b"]["c"]
    OBLIGATOIRE: sh_get_val_x(default, data, "a", "b", "c")

    Args:
        default: Valeur par défaut (OBLIGATOIRE)
        data: Dictionnaire source
        *keys: Clés successives

    Returns:
        Valeur ou default
    """
    current = data

    for key in keys:
        if current is None or not isinstance(current, dict):
            return default
        current = current.get(key)

    if current is None:
        return default

    if default is not None and not isinstance(current, type(default)):
        return default

    return current


def sh_get_str(data: Any, key: str, default: str = "") -> str:
    """Lecture sécurisée d'une string."""
    value = sh_get_val(data, key, default)
    if isinstance(value, str):
        return value
    return str(value) if value is not None else default


def sh_get_int(data: Any, key: str, default: int = 0) -> int:
    """Lecture sécurisée d'un int."""
    value = sh_get_val(data, key, None)
    if value is None:
        return default
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def sh_get_float(data: Any, key: str, default: float = 0.0) -> float:
    """Lecture sécurisée d'un float."""
    value = sh_get_val(data, key, None)
    if value is None:
        return default
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def sh_get_bool(data: Any, key: str, default: bool = False) -> bool:
    """Lecture sécurisée d'un bool."""
    value = sh_get_val(data, key, None)
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'oui')
    return bool(value)


def sh_get_list(data: Any, key: str, default: List = None) -> List:
    """Lecture sécurisée d'une list."""
    if default is None:
        default = []
    value = sh_get_val(data, key, None)
    if value is None:
        return default
    if isinstance(value, list):
        return value
    return default


def sh_get_dict(data: Any, key: str, default: Dict = None) -> Dict:
    """Lecture sécurisée d'un dict."""
    if default is None:
        default = {}
    value = sh_get_val(data, key, None)
    if value is None:
        return default
    if isinstance(value, dict):
        return value
    return default


# =============================================================================
# ACCÈS AUX DONNÉES - ÉCRITURE
# =============================================================================

def sh_set_val(data: Dict, key: str, value: Any, default_type: type = str) -> Dict:
    """
    Écriture sécurisée niveau 1.
    INTERDIT: data["key"] = value
    OBLIGATOIRE: data = sh_set_val(data, "key", value, default_type)

    Args:
        data: Dictionnaire cible
        key: Clé à écrire
        value: Valeur à écrire
        default_type: Type par défaut si value est None

    Returns:
        Dictionnaire modifié
    """
    if data is None:
        data = {}

    if value is None:
        # Remplace None par la valeur par défaut du type
        defaults = {str: "", int: 0, float: 0.0, bool: False, list: [], dict: {}}
        value = defaults.get(default_type, None)

    data[key] = value
    return data


def sh_set_val_x(default_type: type, data: Dict, value: Any, *keys: str) -> Dict:
    """
    Écriture sécurisée niveau N (imbriqué).

    Args:
        default_type: Type par défaut si value est None
        data: Dictionnaire cible
        value: Valeur à écrire
        *keys: Clés successives

    Returns:
        Dictionnaire modifié
    """
    if data is None:
        data = {}

    if not keys:
        return data

    current = data
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]

    if value is None:
        defaults = {str: "", int: 0, float: 0.0, bool: False, list: [], dict: {}}
        value = defaults.get(default_type, None)

    current[keys[-1]] = value
    return data


# =============================================================================
# STRINGS
# =============================================================================

def sh_to_str(data: Any, source_type: str = "auto", default: str = "") -> str:
    """
    Conversion sécurisée vers string UTF-8.
    Règle absolue: UTF-8 en interne. Toujours. Partout.
    """
    if data is None:
        return default

    try:
        if isinstance(data, bytes):
            return data.decode('utf-8', errors='replace')
        return str(data)
    except Exception:
        return default


def sh_format(template: str, **kwargs) -> str:
    """
    Formatage sécurisé de string.
    INTERDIT: f"Hello {name}"
    OBLIGATOIRE: sh_format("Hello {name}", name=name)
    """
    try:
        return template.format(**kwargs)
    except (KeyError, ValueError, IndexError) as e:
        sh_error(
            e,
            code_error="SH_FORMAT_ERROR",
            type_p="WARNING",
            criticality="C4",
            context={"template": template[:100]}
        )
        return template


def sh_concat(*args, separator: str = "") -> str:
    """
    Concaténation sécurisée de strings.
    INTERDIT: str1 + str2
    OBLIGATOIRE: sh_concat(str1, str2)
    """
    result = []
    for arg in args:
        if arg is not None:
            result.append(sh_to_str(arg))
    return separator.join(result)


# =============================================================================
# JSON
# =============================================================================

def sh_load_json(text: str, default: Union[Dict, List] = None) -> Union[Dict, List]:
    """
    Parse JSON sécurisé.
    INTERDIT: json.loads(text)
    OBLIGATOIRE: sh_load_json(text, {})
    """
    if default is None:
        default = {}

    if text is None or text == "":
        return default

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        sh_error(
            e,
            code_error="SH_JSON_PARSE_ERROR",
            type_p="WARNING",
            criticality="C4",
            context={"text_preview": text[:100] if len(text) > 100 else text}
        )
        return default


def sh_save_json(obj: Any, default: str = "{}") -> str:
    """
    Sérialisation JSON sécurisée.
    INTERDIT: json.dumps(obj)
    OBLIGATOIRE: sh_save_json(obj, "{}")
    """
    if obj is None:
        return default

    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except (TypeError, ValueError) as e:
        sh_error(
            e,
            code_error="SH_JSON_SERIALIZE_ERROR",
            type_p="WARNING",
            criticality="C4"
        )
        return default


# =============================================================================
# DONNÉES SENSIBLES RGPD
# =============================================================================

def sh_sensitive(value: Any) -> str:
    """
    Marque une donnée comme sensible RGPD.
    Format: [[donnée sensible]]
    """
    if value is None:
        return "[[NULL]]"
    return f"[[{sh_to_str(value)}]]"


# =============================================================================
# ERREURS ET LOGS
# =============================================================================

def sh_error(
    e: Optional[Exception],
    code_error: str,
    type_p: str = "ERROR",
    criticality: str = "C3",
    correlation_id: str = None,
    context: Dict = None,
    user_id: int = None,
    action: str = None
) -> None:
    """
    Log structuré complet.

    Args:
        e: Exception (peut être None pour log info)
        code_error: Code erreur unique (FONCTION_DESCRIPTION)
        type_p: Type (ERROR, WARNING, DEBUG, INFO)
        criticality: Niveau (C1=vital, C2=important, C3=standard, C4=confort)
        correlation_id: ID de corrélation
        context: Contexte additionnel
        user_id: ID utilisateur si applicable
        action: Action en cours
    """
    if correlation_id is None:
        correlation_id = sh_generate_correlation_id(criticality=criticality)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "code_error": code_error,
        "type": type_p,
        "criticality": criticality,
        "correlation_id": correlation_id,
        "exception": str(e) if e else None,
        "exception_type": type(e).__name__ if e else None,
        "context": context or {},
        "user_id": user_id,
        "action": action
    }

    # Log selon le type
    log_message = sh_save_json(log_entry)

    if type_p == "ERROR":
        logger.error(log_message)
    elif type_p == "WARNING":
        logger.warning(log_message)
    elif type_p == "DEBUG":
        logger.debug(log_message)
    else:
        logger.info(log_message)


def sh_print(message: str) -> None:
    """
    Print encapsulé (CLI uniquement).
    INTERDIT: print(message)
    OBLIGATOIRE: sh_print(message)
    """
    print(sh_to_str(message))


# =============================================================================
# BORNES ET LIMITES (Règle 1)
# =============================================================================

def sh_bounded_loop(
    iterable: Any,
    max_items: int = None,
    on_limit_reached: str = "warn"
) -> Any:
    """
    Itération bornée sécurisée.
    Règle 1: Tout doit être borné par le réel.

    Args:
        iterable: Collection à itérer
        max_items: Limite maximale (défaut depuis config)
        on_limit_reached: Action si limite atteinte (warn, stop, error)

    Yields:
        Éléments de l'itérable jusqu'à la limite
    """
    if max_items is None:
        max_items = sh_get_config("SH_DEFAULT_MAX_ITEMS", 10000, int)

    count = 0
    for item in iterable:
        if count >= max_items:
            sh_error(
                None,
                code_error="SH_BOUNDED_LOOP_LIMIT",
                type_p="WARNING" if on_limit_reached == "warn" else "ERROR",
                criticality="C3",
                context={"max_items": max_items, "reached_at": count}
            )
            if on_limit_reached == "error":
                raise ValueError(f"Limite de {max_items} éléments atteinte")
            break
        yield item
        count += 1


# =============================================================================
# TRANSITIONS D'ÉTAT (Règle 3)
# =============================================================================

class ShStateMachine:
    """
    Machine à états avec transitions contrôlées.
    Règle 3: États explicites et transitions maîtrisées.
    """

    def __init__(
        self,
        name: str,
        states: List[str],
        transitions: Dict[str, List[str]],
        initial_state: str
    ):
        self.name = name
        self.states = set(states)
        self.transitions = transitions
        self.current_state = initial_state

        if initial_state not in self.states:
            raise ValueError(f"État initial '{initial_state}' non valide")

    def can_transition(self, to_state: str) -> bool:
        """Vérifie si une transition est autorisée."""
        allowed = self.transitions.get(self.current_state, [])
        return to_state in allowed

    def transition(
        self,
        to_state: str,
        correlation_id: str = None,
        user_id: int = None,
        context: Dict = None
    ) -> bool:
        """
        Effectue une transition d'état avec log.

        Returns:
            True si transition effectuée, False sinon
        """
        if to_state not in self.states:
            sh_error(
                None,
                code_error=f"{self.name.upper()}_INVALID_STATE",
                type_p="ERROR",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=user_id,
                context={"from": self.current_state, "to": to_state, **(context or {})}
            )
            return False

        if not self.can_transition(to_state):
            sh_error(
                None,
                code_error=f"{self.name.upper()}_FORBIDDEN_TRANSITION",
                type_p="ERROR",
                criticality="C2",
                correlation_id=correlation_id,
                user_id=user_id,
                context={"from": self.current_state, "to": to_state, **(context or {})}
            )
            return False

        # Log de la transition
        sh_error(
            None,
            code_error=f"{self.name.upper()}_STATE_CHANGE",
            type_p="INFO",
            criticality="C3",
            correlation_id=correlation_id,
            user_id=user_id,
            context={"from": self.current_state, "to": to_state, **(context or {})}
        )

        self.current_state = to_state
        return True


# =============================================================================
# DÉCORATEURS UTILITAIRES
# =============================================================================

def sh_with_error_handling(code_prefix: str, criticality: str = "C3"):
    """
    Décorateur pour gestion d'erreur standardisée.

    Usage:
        @sh_with_error_handling("GET_USER", "C2")
        def get_user(user_id: int):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            correlation_id = sh_generate_correlation_id(criticality=criticality)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                sh_error(
                    e,
                    code_error=f"{code_prefix}_1",
                    type_p="ERROR",
                    criticality=criticality,
                    correlation_id=correlation_id,
                    context={"function": func.__name__}
                )
                raise
        return wrapper
    return decorator


# =============================================================================
# MACHINE À ÉTATS POUR STAGES
# =============================================================================

# Définition des transitions autorisées pour les stages
STAGE_STATE_MACHINE = ShStateMachine(
    name="STAGE",
    states=["brouillon", "valide", "conventionne", "en_cours", "termine", "annule", "refuse"],
    transitions={
        "brouillon": ["valide", "refuse", "annule"],
        "valide": ["conventionne", "refuse", "annule"],
        "conventionne": ["en_cours", "annule"],
        "en_cours": ["termine", "annule"],
        "termine": [],  # État final
        "annule": [],   # État final
        "refuse": [],   # État final
    },
    initial_state="brouillon"
)


def sh_validate_stage_transition(
    current_status: str,
    new_status: str,
    correlation_id: str = None,
    user_id: int = None
) -> bool:
    """
    Valide une transition d'état pour un stage.

    Returns:
        True si la transition est autorisée
    """
    sm = ShStateMachine(
        name="STAGE",
        states=STAGE_STATE_MACHINE.states,
        transitions=STAGE_STATE_MACHINE.transitions,
        initial_state=current_status
    )
    return sm.can_transition(new_status)
