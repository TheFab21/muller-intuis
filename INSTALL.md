# Guide d'installation détaillé - Muller Intuis Connect

## Table des matières
1. [Prérequis](#prérequis)
2. [Installation de l'intégration](#installation-de-lintégration)
3. [Obtention des identifiants API](#obtention-des-identifiants-api)
4. [Configuration dans Home Assistant](#configuration-dans-home-assistant)
5. [Installation de l'interface de gestion des plannings](#installation-de-linterface-de-gestion-des-plannings)
6. [Vérification et test](#vérification-et-test)
7. [Migration depuis Node-RED](#migration-depuis-node-red)

---

## Prérequis

### Matériel requis
- Radiateurs Muller Intuis Connect installés et fonctionnels
- Compte Netatmo configuré avec vos radiateurs
- Home Assistant installé (version 2023.1 ou supérieure recommandée)

### Connaissances requises
- Accès à l'interface d'administration de Home Assistant
- Capacité à éditer des fichiers YAML (optionnel)
- Compréhension basique de l'API REST

---

## Installation de l'intégration

### Méthode 1 : Via HACS (recommandé)

1. **Installer HACS** (si ce n'est pas déjà fait)
   - Suivez le guide officiel : https://hacs.xyz/docs/setup/download

2. **Ajouter le dépôt personnalisé**
   - Ouvrez HACS dans Home Assistant
   - Cliquez sur "Intégrations"
   - Cliquez sur les 3 points en haut à droite → "Dépôts personnalisés"
   - Ajoutez l'URL : `https://github.com/votreusername/muller_intuis`
   - Catégorie : `Integration`
   - Cliquez sur "Ajouter"

3. **Installer l'intégration**
   - Recherchez "Muller Intuis Connect" dans HACS
   - Cliquez sur "Télécharger"
   - Redémarrez Home Assistant

### Méthode 2 : Installation manuelle

1. **Télécharger les fichiers**
   ```bash
   cd /config
   mkdir -p custom_components
   cd custom_components
   git clone https://github.com/votreusername/muller_intuis.git
   # OU téléchargez et décompressez le zip
   ```

2. **Vérifier la structure**
   ```
   /config/custom_components/muller_intuis/
   ├── __init__.py
   ├── api.py
   ├── climate.py
   ├── config_flow.py
   ├── const.py
   ├── manifest.json
   ├── select.py
   ├── sensor.py
   ├── services.yaml
   ├── strings.json
   └── translations/
       └── fr.json
   ```

3. **Redémarrer Home Assistant**

---

## Obtention des identifiants API

### Étape 1 : Créer une application Netatmo

1. Allez sur le [portail développeur Netatmo](https://dev.netatmo.com/apps/createanapp)
2. Connectez-vous avec votre compte Netatmo
3. Créez une nouvelle application :
   - **Nom** : `Home Assistant Muller Intuis`
   - **Description** : `Intégration pour Home Assistant`
   - **Data Protection Officer** : Votre email
   - Cochez "J'ai lu et accepte les conditions"
   - Cliquez sur "Créer"

4. **Notez vos identifiants** :
   - `Client ID` : Une longue chaîne de caractères
   - `Client Secret` : Une autre longue chaîne de caractères

### Étape 2 : Obtenir le Refresh Token

#### Méthode A : Via l'outil en ligne (simple)

1. Allez sur : https://dev.netatmo.com/apidocumentation/oauth
2. Cliquez sur "GET TOKEN"
3. Choisissez les scopes nécessaires :
   - ✅ `read_thermostat`
   - ✅ `write_thermostat`
4. Cliquez sur "Generate Token"
5. Connectez-vous à votre compte Netatmo
6. Autorisez l'application
7. **Copiez le `refresh_token`** (pas l'access_token !)

#### Méthode B : Manuellement (avancé)

1. **Construire l'URL d'autorisation**
   ```
   https://api.netatmo.com/oauth2/authorize?
     client_id=VOTRE_CLIENT_ID&
     redirect_uri=https://localhost&
     scope=read_thermostat%20write_thermostat&
     state=test
   ```

2. **Ouvrir dans un navigateur**
   - Connectez-vous et autorisez
   - Vous serez redirigé vers une URL comme :
     ```
     https://localhost?code=AUTHORIZATION_CODE&state=test
     ```
   - Copiez le `AUTHORIZATION_CODE`

3. **Échanger le code contre un refresh token**
   ```bash
   curl -X POST https://api.netatmo.com/oauth2/token \
     -d "grant_type=authorization_code" \
     -d "client_id=VOTRE_CLIENT_ID" \
     -d "client_secret=VOTRE_CLIENT_SECRET" \
     -d "code=AUTHORIZATION_CODE" \
     -d "redirect_uri=https://localhost" \
     -d "scope=read_thermostat write_thermostat"
   ```

4. **Extraire le refresh_token** de la réponse JSON

### Étape 3 : Trouver votre Home ID (optionnel)

Si vous avez plusieurs maisons dans Netatmo :

1. Une fois l'intégration configurée avec un home_id vide, consultez les logs
2. L'intégration listera les home_id disponibles
3. Reconfigurez avec le bon home_id

---

## Configuration dans Home Assistant

### Configuration initiale

1. **Accéder aux intégrations**
   - Configuration → Appareils et services → Intégrations
   - Cliquez sur "+ Ajouter une intégration"
   - Recherchez "Muller Intuis Connect"

2. **Entrer les identifiants**
   - `Client ID` : Collez votre Client ID Netatmo
   - `Client Secret` : Collez votre Client Secret
   - Cliquez sur "Soumettre"

3. **Configuration OAuth**
   - `Client ID` : (déjà rempli)
   - `Client Secret` : (déjà rempli)
   - `Refresh Token` : Collez le refresh_token obtenu
   - `Home ID` : Laissez vide ou entrez votre home_id
   - Cliquez sur "Soumettre"

4. **Vérification**
   - L'intégration devrait se configurer
   - Vous verrez un message de succès
   - Les entités seront créées automatiquement

### Vérifier les entités créées

1. **Allez dans** : Configuration → Entités
2. **Filtrez par** : `muller_intuis`
3. **Vous devriez voir** :
   - `climate.muller_intuis_[nom_piece]` pour chaque radiateur
   - `sensor.muller_intuis_[nom_piece]_temperature`
   - `sensor.muller_intuis_[nom_piece]_heating_power`
   - `sensor.muller_intuis_[nom_piece]_daily_energy`
   - `sensor.muller_intuis_schedule_[nom_planning]` pour chaque planning
   - `sensor.muller_intuis_active_schedule`
   - `select.muller_intuis_active_schedule`

---

## Installation de l'interface de gestion des plannings

### Copier le fichier HTML

1. **Créer le dossier www** (s'il n'existe pas)
   ```bash
   cd /config
   mkdir -p www
   ```

2. **Copier le fichier**
   - Copiez `muller_planning.html` dans `/config/www/`
   - Ou créez-le directement avec le contenu fourni

3. **Vérifier les permissions**
   ```bash
   chmod 644 /config/www/muller_planning.html
   ```

### Ajouter la carte dans Lovelace

1. **Mode édition**
   - Ouvrez votre dashboard
   - Cliquez sur les 3 points → "Modifier le tableau de bord"

2. **Ajouter une carte**
   - Cliquez sur "+ Ajouter une carte"
   - Choisissez "Iframe"
   - Configuration :
     ```yaml
     type: iframe
     url: /local/muller_planning.html
     aspect_ratio: 75%
     ```

3. **Sauvegarder**

### Alternative : Carte YAML complète

Créez une vue dédiée avec la configuration fournie dans `lovelace_examples.md`

---

## Vérification et test

### Test des entités Climate

1. **Sélectionner un radiateur**
   - Allez dans Aperçu → Contrôles
   - Cliquez sur un radiateur

2. **Tester les contrôles**
   - Changez la température → Vérifiez sur le radiateur physique
   - Changez le mode (Auto/Heat/Off)
   - Changez le preset (Schedule/Away/etc.)

### Test des services

1. **Ouvrir les Outils de développement**
   - Outils de développement → Services

2. **Tester le service set_schedule**
   ```yaml
   service: muller_intuis.set_schedule
   data:
     schedule_id: "votre_schedule_id"
   ```
   (Récupérez le schedule_id depuis les attributs d'un capteur de planning)

3. **Tester le service set_home_mode**
   ```yaml
   service: muller_intuis.set_home_mode
   data:
     mode: away
   ```

### Vérifier les logs

1. **Activer les logs de débogage** (optionnel)
   - Éditez `configuration.yaml` :
     ```yaml
     logger:
       default: info
       logs:
         custom_components.muller_intuis: debug
     ```
   - Redémarrez Home Assistant

2. **Consulter les logs**
   - Configuration → Système → Journaux
   - Filtrez par "muller_intuis"

---

## Migration depuis Node-RED

### Mappage des fonctionnalités

| Node-RED | Home Assistant |
|----------|----------------|
| MQTT publish `cmnd/set_therm_mode` | Service `muller_intuis.set_home_mode` |
| MQTT publish `cmnd/set_thermpoint` | Service `muller_intuis.set_room_thermpoint` |
| MQTT publish `plannings/[id]/set` | Service `muller_intuis.sync_schedule` |
| MQTT subscribe `stat/homestatus` | Capteur `sensor.muller_intuis_*` |
| Flow récupération stats | Capteur `sensor.*_daily_energy` |

### Migration étape par étape

1. **Phase 1 : Fonctionnement en parallèle**
   - Gardez Node-RED actif
   - Installez l'intégration Home Assistant
   - Testez les deux systèmes en parallèle

2. **Phase 2 : Migration des automatisations**
   - Recréez vos automatisations Node-RED dans Home Assistant
   - Testez chaque automatisation individuellement
   - Désactivez les flows Node-RED correspondants

3. **Phase 3 : Migration de l'interface**
   - Créez votre dashboard Lovelace
   - Installez l'interface HTML de gestion des plannings
   - Vérifiez que tout fonctionne

4. **Phase 4 : Désactivation Node-RED**
   - Désactivez complètement vos flows Node-RED
   - Surveillez pendant quelques jours
   - Supprimez Node-RED si tout fonctionne

### Récupération des ID

Pour récupérer vos `room_id` et `schedule_id` depuis Node-RED :

1. **Dans Node-RED**, consultez vos flows
2. **Notez les ID** utilisés dans vos requêtes API
3. **Dans Home Assistant**, vérifiez les attributs des entités pour retrouver les mêmes ID

---

## Dépannage courant

### Erreur "cannot_connect"
- Vérifiez votre Client ID et Client Secret
- Assurez-vous que votre application Netatmo est active
- Vérifiez votre connexion Internet

### Erreur "invalid_auth"
- Votre refresh_token est probablement expiré
- Régénérez un nouveau refresh_token
- Reconfigurez l'intégration

### Les entités ne se mettent pas à jour
- Vérifiez les logs pour les erreurs API
- Rafraîchissez manuellement : `homeassistant.update_entity`
- Vérifiez votre limite de requêtes API Netatmo

### L'interface HTML ne fonctionne pas
- Vérifiez que le fichier est bien dans `/config/www/`
- Videz le cache de votre navigateur (Ctrl+F5)
- Consultez la console JavaScript (F12)

### Les plannings ne se synchronisent pas
- Vérifiez le format JSON de vos zones et timetable
- Consultez les logs pour les erreurs détaillées
- Testez avec un planning simple d'abord

---

## Support et contribution

### Obtenir de l'aide
- GitHub Issues : https://github.com/votreusername/muller_intuis/issues
- Forum Home Assistant : https://community.home-assistant.io/

### Contribuer
Les contributions sont les bienvenues ! Consultez `CONTRIBUTING.md` pour plus d'informations.

---

## Ressources supplémentaires

- [Documentation API Netatmo](https://dev.netatmo.com/apidocumentation/energy)
- [Documentation Home Assistant](https://www.home-assistant.io/docs/)
- [Guide HACS](https://hacs.xyz/docs/basic/getting_started)
