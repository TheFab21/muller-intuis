# 🚀 Démarrage Rapide - 5 minutes

## Ce qui a été corrigé

✅ **Erreur "endtime in past"** → Validation automatique des timestamps  
✅ **Ajout du vrai mode OFF** → Arrêt complet des radiateurs  
✅ **Hors-gel en preset** → Distinction claire OFF vs hors-gel  

---

## Installation en 3 étapes

### 1️⃣ Copier les fichiers (2 min)

**Option A : Décompresser le ZIP**
```
Extraire muller_intuis_v1.1.0.zip
→ Copier le dossier muller_intuis_fixed
→ Renommer en muller_intuis
→ Placer dans config/custom_components/
```

**Option B : Via Samba/SSH**
```bash
# Structure finale :
config/
└── custom_components/
    └── muller_intuis/
        ├── __init__.py
        ├── climate.py
        ├── sensor.py
        ├── select.py
        ├── config_flow.py
        ├── const.py
        ├── manifest.json
        └── strings.json
```

### 2️⃣ Redémarrer Home Assistant (1 min)
```
Paramètres → Système → Redémarrer
```

### 3️⃣ Configurer (2 min)
```
Paramètres → Appareils et services 
→ + Ajouter une intégration 
→ "Muller Intuis Connect"
→ Entrer :
   - Client ID (depuis dev.netatmo.com)
   - Client Secret (depuis dev.netatmo.com)
   - Email Muller Intuitiv
   - Mot de passe Muller Intuitiv
```

---

## Test rapide

### Test 1 : Vrai OFF
```yaml
# Dans Outils pour développeurs → Services
service: climate.set_hvac_mode
target:
  entity_id: climate.muller_salon
data:
  hvac_mode: "off"
```
➡️ **Vérifie que les radiateurs s'éteignent vraiment**

### Test 2 : Hors-gel
```yaml
service: climate.set_preset_mode
target:
  entity_id: climate.muller_salon
data:
  preset_mode: "frost_protection"
```
➡️ **Vérifie température ~7°C**

### Test 3 : Retour au planning
```yaml
service: climate.set_hvac_mode
target:
  entity_id: climate.muller_salon
data:
  hvac_mode: "auto"
```
➡️ **Vérifie retour au planning actif**

---

## Modes disponibles

### HVAC Modes (bouton principal)
- **OFF** → Arrêt complet ⭐ **NOUVEAU**
- **AUTO** → Suit le planning
- **HEAT** → Température manuelle

### Presets (modes avancés)
- **schedule** → Planning
- **manual** → Manuel avec température
- **away** → Absent (3h par défaut)
- **frost_protection** → Hors-gel (~7°C)

---

## Automatisations utiles

### OFF la nuit
```yaml
automation:
  - alias: "Chauffage OFF 23h"
    trigger:
      platform: time
      at: "23:00:00"
    action:
      service: climate.set_hvac_mode
      target:
        entity_id: all
      data:
        hvac_mode: "off"
```

### Planning le matin
```yaml
automation:
  - alias: "Planning 7h"
    trigger:
      platform: time
      at: "07:00:00"
    action:
      service: climate.set_hvac_mode
      target:
        entity_id: all
      data:
        hvac_mode: "auto"
```

### Hors-gel si absent
```yaml
automation:
  - alias: "Hors-gel si absent 2h"
    trigger:
      platform: state
      entity_id: person.vous
      to: "not_home"
      for:
        hours: 2
    action:
      service: climate.set_preset_mode
      target:
        entity_id: all
      data:
        preset_mode: "frost_protection"
```

---

## Problème ?

### ❌ "endtime in past" persiste
→ Vérifie version 1.1.0 dans `manifest.json`

### ❌ Mode OFF ne marche pas
→ Vérifie les logs : `Paramètres → Système → Journaux`  
→ Recherche "Setting real OFF mode"

### ❌ Intégration invisible
→ Vérifie que les fichiers sont dans `custom_components/muller_intuis`  
→ Redémarre HA

### ❌ Authentification échoue
→ Vérifie Client ID/Secret sur dev.netatmo.com  
→ Vérifie email/mot de passe de l'app Muller Intuitiv

---

## Documentation complète

- **[README.md](README.md)** - Vue d'ensemble
- **[INSTALLATION.md](INSTALLATION.md)** - Guide détaillé
- **[README_CORRECTIONS.md](README_CORRECTIONS.md)** - Détails techniques
- **[COMPARAISON_NODERED.md](COMPARAISON_NODERED.md)** - vs Node-RED

---

## ✅ C'est tout !

Tu as maintenant :
- ✅ L'erreur "endtime in past" corrigée
- ✅ Un vrai mode OFF fonctionnel
- ✅ Le hors-gel accessible en preset
- ✅ Une intégration compatible avec Node-RED
- ✅ Des automatisations simplifiées

**Bon chauffage ! 🔥**
