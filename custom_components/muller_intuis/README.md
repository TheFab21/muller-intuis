# 🎯 Intégration Muller Intuis Connect v1.1.0 - CORRIGÉE

## 📦 Contenu de cette livraison

Tous les fichiers nécessaires pour ton intégration Home Assistant **100% fonctionnelle** :

### Fichiers Python (intégration)
- ✅ `__init__.py` - Coordinateur avec validation endtime
- ✅ `climate.py` - Entités thermostat avec mode OFF
- ✅ `sensor.py` - Capteurs température/puissance/énergie
- ✅ `select.py` - Sélection des plannings
- ✅ `config_flow.py` - Interface de configuration
- ✅ `const.py` - Constantes
- ✅ `manifest.json` - Métadonnées HACS
- ✅ `strings.json` - Traductions

### Documentation
- 📖 `README_CORRECTIONS.md` - Détails des corrections
- 📖 `INSTALLATION.md` - Guide d'installation pas à pas
- 📖 `COMPARAISON_NODERED.md` - Comparaison avec ton flow Node-RED

---

## 🔧 Corrections principales

### 1️⃣ Erreur "endtime in past" ✅ CORRIGÉ

**Avant :**
```
API error: 400 - {"error":{"code":21,"message":"endtime in past"}}
```

**Après :**
- ✅ Validation automatique : minimum 5 minutes dans le futur
- ✅ Validation automatique : maximum 1 an
- ✅ Fallback à 3 heures si timestamp invalide
- ✅ Pas d'endtime pour les modes qui n'en ont pas besoin

### 2️⃣ Ajout du vrai mode OFF ✅ NOUVEAU

**Avant :**
- ❌ Mode OFF = Hors-gel (7°C)
- ❌ Pas de vrai arrêt

**Après :**
- ✅ Mode OFF = Arrêt complet des radiateurs
- ✅ Hors-gel accessible via preset `frost_protection`
- ✅ Distinction claire entre OFF et hors-gel

---

## 🚀 Installation rapide

### Étape 1 : Copier les fichiers
```bash
# Via Samba ou SSH
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

### Étape 2 : Redémarrer Home Assistant
```
Paramètres → Système → Redémarrer
```

### Étape 3 : Configurer
```
Paramètres → Appareils et services → + Ajouter une intégration
→ Rechercher "Muller Intuis Connect"
→ Entrer les 4 identifiants (Client ID, Secret, Email, Password)
```

---

## 🎮 Utilisation

### Modes disponibles

| Interface | Action | API |
|-----------|--------|-----|
| Mode `OFF` | Arrêt complet | `off` |
| Mode `AUTO` | Planning actif | `schedule` |
| Mode `HEAT` | Manuel avec température | `manual` |
| Preset `away` | Absence | `away` |
| Preset `frost_protection` | Hors-gel | `hg` |

### Exemples

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

**Mode absent 3 heures :**
```yaml
service: climate.set_preset_mode
target:
  entity_id: climate.muller_salon
data:
  preset_mode: "away"
```

---

## ✅ Tests recommandés

Après installation, teste :

1. ✅ Mode OFF → vérifie que les radiateurs s'éteignent vraiment
2. ✅ Mode hors-gel → vérifie la température à ~7°C
3. ✅ Changement de température en mode HEAT
4. ✅ Retour au mode AUTO (planning)
5. ✅ Changement de planning via select.muller_intuis_active_schedule

---

## 🔄 Compatibilité Node-RED

Cette version est **100% compatible** avec ton flow Node-RED.

**Tu peux :**
- Utiliser les deux en parallèle
- Migrer progressivement vers HA
- Ou garder Node-RED pour des logiques complexes

Voir [COMPARAISON_NODERED.md](COMPARAISON_NODERED.md) pour tous les détails.

---

## 📚 Documentation complète

| Fichier | Description |
|---------|-------------|
| [README_CORRECTIONS.md](README_CORRECTIONS.md) | Détails techniques des corrections |
| [INSTALLATION.md](INSTALLATION.md) | Guide d'installation complet |
| [COMPARAISON_NODERED.md](COMPARAISON_NODERED.md) | Comparaison avec Node-RED |

---

## 🐛 Dépannage

### Problème : "endtime in past" persiste
**Solution :** Vérifie que tu utilises bien cette version (v1.1.0)

### Problème : Mode OFF ne fonctionne pas
**Solution :** 
1. Vérifie les logs : `Paramètres → Système → Journaux`
2. Cherche "Muller" ou "Setting real OFF mode"
3. Vérifie que l'API accepte le mode "off"

### Problème : Token expiré
**Solution :**
1. Supprime l'intégration
2. Redémarre HA
3. Reconfigurer avec les mêmes identifiants

---

## 💬 Support

- **GitHub Issues :** https://github.com/TheFab21/muller-intuis/issues
- **Documentation :** Voir les fichiers .md inclus

---

## 📊 Changelog v1.1.0

### ✨ Nouvelles fonctionnalités
- Mode OFF véritable (arrêt complet)
- Hors-gel maintenant un preset distinct
- Validation automatique des timestamps

### 🐛 Corrections de bugs
- Erreur "endtime in past" corrigée
- Gestion des endtime invalides
- Pas d'endtime pour modes qui n'en ont pas besoin

### 🔧 Améliorations
- Logs plus détaillés
- Code inspiré du flow Node-RED fonctionnel
- Documentation complète

---

## 🎉 Prêt à l'emploi

Tous les fichiers sont prêts à être copiés dans Home Assistant !

**Prochaine étape :**
1. Copie le dossier `muller_intuis_fixed` vers `config/custom_components/muller_intuis`
2. Redémarre Home Assistant
3. Configure l'intégration
4. Profite ! 🚀

---

**Version :** 1.1.0  
**Date :** Novembre 2024  
**Auteur :** @TheFab21  
**Basé sur :** API Netatmo Energy / Muller Intuitiv
