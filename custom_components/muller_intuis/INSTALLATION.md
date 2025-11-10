# Guide d'Installation - Intégration Muller Intuis Connect v1.1.0

## 📋 Prérequis

1. **Home Assistant** installé et fonctionnel
2. **Compte Muller Intuitiv** avec radiateurs configurés
3. **Application Muller Intuitiv** fonctionnelle sur smartphone
4. Accès à **dev.netatmo.com**

---

## 🔑 Étape 1 : Créer une application Netatmo

1. Rendez-vous sur https://dev.netatmo.com
2. Connectez-vous avec vos identifiants Muller Intuitiv (même email/mot de passe que l'app mobile)
3. Cliquez sur **"Create"** pour créer une nouvelle application
4. Remplissez le formulaire :
   - **App name** : `Home Assistant Muller` (ou autre nom de votre choix)
   - **Description** : `Intégration Home Assistant`
   - **Data protection officer** : Votre nom
   - **Company name** : Votre nom
   - **Company website** : `https://home-assistant.io`
5. Cliquez sur **"Save"**
6. **Notez précieusement** (gardez-les en lieu sûr) :
   - ✅ **Client ID** : Une chaîne alphanumérique (ex: `60xxxxxxxxxxxxxxxxxxxxx`)
   - ✅ **Client Secret** : Une chaîne alphanumérique (cliquez sur l'œil 👁 pour révéler)

---

## 💾 Étape 2 : Installation de l'intégration

### Option A : Via HACS (Recommandé)

1. Ouvrez **HACS** dans Home Assistant
2. Allez dans **Intégrations**
3. Cliquez sur le **menu ⋮** (3 points) en haut à droite
4. Sélectionnez **"Dépôts personnalisés"**
5. Ajoutez l'URL : `https://github.com/TheFab21/muller-intuis`
6. Catégorie : **"Integration"**
7. Cliquez sur **"Ajouter"**
8. Recherchez **"Muller Intuis Connect"** dans HACS
9. Cliquez sur **"Télécharger"**
10. **Redémarrez Home Assistant** 🔄

### Option B : Installation manuelle

1. Téléchargez tous les fichiers de ce dossier
2. Connectez-vous à votre Home Assistant via SSH ou Samba
3. Naviguez vers `/config/custom_components/`
4. Créez un dossier `muller_intuis` s'il n'existe pas
5. Copiez tous les fichiers Python dans ce dossier :
   ```
   config/
   └── custom_components/
       └── muller_intuis/
           ├── __init__.py
           ├── climate.py
           ├── config_flow.py
           ├── const.py
           ├── manifest.json
           ├── sensor.py
           ├── select.py
           └── strings.json
   ```
6. **Redémarrez Home Assistant** 🔄

---

## ⚙️ Étape 3 : Configuration dans Home Assistant

1. Allez dans **Paramètres** → **Appareils et services**
2. Cliquez sur **+ Ajouter une intégration**
3. Recherchez **"Muller Intuis Connect"**
4. Entrez vos 4 identifiants :

| Champ | Valeur | Où le trouver |
|-------|--------|---------------|
| **Client ID** | `60xxxxx...` | Sur dev.netatmo.com |
| **Client Secret** | `Xxxxxxx...` | Sur dev.netatmo.com (cliquez sur 👁) |
| **Username** | `votre@email.com` | Votre email Muller Intuitiv (app mobile) |
| **Password** | `VotreMotDePasse` | Votre mot de passe Muller Intuitiv (app mobile) |

5. Cliquez sur **"Soumettre"**
6. ✅ L'intégration va se connecter et récupérer tous vos radiateurs

---

## 🎯 Étape 4 : Vérification

### Entités créées

Pour chaque radiateur/pièce, vous devriez voir :

**Entité Climate (thermostat) :**
- `climate.muller_[nom_piece]`
  - Modes : `AUTO`, `HEAT`, `OFF`
  - Presets : `schedule`, `manual`, `away`, `frost_protection`

**Capteurs :**
- `sensor.muller_[nom_piece]_temperature` - Température mesurée
- `sensor.muller_[nom_piece]_heating_power` - Puissance de chauffe (%)
- `sensor.muller_[nom_piece]_daily_energy` - Consommation journalière (kWh)

**Sélection globale :**
- `select.muller_intuis_active_schedule` - Planning actif

### Test rapide

1. Allez dans **Paramètres** → **Appareils et services** → **Muller Intuis Connect**
2. Cliquez sur votre première pièce
3. Essayez de changer le mode ou la température
4. Vérifiez que le changement s'applique sur vos radiateurs

---

## 🏠 Utilisation

### Modes HVAC disponibles

| Mode | Description | Utilisation |
|------|-------------|-------------|
| **AUTO** | Mode planning | Suit le planning actif |
| **HEAT** | Mode manuel | Température fixe réglable |
| **OFF** | Arrêt complet | ⚠️ Radiateurs complètement éteints |

### Presets disponibles

| Preset | Description | Durée par défaut |
|--------|-------------|------------------|
| **schedule** | Suit le planning | Permanent |
| **manual** | Température manuelle | 3 heures |
| **away** | Mode absent | 3 heures |
| **frost_protection** | Hors-gel (~7°C) | Permanent |

---

## 🤖 Exemples d'automatisations

### Arrêt complet la nuit

```yaml
automation:
  - alias: "Chauffage OFF la nuit"
    trigger:
      - platform: time
        at: "23:00:00"
    action:
      - service: climate.set_hvac_mode
        target:
          entity_id:
            - climate.muller_salon
            - climate.muller_chambre
        data:
          hvac_mode: "off"
```

### Hors-gel quand absence

```yaml
automation:
  - alias: "Hors-gel si absent > 2h"
    trigger:
      - platform: state
        entity_id: person.vous
        to: "not_home"
        for:
          hours: 2
    action:
      - service: climate.set_preset_mode
        target:
          entity_id: all
        data:
          preset_mode: "frost_protection"
```

### Retour au planning le matin

```yaml
automation:
  - alias: "Planning le matin"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: climate.set_hvac_mode
        target:
          entity_id: all
        data:
          hvac_mode: "auto"
```

---

## 🔧 Dépannage

### ❌ "Authentication failed"

**Solution :**
- Vérifiez que le Client ID et Client Secret viennent bien de dev.netatmo.com
- Vérifiez que l'email et le mot de passe sont ceux de l'app Muller Intuitiv
- Testez la connexion à l'app mobile

### ❌ "No homes found"

**Solution :**
- Assurez-vous d'avoir configuré au moins un radiateur dans l'app Muller Intuitiv
- Vérifiez que vous utilisez le bon compte utilisateur

### ❌ "endtime in past"

**Cette erreur est normalement corrigée dans v1.1.0**

Si elle persiste :
- Vérifiez que vous avez bien la version 1.1.0
- Regardez les logs : Paramètres → Système → Journaux
- Recherchez "Muller" dans les logs

### ❌ Token expiré

L'intégration renouvelle automatiquement le token, mais si problème :
1. Supprimez l'intégration
2. Redémarrez Home Assistant
3. Recréez l'intégration

---

## 📊 Compatibilité Node-RED

Cette version est **100% compatible** avec Node-RED.

Vous pouvez :
- ✅ Utiliser Node-RED et Home Assistant en parallèle
- ✅ Les changements dans l'un se reflètent dans l'autre
- ✅ Partager les mêmes modes et API

---

## 📝 Logs et débogage

Pour activer les logs détaillés, ajoutez dans `configuration.yaml` :

```yaml
logger:
  default: info
  logs:
    custom_components.muller_intuis: debug
```

Puis redémarrez Home Assistant et consultez :
**Paramètres** → **Système** → **Journaux**

---

## 🆘 Support

- **GitHub Issues** : https://github.com/TheFab21/muller-intuis/issues
- **Documentation complète** : [README_CORRECTIONS.md](README_CORRECTIONS.md)

---

## ✅ Checklist finale

- [ ] Application créée sur dev.netatmo.com
- [ ] Client ID et Client Secret récupérés
- [ ] Intégration installée via HACS ou manuellement
- [ ] Home Assistant redémarré
- [ ] Intégration configurée avec les 4 identifiants
- [ ] Entités visibles dans Appareils et services
- [ ] Test de changement de mode réussi
- [ ] Automatisations créées (optionnel)

**Félicitations ! Votre intégration Muller Intuis Connect est opérationnelle ! 🎉**
