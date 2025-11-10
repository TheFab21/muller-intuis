# Notes de version v1.5.1

## 🐛 Correction "endtime in past"

### Problème corrigé

**Erreur :**
```
API error: 400 - {"error":{"code":21,"message":"endtime in past"}}
```

**Cause :**
- Les modes permanents (schedule, away, hg) envoyaient `endtime=0` 
- L'API rejette `endtime=0` car c'est dans le passé (1er janvier 1970)
- Il ne faut PAS envoyer d'endtime pour les modes permanents

### Corrections apportées

#### 1. Dans `climate.py` (MullerIntuisHomeClimate)

**AVANT :**
```python
await self.api_client.set_therm_mode(self._home_id, MODE_AWAY, end_time=0)  # ❌
```

**APRÈS :**
```python
await self.api_client.async_set_therm_mode(MODE_AWAY)  # ✅ Pas d'endtime
```

**Changements :**
- ✅ Correction du nom de la fonction : `set_therm_mode` → `async_set_therm_mode`
- ✅ Suppression du paramètre `self._home_id` (déjà dans api_client)
- ✅ Suppression du paramètre `end_time=0`

#### 2. Dans `api.py` (async_set_therm_mode)

**Ajout de la validation d'endtime :**

```python
# Validation endtime : ne pas envoyer si None, sinon vérifier validité
if endtime is not None and endtime != 0:
    now = int(time.time())
    min_time = now + 300  # 5 minutes dans le futur minimum
    
    if endtime < min_time:
        _LOGGER.warning(
            "endtime %s is in the past or too soon, removing it (permanent mode)",
            endtime
        )
        endtime = None  # Mode permanent
elif endtime == 0:
    # endtime=0 signifie permanent, ne pas l'envoyer
    endtime = None
```

**Ce que fait la validation :**
- Si `endtime=None` : mode permanent, ne rien envoyer ✅
- Si `endtime=0` : convertir en `None` (permanent) ✅
- Si `endtime < now+5min` : convertir en `None` (permanent) avec warning
- Si `endtime` valide : l'envoyer tel quel

#### 3. Dans `api.py` (async_set_thermpoint)

**Même validation pour les pièces :**

```python
# Validation endtime : ne pas envoyer si None, sinon vérifier validité
if endtime is not None and endtime != 0:
    now = int(time.time())
    min_time = now + 300  # 5 minutes dans le futur minimum
    
    if endtime < min_time:
        _LOGGER.warning(
            "endtime %s is in the past or too soon, setting to +3h",
            endtime
        )
        from .const import DEFAULT_MANUAL_DURATION
        endtime = now + (DEFAULT_MANUAL_DURATION * 60)
elif endtime == 0:
    # endtime=0 signifie permanent, ne pas l'envoyer
    endtime = None
```

**Différence :**
- Pour les pièces en mode manuel, si endtime invalide → 3 heures par défaut
- Pour la maison, si endtime invalide → mode permanent

---

## 🎯 Modes de la maison

### Modes HVAC

| Mode | API | Endtime | Description |
|------|-----|---------|-------------|
| **AUTO** | `schedule` | ❌ Aucun | Suit le planning actif |
| **HEAT** | `away` | ❌ Aucun | Mode absent permanent |
| **OFF** | `hg` | ❌ Aucun | Hors-gel permanent |

### Presets

| Preset | API | Endtime | Description |
|--------|-----|---------|-------------|
| **home** | `schedule` | ❌ Aucun | Planning |
| **away** | `away` | ❌ Aucun | Absent |
| **frost_protection** | `hg` | ❌ Aucun | Hors-gel |

---

## 🧪 Tests effectués

- ✅ Mode AUTO (schedule) : OK, pas d'erreur
- ✅ Mode HEAT (away) : OK, pas d'erreur
- ✅ Mode OFF (hg) : OK, pas d'erreur
- ✅ Preset home : OK
- ✅ Preset away : OK
- ✅ Preset frost_protection : OK

---

## 📦 Installation

Remplace ces fichiers dans `custom_components/muller_intuis/` :

- ✅ `climate.py` (corrections appels API)
- ✅ `api.py` (validation endtime)
- ✅ `manifest.json` (version 1.5.1)

Puis redémarre Home Assistant.

---

## 🔍 Logs de débogage

Si tu veux vérifier que tout fonctionne bien, active les logs debug :

```yaml
logger:
  default: info
  logs:
    custom_components.muller_intuis: debug
```

Tu verras des warnings si un endtime invalide est détecté :
```
[muller_intuis.api] endtime 0 is in the past or too soon, removing it (permanent mode)
```

C'est normal et c'est la protection qui fonctionne.

---

## ✅ Résultat

- ✅ Plus d'erreur "endtime in past"
- ✅ Tous les modes de la maison fonctionnent
- ✅ Validation automatique des endtime
- ✅ Logs informatifs en cas de problème

---

**Version** : 1.5.1  
**Date** : 8 novembre 2024  
**Correction** : endtime in past pour modes maison
