# Notes de version v1.5.1

## 🐛 Corrections

### Correction du KeyError 'name'

**Problème identifié :**
```
KeyError: 'name'
File "/config/custom_components/muller_intuis/climate.py", line 98
```

**Cause :**
L'API Muller/Netatmo retourne des structures de données variables selon les installations. Le champ `'name'` n'est pas toujours présent directement dans l'objet room.

**Solutions possibles selon l'API :**
- `room['name']` - Nom standard
- `room['module_name']` - Nom du module
- `room['id']` - ID comme fallback

**Correction appliquée :**

```python
# AVANT (v1.5.0)
self._attr_name = f"Muller {room['name']}"  # ❌ KeyError si 'name' absent

# APRÈS (v1.5.1)
room_name = room.get("name") or room.get("module_name") or room.get("id")
self._attr_name = f"Muller {room_name}"  # ✅ Toujours un nom
```

**Fichiers modifiés :**
- ✅ `climate.py` - Ligne 98 et device_info
- ✅ `sensor.py` - Tous les capteurs
- ✅ `manifest.json` - Version mise à jour

**Logging ajouté :**
```python
_LOGGER.debug("Room data: %s", room)
```
Pour aider à identifier la structure exacte retournée par l'API.

---

## 📊 Structures API possibles

### Structure type 1 (avec 'name')
```json
{
  "id": "1234567890",
  "name": "Salon",
  "therm_measured_temperature": 19.5,
  "therm_setpoint_temperature": 20.0
}
```

### Structure type 2 (avec 'module_name')
```json
{
  "id": "1234567890",
  "module_name": "Radiateur Salon",
  "therm_measured_temperature": 19.5,
  "therm_setpoint_temperature": 20.0
}
```

### Structure type 3 (sans nom)
```json
{
  "id": "1234567890",
  "therm_measured_temperature": 19.5,
  "therm_setpoint_temperature": 20.0
}
```

L'intégration gère maintenant les 3 cas automatiquement.

---

## 🔍 Débogage

Si tu veux voir la structure exacte retournée par ton API, active les logs debug :

**Dans `configuration.yaml` :**
```yaml
logger:
  default: info
  logs:
    custom_components.muller_intuis: debug
```

**Redémarre HA et consulte :**
```
Paramètres → Système → Journaux
```

Cherche les lignes contenant `"Room data:"` pour voir la structure complète.

---

## ✅ Test de la correction

Après avoir mis à jour vers v1.5.1 :

1. Redémarre Home Assistant
2. L'intégration devrait charger sans erreur
3. Les entités devraient apparaître avec des noms

Si tu vois encore des erreurs, partage-moi le contenu du log `"Room data:"` pour que je puisse affiner.

---

## 📦 Installation

Remplace les fichiers suivants dans `custom_components/muller_intuis/` :
- `climate.py`
- `sensor.py`
- `manifest.json`

Puis redémarre Home Assistant.

---

## 🔄 Changelog complet depuis v1.1.0

### v1.5.1 (Novembre 2024)
- 🐛 **FIX** : KeyError 'name' résolu
- 🐛 **FIX** : Support de structures API variables
- 📝 **AMÉLIORATION** : Logging ajouté pour débogage
- 📝 **AMÉLIORATION** : Fallback sur module_name ou id

### v1.5.0 (existant)
- Version actuelle dans ton installation

### v1.1.0 (corrections initiales)
- ✅ Correction "endtime in past"
- ✅ Ajout mode OFF véritable
- ✅ Validation automatique timestamps

---

## 💬 Besoin d'aide ?

Si le problème persiste après cette mise à jour, partage-moi :
1. Les logs avec `custom_components.muller_intuis: debug`
2. La ligne contenant `"Room data:"`
3. Le message d'erreur complet

Je pourrai alors affiner la correction pour ta configuration spécifique.
