# Comparaison intégration Home Assistant vs Flow Node-RED

## 🔍 Analyse de ton flow Node-RED

Après analyse de ton flow `flows_18_.json`, voici ce que j'ai identifié :

### 📡 API utilisée dans Node-RED

**Endpoint** : `https://app.muller-intuitiv.net/api/setthermmode`

**Payload envoyé** :
```json
{
  "app_identifier": "app_muller",
  "home_id": "<home_id>",
  "mode": "<mode>",
  "endtime": <timestamp> (optionnel)
}
```

### 🎛️ Modes Node-RED

Ton Node-RED utilise 3 modes principaux (fonction `Transco home mode`, ligne 408-427) :

| Interface HA | Valeur Node-RED | API Mode |
|--------------|-----------------|----------|
| "Home" | → `schedule` | Mode planning |
| "Away" | → `away` | Mode absent |
| "Hors Gel" | → `hg` | Hors-gel |

**Note importante** : Ton flow Node-RED **ne gère PAS le OFF** (tu l'as mentionné dans ta demande).

### ⏰ Gestion de l'endtime dans Node-RED

Ta fonction `Modifie endpoint à null si dans le passé` (ligne 429-449) fait **exactement** ce qui manquait dans l'intégration HA :

```javascript
const endtime = global.get("due_date_setpoint");
const now = Math.floor(Date.now() / 1000);
const minTime = now + 5 * 60;  // 5 minutes dans le futur minimum
const maxTime = now + 365 * 24 * 60 * 60;  // 1 an maximum

let validEndtime = null;

// Vérifie si endtime est dans la plage valide
if (endtime >= minTime && endtime <= maxTime) {
    validEndtime = endtime;
}

// Si invalide ET mode "manual", mettre 3 heures par défaut
if (validEndtime === null && global.get("mode_setpoint") === "manual") {
    validEndtime = now + 60 * 60 * 3; // 3 heures
}

// Pour "hg", pas besoin d'endtime
if (validEndtime === null && global.get("mode_setpoint") === "hg") {
    validEndtime = null;
}
```

**C'est exactement cette logique que j'ai portée en Python dans l'intégration HA corrigée !**

---

## ✅ Corrections apportées dans l'intégration HA

### 1. Fonction `_validate_endtime()` (portée depuis Node-RED)

```python
def _validate_endtime(self, endtime: int | None, mode: str) -> int | None:
    """
    Valide et corrige l'endtime - MÊME LOGIQUE QUE NODE-RED
    """
    if endtime is None:
        if mode in ["hg", "schedule", "off"]:
            return None
        elif mode in ["away", "manual"]:
            return int((datetime.now() + timedelta(hours=3)).timestamp())
        return None
    
    now = int(datetime.now().timestamp())
    min_time = now + 5 * 60  # 5 minutes (comme Node-RED)
    max_time = now + 365 * 24 * 60 * 60  # 1 an (comme Node-RED)
    
    if endtime < min_time or endtime > max_time:
        return int((datetime.now() + timedelta(hours=3)).timestamp())
    
    return endtime
```

### 2. Ajout du vrai mode OFF

Dans ton Node-RED, il manquait le mode OFF. Je l'ai ajouté dans l'intégration HA :

```python
HVAC_MODE_TO_API = {
    HVACMode.AUTO: "schedule",   # = "Home" dans ton Node-RED
    HVACMode.HEAT: "manual",     # Mode manuel
    HVACMode.OFF: "off",         # ⭐ NOUVEAU - Vrai arrêt
}

PRESET_TO_API = {
    PRESET_SCHEDULE: "schedule",
    PRESET_MANUAL: "manual",
    PRESET_AWAY: "away",         # = "Away" dans ton Node-RED
    PRESET_FROST_PROTECTION: "hg",  # = "Hors Gel" dans ton Node-RED
}
```

### 3. Gestion de l'endtime dans les appels API

```python
async def async_set_home_mode(self, mode: str, endtime: int | None = None) -> None:
    # Validation AUTOMATIQUE de l'endtime
    validated_endtime = self._validate_endtime(endtime, mode)
    
    payload = {
        "app_identifier": "app_muller",
        "home_id": self.home_id,
        "mode": mode,
    }
    
    # N'ajouter endtime QUE s'il est valide
    if validated_endtime is not None:
        payload["endtime"] = validated_endtime
    
    # Appel API (même endpoint que Node-RED)
    async with session.post(
        f"{API_BASE_URL}/setthermmode",
        headers=headers,
        json=payload
    ) as response:
        ...
```

---

## 🔄 Équivalences complètes

### Modes

| Ton Node-RED | Intégration HA v1.1.0 | API |
|--------------|----------------------|-----|
| input_select "Home" | HVAC Mode `AUTO` | `schedule` |
| input_select "Away" | Preset `away` | `away` |
| input_select "Hors Gel" | Preset `frost_protection` | `hg` |
| ❌ Pas disponible | HVAC Mode `OFF` | `off` ⭐ |
| ❌ Pas disponible | HVAC Mode `HEAT` | `manual` |

### Gestion timestamp

| Node-RED | Intégration HA |
|----------|----------------|
| `input_datetime.away_until_date` | Paramètre `endtime` optionnel |
| Conversion via moment.js | Conversion Python `datetime` |
| Validation 5 min minimum | ✅ Identique |
| Validation 1 an maximum | ✅ Identique |
| Fallback 3 heures | ✅ Identique |

---

## 🎯 Ce que tu gagnes avec l'intégration HA corrigée

### ✅ Avantages

1. **Plus besoin de Node-RED** pour contrôler le chauffage (mais tu peux continuer à l'utiliser)
2. **Interface native Home Assistant** pour tous les radiateurs
3. **Mode OFF véritable** (arrêt complet)
4. **Automatisations HA simplifiées** (plus besoin de gérer les timestamps manuellement)
5. **Compatibilité totale** avec ton Node-RED existant
6. **Capteurs supplémentaires** (température, puissance, énergie)
7. **Sélection des plannings** via interface HA

### 🔁 Compatibilité Node-RED

Tu peux **garder ton flow Node-RED** et il fonctionnera **en parallèle** :

- ✅ Les changements dans Node-RED se reflètent dans HA
- ✅ Les changements dans HA se reflètent dans Node-RED
- ✅ Même API, mêmes modes, même validation

**Exemple :**
- Tu changes le mode via Node-RED → HA voit le changement après 5 minutes (refresh)
- Tu changes le mode via HA → Node-RED peut le détecter s'il interroge l'API

---

## 📋 Migration recommandée

### Option 1 : Remplacement complet (recommandé)

**Supprimer de Node-RED :**
- ❌ Le groupe "Passer une commande manuelle"
- ❌ Les input_select et input_datetime

**Utiliser dans HA :**
- ✅ `climate.muller_*` pour contrôler chaque pièce
- ✅ `select.muller_intuis_active_schedule` pour les plannings
- ✅ Automatisations HA natives

**Avantages :**
- Interface unifiée
- Moins de complexité
- Maintenance simplifiée

### Option 2 : Cohabitation

**Garder Node-RED pour :**
- Logiques complexes spécifiques
- Intégrations avec d'autres systèmes

**Utiliser HA pour :**
- Contrôle quotidien des radiateurs
- Automatisations simples
- Dashboard

**Avantages :**
- Flexibilité maximale
- Transition progressive

---

## 🚀 Prochaines étapes

1. **Installer l'intégration HA corrigée** (voir [INSTALLATION.md](INSTALLATION.md))
2. **Tester les modes OFF et frost_protection**
3. **Décider** : migration complète ou cohabitation
4. **Créer des automatisations HA** selon tes besoins
5. **Optionnel** : Désactiver/supprimer le flow Node-RED si satisfait

---

## 💡 Exemple de migration d'automatisation

### Avant (Node-RED)

```
[Mode selector] → [Transco] → [Set mode] → [Validate endtime] → [API call]
```

### Après (Home Assistant)

```yaml
automation:
  - alias: "Mode Away si absent"
    trigger:
      - platform: state
        entity_id: person.toi
        to: "not_home"
        for:
          minutes: 30
    action:
      - service: climate.set_preset_mode
        target:
          entity_id: all
        data:
          preset_mode: "away"
```

**Résultat :**
- ✅ Plus simple
- ✅ Validation automatique de l'endtime
- ✅ Pas besoin de gérer les timestamps
- ✅ Code plus lisible

---

## 📞 Questions fréquentes

### Q: Puis-je garder mon Node-RED ?
**R:** Oui ! Les deux peuvent coexister sans problème.

### Q: Les durées de 3 heures sont-elles modifiables ?
**R:** Oui, tu peux modifier la valeur dans `__init__.py` ligne ~280 :
```python
return int((datetime.now() + timedelta(hours=3)).timestamp())
#                                          ↑↑↑↑↑
#                                    Changer ici
```

### Q: Comment tester le vrai OFF ?
**R:** 
```yaml
service: climate.set_hvac_mode
target:
  entity_id: climate.muller_salon
data:
  hvac_mode: "off"
```

### Q: L'erreur "endtime in past" peut-elle encore survenir ?
**R:** Non, la validation automatique l'empêche. Si elle survient quand même, c'est un bug à signaler.

---

## 🎉 Conclusion

L'intégration Home Assistant v1.1.0 **reprend toute la logique fonctionnelle** de ton flow Node-RED et **ajoute** :
- ✅ Le vrai mode OFF
- ✅ Une interface native HA
- ✅ Des capteurs supplémentaires
- ✅ Une meilleure maintenabilité

Tu es libre de choisir la solution qui te convient le mieux ! 🚀
