# Intégration Muller Intuis Connect pour Home Assistant

Cette intégration personnalisée permet de contrôler vos radiateurs Muller Intuis Connect via Home Assistant. Elle s'appuie sur l'API Netatmo Energy.

## Fonctionnalités

### ✅ Entités Climate
- **Contrôle individuel** de chaque radiateur
- **Modes supportés** : Auto (schedule), Heat (manuel), Off
- **Presets** : Schedule, Away, Frost Protection (Hors-gel), Manual
- **Température** : Consultation et modification de la consigne

### ✅ Capteurs
- **Température actuelle** de chaque pièce
- **Puissance de chauffe** (en Watts)
- **Consommation énergétique** journalière (en kWh)
- **Planning actif**
- **État de chaque planning** avec attributs complets (timetable, zones, etc.)

### ✅ Sélecteur de Planning
- Entité `select` pour **changer facilement le planning actif**

### ✅ Services Personnalisés

#### `muller_intuis.set_schedule`
Change le planning actif
```yaml
service: muller_intuis.set_schedule
data:
  schedule_id: "1234567890"
```

#### `muller_intuis.sync_schedule`
Met à jour un planning existant
```yaml
service: muller_intuis.sync_schedule
data:
  schedule_id: "1234567890"
  name: "Mon planning modifié"
  timetable:
    - m_offset: 0
      zone_id: 0
    - m_offset: 420
      zone_id: 1
  zones:
    - id: 0
      name: "Confort"
      rooms_temp:
        - room_id: "123456"
          temp: 20.5
```

#### `muller_intuis.create_schedule`
Crée un nouveau planning
```yaml
service: muller_intuis.create_schedule
data:
  name: "Planning vacances"
  timetable: [...]
  zones: [...]
```

#### `muller_intuis.delete_schedule`
Supprime un planning
```yaml
service: muller_intuis.delete_schedule
data:
  schedule_id: "1234567890"
```

#### `muller_intuis.rename_schedule`
Renomme un planning
```yaml
service: muller_intuis.rename_schedule
data:
  schedule_id: "1234567890"
  name: "Nouveau nom"
```

#### `muller_intuis.set_room_thermpoint`
Définit la température d'une pièce
```yaml
service: muller_intuis.set_room_thermpoint
data:
  room_id: "1234567890"
  mode: "manual"
  temp: 21.5
```

#### `muller_intuis.set_home_mode`
Définit le mode global de la maison
```yaml
service: muller_intuis.set_home_mode
data:
  mode: "schedule"
  schedule_id: "1234567890"  # optionnel
```

## Installation

### Via HACS (recommandé)

1. Ouvrez HACS dans Home Assistant
2. Cliquez sur "Intégrations"
3. Cliquez sur le menu (3 points) en haut à droite
4. Sélectionnez "Dépôts personnalisés"
5. Ajoutez l'URL de ce repository
6. Installez l'intégration "Muller Intuis Connect"
7. Redémarrez Home Assistant

### Installation manuelle

1. Copiez le dossier `muller_intuis` dans `custom_components/`
2. Redémarrez Home Assistant

## Configuration

### Prérequis : Obtenir les identifiants OAuth

1. Créez une application sur le [portail développeur Netatmo](https://dev.netatmo.com/)
2. Notez votre `Client ID` et `Client Secret`
3. Pour obtenir votre `refresh_token`, suivez [ce guide](https://dev.netatmo.com/apidocumentation/oauth)

### Configuration dans Home Assistant

1. Allez dans **Configuration** → **Intégrations**
2. Cliquez sur **+ Ajouter une intégration**
3. Recherchez **Muller Intuis Connect**
4. Entrez vos identifiants :
   - Client ID
   - Client Secret
   - Refresh Token
   - Home ID (optionnel, sera détecté automatiquement)

## Interface Lovelace pour la gestion des plannings

Vous pouvez créer une interface graphique pour éditer vos plannings directement dans Home Assistant. Voici un exemple de carte personnalisée :

### Carte basique

```yaml
type: vertical-stack
cards:
  - type: entities
    title: Contrôle des chauffages
    entities:
      - entity: select.muller_intuis_active_schedule
        name: Planning actif
      - entity: sensor.muller_intuis_active_schedule
        name: Détails du planning

  - type: horizontal-stack
    cards:
      - type: button
        name: Mode Schedule
        tap_action:
          action: call-service
          service: muller_intuis.set_home_mode
          service_data:
            mode: schedule
      - type: button
        name: Mode Absent
        tap_action:
          action: call-service
          service: muller_intuis.set_home_mode
          service_data:
            mode: away
      - type: button
        name: Hors-gel
        tap_action:
          action: call-service
          service: muller_intuis.set_home_mode
          service_data:
            mode: hg
```

### Interface avancée avec page HTML personnalisée

Pour reproduire l'interface de votre flow Node-RED, créez un fichier `www/muller_planning.html` dans votre configuration Home Assistant :

1. Créez le dossier `www` s'il n'existe pas
2. Copiez le fichier HTML fourni dans `www/muller_planning.html`
3. Modifiez les topics MQTT si nécessaire
4. Ajoutez une carte `iframe` dans Lovelace :

```yaml
type: iframe
url: /local/muller_planning.html
aspect_ratio: 75%
```

## Automatisations

### Changer de planning selon le moment de la journée

```yaml
automation:
  - alias: "Chauffage - Planning jour"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: muller_intuis.set_schedule
        data:
          schedule_id: "id_planning_jour"

  - alias: "Chauffage - Planning nuit"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: muller_intuis.set_schedule
        data:
          schedule_id: "id_planning_nuit"
```

### Mode absent lors de l'absence

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
      - service: muller_intuis.set_home_mode
        data:
          mode: away
```

## Dépannage

### Les tokens expirent régulièrement
- L'intégration rafraîchit automatiquement les tokens
- Si le problème persiste, reconfigurer l'intégration

### Les données ne se mettent pas à jour
- Vérifiez les logs : **Configuration** → **Logs**
- L'intervalle de mise à jour par défaut est de 5 minutes
- Vous pouvez forcer une mise à jour via le service `homeassistant.update_entity`

### Erreur d'authentification
- Vérifiez que votre `Client ID` et `Client Secret` sont corrects
- Assurez-vous que votre `refresh_token` est valide
- Regénérez un nouveau refresh token si nécessaire

## Migration depuis Node-RED

Si vous utilisez actuellement Node-RED :

1. **Notez vos room_id et schedule_id** depuis vos flows
2. **Installez l'intégration** comme décrit ci-dessus
3. **Recréez vos automatisations** avec les services Home Assistant
4. **Pour MQTT** : vous pouvez continuer à l'utiliser en parallèle ou migrer entièrement vers les services

## Contribuer

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## Licence

MIT License

## Crédits

Développé pour l'intégration des radiateurs Muller Intuis Connect dans Home Assistant.
Basé sur l'API Netatmo Energy.
