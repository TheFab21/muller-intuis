# Muller Intuis Connect - Intégration Home Assistant

Cette intégration personnalisée permet de contrôler vos radiateurs **Muller Intuis Connect** via Home Assistant. Elle utilise l'API Netatmo Energy (backend de Muller Intuitiv).

## 🔑 Prérequis - Obtenir les identifiants

### Étape 1 : Créer une application sur le portail développeur Netatmo

1. Allez sur [https://dev.netatmo.com/](https://dev.netatmo.com/)
2. Connectez-vous avec vos identifiants Muller Intuitiv (email/mot de passe)
3. Cliquez sur **"Create"** pour créer une nouvelle application
4. Remplissez les informations :
   - **App name** : Choisissez un nom (ex: "Home Assistant Muller")
   - **Description** : Description de votre choix
   - **Data protection officer** : Votre nom
   - **Company name** : Votre nom ou entreprise
   - **Company website** : Vous pouvez mettre `https://home-assistant.io`
5. Cliquez sur **"Save"**
6. Notez précieusement :
   - **Client ID** : Chaîne alphanumérique
   - **Client Secret** : Chaîne alphanumérique (cliquez sur l'œil pour révéler)

### Étape 2 : Préparer vos identifiants

Vous aurez besoin de 4 informations pour configurer l'intégration :

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| **Client ID** | Obtenu sur dev.netatmo.com | `60xxxxxxxxxxxxxxxxxxxxx` |
| **Client Secret** | Obtenu sur dev.netatmo.com | `Xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxv` |
| **Username** | Votre email Muller Intuitiv | `votre.email@exemple.com` |
| **Password** | Votre mot de passe Muller Intuitiv | `VotreMotDePasse` |

⚠️ **Important** : Utilisez les mêmes identifiants (email/mot de passe) que vous utilisez pour vous connecter à l'application mobile Muller Intuitiv.

## 📥 Installation

### Méthode 1 : Via HACS (Recommandé)

1. Ouvrez **HACS** dans Home Assistant
2. Cliquez sur **"Intégrations"**
3. Cliquez sur le menu **⋮** (3 points) en haut à droite
4. Sélectionnez **"Dépôts personnalisés"**
5. Ajoutez l'URL : `https://github.com/TheFab21/muller-intuis`
6. Sélectionnez la catégorie : **"Integration"**
7. Cliquez sur **"Ajouter"**
8. Recherchez **"Muller Intuis Connect"** dans HACS
9. Cliquez sur **"Télécharger"**
10. **Redémarrez Home Assistant**

### Méthode 2 : Installation manuelle

1. Téléchargez le dossier `custom_components/muller_intuis`
2. Copiez-le dans le dossier `custom_components` de votre Home Assistant
3. Votre structure doit ressembler à :
   ```
   config/
   └── custom_components/
       └── muller_intuis/
           ├── __init__.py
           ├── config_flow.py
           ├── const.py
           ├── manifest.json
           ├── strings.json
           ├── climate.py
           ├── sensor.py
           └── select.py
   ```
4. **Redémarrez Home Assistant**

## ⚙️ Configuration

### Ajouter l'intégration

1. Allez dans **Paramètres** → **Appareils et services**
2. Cliquez sur **+ Ajouter une intégration**
3. Recherchez **"Muller Intuis Connect"**
4. Entrez vos 4 identifiants :
   - **Client ID** (de dev.netatmo.com)
   - **Client Secret** (de dev.netatmo.com)
   - **Username** (votre email Muller)
   - **Password** (votre mot de passe Muller)
5. Cliquez sur **"Soumettre"**

L'intégration va :
- ✅ Se connecter à l'API Muller Intuitiv
- ✅ Récupérer automatiquement votre `home_id`
- ✅ Créer toutes les entités pour vos radiateurs

## 🎛️ Entités créées

Pour chaque radiateur/pièce, l'intégration crée :

### Climate (Thermostat)
- **Entité** : `climate.muller_[nom_piece]`
- **Modes HVAC** :
  - `auto` : Mode planning (suit le planning actif)
  - `heat` : Mode manuel (température fixe)
  - `off` : Hors-gel
- **Presets** :
  - `Schedule` : Suit le planning
  - `Manual` : Température manuelle
  - `Away` : Mode absent
  - `Frost Protection` : Hors-gel

### Sensors
- **Température actuelle** : `sensor.muller_[nom_piece]_temperature`
- **Puissance de chauffe** : `sensor.muller_[nom_piece]_heating_power_request`
- **Consommation journalière** : `sensor.muller_[nom_piece]_daily_energy`

### Select
- **Planning actif** : `select.muller_intuis_active_schedule`
  - Permet de changer facilement le planning actif
  - Liste tous les plannings disponibles

## 🔧 Utilisation

### Contrôler la température d'une pièce

```yaml
service: climate.set_temperature
target:
  entity_id: climate.muller_salon
data:
  temperature: 21
```

### Changer le mode HVAC

```yaml
service: climate.set_hvac_mode
target:
  entity_id: climate.muller_salon
data:
  hvac_mode: heat  # ou auto, off
```

### Changer de planning

Via l'entité select :
```yaml
service: select.select_option
target:
  entity_id: select.muller_intuis_active_schedule
data:
  option: "Planning Jour"
```

## 🐛 Dépannage

### L'authentification échoue

1. **Vérifiez vos identifiants** :
   - Client ID et Client Secret doivent venir de [dev.netatmo.com](https://dev.netatmo.com)
   - Username et Password sont ceux de l'app Muller Intuitiv
2. **Testez vos identifiants** dans l'application mobile Muller Intuitiv
3. **Vérifiez les logs** : Paramètres → Système → Journaux

### Erreur "No homes found"

L'API ne trouve pas de maison associée à votre compte. Vérifiez que :
- Vous avez bien des radiateurs configurés dans l'app Muller Intuitiv
- Vous utilisez les bons identifiants

### Les températures ne se mettent pas à jour

- L'intégration rafraîchit les données toutes les **5 minutes**
- Vous pouvez forcer une mise à jour via le service `homeassistant.update_entity`

### Erreur 401 (Authentication failed)

Le token a expiré. L'intégration le renouvelle automatiquement, mais si l'erreur persiste :
1. Supprimez l'intégration
2. Recréez-la avec vos identifiants

## 📊 Exemple de carte Lovelace

```yaml
type: vertical-stack
cards:
  - type: entities
    title: Contrôle Chauffage
    entities:
      - entity: select.muller_intuis_active_schedule
        name: Planning actif
      - entity: climate.muller_salon
        name: Salon
      - entity: climate.muller_chambre
        name: Chambre
  
  - type: thermostat
    entity: climate.muller_salon
    name: Salon
```

## 🔄 Automatisations

### Changer de planning selon l'heure

```yaml
automation:
  - alias: "Chauffage - Planning Jour"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: select.select_option
        target:
          entity_id: select.muller_intuis_active_schedule
        data:
          option: "Planning Jour"

  - alias: "Chauffage - Planning Nuit"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: select.select_option
        target:
          entity_id: select.muller_intuis_active_schedule
        data:
          option: "Planning Nuit"
```

### Mode absent automatique

```yaml
automation:
  - alias: "Chauffage - Mode absent"
    trigger:
      - platform: state
        entity_id: person.vous
        to: "not_home"
        for:
          hours: 1
    action:
      - service: climate.set_preset_mode
        target:
          entity_id: 
            - climate.muller_salon
            - climate.muller_chambre
        data:
          preset_mode: "away"
```

## 📝 Notes techniques

- **API utilisée** : Netatmo Energy API (backend Muller Intuitiv)
- **Endpoint OAuth2** : `https://app.muller-intuitiv.net/oauth2/token`
- **Grant type** : `password` (Resource Owner Password Credentials)
- **Scopes** : `read_muller write_muller`
- **User prefix** : `muller`
- **Rafraîchissement token** : Automatique, 5 minutes avant expiration
- **Intervalle de mise à jour** : 5 minutes

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Ouvrir une issue pour signaler un bug
- Proposer une pull request pour ajouter des fonctionnalités
- Améliorer la documentation

## 📜 Licence

MIT License

## 🙏 Remerciements

- Basé sur l'API Netatmo Energy
- Inspiré du travail de la communauté Home Assistant
