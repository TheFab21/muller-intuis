# Corrections apportées à l'intégration Muller Intuis Connect

## Version corrigée : 1.1.0

Cette version corrige deux problèmes majeurs identifiés dans l'intégration originale.

---

## 🐛 Problèmes corrigés

### 1. **Erreur "endtime in past" (Code 21)**

**Symptôme :** 
```
API error: 400 - {"error":{"code":21,"message":"endtime in past"}}
```

**Cause :**
L'API Muller Intuitiv/Netatmo rejette les requêtes avec un `endtime` (timestamp de fin) qui est dans le passé ou trop proche du présent.

**Solution implémentée :**
- Ajout d'une fonction `_validate_endtime()` dans `__init__.py` qui :
  - Vérifie que l'endtime est au moins 5 minutes dans le futur
  - Vérifie que l'endtime n'est pas plus d'un an dans le futur
  - Si invalide, utilise une valeur par défaut de 3 heures
  - Ne définit pas d'endtime pour les modes qui n'en ont pas besoin (schedule, hg, off)

```python
def _validate_endtime(self, endtime: int | None, mode: str) -> int | None:
    """Valide et corrige l'endtime selon les règles de l'API."""
    if endtime is None:
        if mode in ["hg", "schedule", "off"]:
            return None
        elif mode in ["away", "manual"]:
            return int((datetime.now() + timedelta(hours=3)).timestamp())
        return None
    
    now = int(datetime.now().timestamp())
    min_time = now + 5 * 60  # Au moins 5 minutes dans le futur
    max_time = now + 365 * 24 * 60 * 60  # Maximum 1 an
    
    if endtime < min_time or endtime > max_time:
        return int((datetime.now() + timedelta(hours=3)).timestamp())
    
    return endtime
```

---

### 2. **Absence du vrai mode OFF**

**Symptôme :**
Le mode `OFF` dans Home Assistant correspondait au mode "hors-gel" (`hg`), ce qui ne coupe pas complètement les radiateurs.

**Solution implémentée :**

#### A. Distinction claire des modes dans `climate.py` :

**Modes HVAC (visibles dans Home Assistant) :**
- `AUTO` → Mode planning (`schedule`)
- `HEAT` → Mode manuel (`manual`) avec température réglable
- `OFF` → **VRAI arrêt complet** (`off`)

**Presets (modes supplémentaires) :**
- `schedule` → Suit le planning actif
- `manual` → Température manuelle
- `away` → Mode absent
- `frost_protection` → Hors-gel (ancien "OFF")

#### B. Mapping des modes :

```python
HVAC_MODE_TO_API = {
    HVACMode.AUTO: "schedule",      # Mode planning
    HVACMode.HEAT: "manual",        # Mode manuel
    HVACMode.OFF: "off",            # VRAI arrêt (nouveau)
}

PRESET_TO_API = {
    PRESET_SCHEDULE: "schedule",
    PRESET_MANUAL: "manual",
    PRESET_AWAY: "away",
    PRESET_FROST_PROTECTION: "hg",  # Hors-gel
}
```

#### C. Comportement du mode OFF :

Quand vous définissez le mode sur `OFF` dans Home Assistant :
```python
async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
    if hvac_mode == HVACMode.OFF:
        _LOGGER.info("Setting real OFF mode (not frost protection)")
        await self.coordinator.async_set_home_mode("off", endtime=None)
```

---

## 📋 Modes disponibles

### Modes HVAC (bouton principal)

| Mode HA | API Mode | Description | Endtime requis |
|---------|----------|-------------|----------------|
| `AUTO` | `schedule` | Suit le planning actif | Non |
| `HEAT` | `manual` | Température manuelle | Oui (3h par défaut) |
| `OFF` | `off` | **Arrêt complet** | Non |

### Presets (modes avancés)

| Preset | API Mode | Description | Endtime requis |
|--------|----------|-------------|----------------|
| `schedule` | `schedule` | Suit le planning | Non |
| `manual` | `manual` | Température manuelle | Oui (3h par défaut) |
| `away` | `away` | Mode absent | Oui (3h par défaut) |
| `frost_protection` | `hg` | Hors-gel (~7°C) | Non |

---

## 🔧 Utilisation

### Via l'interface Home Assistant

1. **Arrêt complet** : Sélectionner le mode `OFF`
2. **Hors-gel** : Sélectionner le preset `frost_protection`
3. **Planning** : Sélectionner le mode `AUTO`
4. **Température manuelle** : Sélectionner `HEAT` et ajuster la température

### Via automatisations YAML

**Arrêt complet :**
```yaml
service: climate.set_hvac_mode
target:
  entity_id: climate.muller_salon
data:
  hvac_mode: "off"
```

**Hors-gel :**
```yaml
service: climate.set_preset_mode
target:
  entity_id: climate.muller_salon
data:
  preset_mode: "frost_protection"
```

**Mode absent :**
```yaml
service: climate.set_preset_mode
target:
  entity_id: climate.muller_salon
data:
  preset_mode: "away"
```

---

## 🚀 Installation

### Via HACS (recommandé)

1. Dans HACS → Intégrations → Menu (⋮) → Dépôts personnalisés
2. Ajouter : `https://github.com/TheFab21/muller-intuis`
3. Catégorie : `Integration`
4. Installer et redémarrer Home Assistant

### Manuel

1. Copier le dossier `muller_intuis_fixed` vers `custom_components/muller_intuis`
2. Redémarrer Home Assistant
3. Ajouter l'intégration via l'interface

---

## 🔄 Compatibilité avec Node-RED

L'intégration corrigée est maintenant **100% compatible** avec votre flow Node-RED existant. 

### Correspondance des modes :

| Node-RED | Home Assistant HVAC | Home Assistant Preset |
|----------|---------------------|----------------------|
| `schedule` | `AUTO` | `schedule` |
| `manual` | `HEAT` | `manual` |
| `away` | - | `away` |
| `hg` | - | `frost_protection` |
| `off` | `OFF` | - |

Vous pouvez donc :
- Continuer à utiliser Node-RED pour contrôler vos radiateurs
- Utiliser Home Assistant en parallèle
- Les deux systèmes se synchroniseront via l'API

---

## 📝 Changelog

### Version 1.1.0 (Novembre 2024)

**Nouvelles fonctionnalités :**
- ✅ Ajout du vrai mode OFF (arrêt complet des radiateurs)
- ✅ Le mode "hors-gel" est maintenant un preset distinct

**Corrections :**
- 🐛 Correction de l'erreur "endtime in past" 
- 🐛 Validation automatique des timestamps
- 🐛 Gestion des endtime invalides avec fallback de 3 heures

**Améliorations :**
- 📝 Logs plus détaillés pour le débogage
- 🔒 Validation stricte des endtime (min 5 min, max 1 an)
- ⚡ Pas d'endtime envoyé pour les modes qui n'en ont pas besoin

---

## 🧪 Tests effectués

- ✅ Changement de mode AUTO → OFF : OK
- ✅ Changement de mode OFF → HEAT : OK
- ✅ Preset frost_protection : OK
- ✅ Preset away : OK
- ✅ Validation endtime dans le passé : OK (fallback 3h)
- ✅ Mode schedule sans endtime : OK
- ✅ Compatibilité Node-RED : OK

---

## 📞 Support

- **Issues** : https://github.com/TheFab21/muller-intuis/issues
- **Documentation** : https://github.com/TheFab21/muller-intuis

---

## 👏 Crédits

Basé sur l'API Netatmo Energy et inspiré par la communauté Home Assistant.

Corrections apportées suite à l'analyse du flow Node-RED fonctionnel.
