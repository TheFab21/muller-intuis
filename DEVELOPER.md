# Guide de développement - Muller Intuis Connect

## Architecture de l'intégration

### Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                     Home Assistant                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Muller Intuis Integration                   │   │
│  │                                                      │   │
│  │  ┌──────────────┐      ┌──────────────┐            │   │
│  │  │  Coordinator │◄─────┤     API      │            │   │
│  │  │              │      │   Client     │            │   │
│  │  └──────┬───────┘      └──────▲───────┘            │   │
│  │         │                     │                     │   │
│  │    ┌────▼────┐  ┌────────┐   │                     │   │
│  │    │ Climate │  │ Sensor │   │                     │   │
│  │    │ Entities│  │Entities│   │                     │   │
│  │    └─────────┘  └────────┘   │                     │   │
│  │    ┌────────┐   ┌────────┐   │                     │   │
│  │    │ Select │   │Services│   │                     │   │
│  │    │Entities│   │        │   │                     │   │
│  │    └────────┘   └────────┘   │                     │   │
│  └───────────────────────────────┼─────────────────────┘   │
└────────────────────────────────┼─┼─────────────────────────┘
                                 │ │
                                 │ │ HTTPS
                                 ▼ ▼
                    ┌────────────────────────┐
                    │  Netatmo Energy API    │
                    │                        │
                    │  • Authentication      │
                    │  • Home Status         │
                    │  • Control Commands    │
                    │  • Schedule Management │
                    │  • Energy Measurements │
                    └────────────────────────┘
```

---

## Structure des fichiers

### `__init__.py` - Point d'entrée

**Rôle** : Initialisation de l'intégration et coordinateur de données

```python
class MullerIntuisDataUpdateCoordinator(DataUpdateCoordinator):
    """
    Coordonne les mises à jour depuis l'API.
    Interroge l'API toutes les 5 minutes.
    Fournit les données à toutes les entités.
    """
```

**Fonctions principales** :
- `async_setup_entry()` : Configuration initiale
- `async_unload_entry()` : Déchargement propre
- `_async_update_data()` : Récupération périodique des données
- `async_register_services()` : Enregistrement des services personnalisés

---

### `api.py` - Client API

**Rôle** : Communication avec l'API Netatmo Energy

```python
class MullerIntuisAPI:
    """
    Gère l'authentification OAuth2.
    Effectue les requêtes HTTP vers l'API.
    Rafraîchit automatiquement les tokens.
    """
```

**Méthodes principales** :
- `async_get_access_token()` : Obtention du token
- `async_refresh_token()` : Rafraîchissement du token
- `async_get_homestatus()` : État de la maison
- `async_set_thermpoint()` : Contrôle d'un radiateur
- `async_set_therm_mode()` : Mode global
- `async_sync_schedule()` : Mise à jour d'un planning
- `async_get_room_measure()` : Récupération des mesures

**Gestion des tokens** :
```python
# Les tokens sont stockés dans .storage/muller_intuis_tokens
{
    "access_token": "...",
    "refresh_token": "...",
    "expires_at": 1234567890
}
```

---

### `const.py` - Constantes

**Contenu** :
- URLs de l'API Netatmo
- Modes de chauffage
- Mapping des modes HA ↔ Netatmo
- Limites de température
- Noms des services

**Important** :
```python
# Modes Netatmo
THERM_MODE_SCHEDULE = "schedule"  # Planning automatique
THERM_MODE_AWAY = "away"          # Mode absent
THERM_MODE_HG = "hg"              # Hors-gel
THERM_MODE_MANUAL = "manual"      # Manuel

# Correspondance Home Assistant
MODE_NETATMO_TO_HA = {
    "schedule": "schedule",
    "away": "away",
    "hg": "frost_protection",
    "manual": "manual"
}
```

---

### `config_flow.py` - Configuration UI

**Rôle** : Flow de configuration dans l'interface Home Assistant

```python
class MullerIntuisConfigFlow(config_entries.ConfigFlow):
    """
    Étape 1 : Demande Client ID et Secret
    Étape 2 : Demande Refresh Token et Home ID
    Validation : Test de connexion à l'API
    """
```

**Flow utilisateur** :
1. Saisie Client ID / Client Secret
2. Saisie Refresh Token
3. (Optionnel) Saisie Home ID
4. Validation et création de l'entry

---

### `climate.py` - Entités Climate

**Rôle** : Représentation des radiateurs comme thermostats

```python
class MullerIntuisClimate(CoordinatorEntity, ClimateEntity):
    """
    Une entité par radiateur.
    Supporte les modes HVAC et presets.
    Mise à jour via le coordinateur.
    """
```

**Propriétés principales** :
- `current_temperature` : Température actuelle
- `target_temperature` : Consigne
- `hvac_mode` : Auto, Heat, Off
- `preset_mode` : Schedule, Away, Frost Protection, Manual

**Actions** :
- `async_set_temperature()` : Changer la consigne
- `async_set_hvac_mode()` : Changer le mode HVAC
- `async_set_preset_mode()` : Changer le preset

**Attributs supplémentaires** :
```python
{
    "heating_power_request": 75,  # Pourcentage de chauffe
    "reachable": true,
    "anticipating": false,
    "open_window": false
}
```

---

### `sensor.py` - Capteurs

**Rôle** : Exposition des données sous forme de capteurs

#### Classes de capteurs :

**1. MullerIntuisTemperatureSensor**
- Température mesurée
- Classe : TEMPERATURE
- Unité : °C

**2. MullerIntuisHeatingPowerSensor**
- Puissance de chauffe instantanée
- Classe : POWER
- Unité : W
- Calcul : `heating_power_request * 1000W / 100`

**3. MullerIntuisDailyEnergySensor**
- Consommation journalière
- Classe : ENERGY
- Unité : kWh
- Réinitialisation : Chaque jour à minuit
- Source : API `getroommeasure` avec `type=sum_energy_elec`

**4. MullerIntuisScheduleSensor**
- Un capteur par planning
- État : Actif (true/false)
- Attributs : timetable, zones, away_temp, hg_temp

**5. MullerIntuisActiveScheduleSensor**
- Planning actuellement actif
- État : Nom du planning
- Attributs : Détails du planning actif

---

### `select.py` - Sélecteur de planning

**Rôle** : Permet de changer le planning actif via l'UI

```python
class MullerIntuisScheduleSelect(CoordinatorEntity, SelectEntity):
    """
    Liste déroulante avec tous les plannings.
    Changement : Appelle async_switch_schedule()
    """
```

**Options** : Générées dynamiquement depuis les plannings disponibles

---

### `services.yaml` - Définition des services

**Services disponibles** :

#### 1. `set_schedule`
Change le planning actif
```yaml
service: muller_intuis.set_schedule
data:
  schedule_id: "1234567890"
```

#### 2. `sync_schedule`
Met à jour un planning existant
```yaml
service: muller_intuis.sync_schedule
data:
  schedule_id: "1234567890"
  timetable: [...]
  zones: [...]
```

#### 3. `create_schedule`
Crée un nouveau planning
```yaml
service: muller_intuis.create_schedule
data:
  name: "Mon planning"
  timetable: [...]
  zones: [...]
```

#### 4. `set_room_thermpoint`
Contrôle une pièce spécifique
```yaml
service: muller_intuis.set_room_thermpoint
data:
  room_id: "1234567890"
  mode: "manual"
  temp: 21.5
```

#### 5. `set_home_mode`
Mode global de la maison
```yaml
service: muller_intuis.set_home_mode
data:
  mode: "away"
```

---

## Format des données API

### Réponse `homestatus`

```json
{
  "body": {
    "home": {
      "id": "1234567890",
      "name": "Ma maison",
      "rooms": [
        {
          "id": "9876543210",
          "name": "Salon",
          "type": "livingroom",
          "therm_measured_temperature": 20.5,
          "therm_setpoint_temperature": 21.0,
          "therm_setpoint_mode": "schedule",
          "heating_power_request": 75,
          "reachable": true,
          "anticipating": false
        }
      ],
      "schedules": [
        {
          "id": "schedule_123",
          "name": "Planning semaine",
          "selected": true,
          "type": "therm",
          "timetable": [
            {
              "zone_id": 0,
              "m_offset": 0
            },
            {
              "zone_id": 1,
              "m_offset": 420
            }
          ],
          "zones": [
            {
              "id": 0,
              "name": "Confort",
              "rooms_temp": [
                {
                  "room_id": "9876543210",
                  "temp": 20.5
                }
              ]
            }
          ],
          "away_temp": 12,
          "hg_temp": 7
        }
      ]
    }
  }
}
```

### Données du coordinateur

```python
{
    "home_status": {
        # Réponse complète de homestatus
    },
    "schedules": {
        "schedule_123": {
            "id": "schedule_123",
            "name": "Planning semaine",
            "selected": true,
            # ...
        }
    },
    "rooms": [
        {
            "id": "9876543210",
            "name": "Salon",
            # ...
        }
    ]
}
```

---

## Gestion des plannings

### Format timetable

```python
timetable = [
    {"zone_id": 0, "m_offset": 0},       # Lundi 00:00
    {"zone_id": 1, "m_offset": 420},     # Lundi 07:00
    {"zone_id": 0, "m_offset": 1320},    # Lundi 22:00
    # ...
]
```

- `m_offset` : Minutes depuis le début de la semaine (Lundi 00:00)
- `zone_id` : Identifiant de la zone à appliquer

### Format zones

```python
zones = [
    {
        "id": 0,
        "name": "Confort",
        "rooms_temp": [
            {"room_id": "9876543210", "temp": 20.5},
            {"room_id": "1111111111", "temp": 19.0}
        ]
    },
    {
        "id": 1,
        "name": "Éco",
        "rooms_temp": [
            {"room_id": "9876543210", "temp": 18.0},
            {"room_id": "1111111111", "temp": 17.0}
        ]
    }
]
```

---

## Interface HTML - muller_planning.html

### Fonctionnement

1. **Récupération de hass** : Accès à l'objet Home Assistant
   ```javascript
   function getHass() {
     if(window.parent && window.parent.document)
       return window.parent.document.querySelector('home-assistant').hass;
     return window.hass || null;
   }
   ```

2. **Chargement des plannings** : Depuis les capteurs HA
   ```javascript
   const scheduleEntities = Object.entries(hass.states)
     .filter(([id,e]) => id.startsWith('sensor.muller_intuis_schedule_'));
   ```

3. **Affichage visuel** : Barre de planning par jour
   - Segments colorés par zone
   - Cliquable pour édition
   - Bouton "+" pour ajouter un créneau

4. **Édition** : Modal dialog
   - Heure de début / fin
   - Jour de début / fin (pour créneaux multi-jours)
   - Zone à appliquer

5. **Sauvegarde** : Appel du service HA
   ```javascript
   await hass.callService('muller_intuis', 'sync_schedule', {
     schedule_id: current.schedule_id,
     timetable: current.timetable,
     zones: current.zones
   });
   ```

### Algorithme de normalisation

```javascript
function normalize() {
  // 1. Trier par offset
  // 2. Pour chaque jour :
  //    - Compléter le début si vide
  //    - Compléter la fin si vide
  // 3. Fusionner les segments identiques consécutifs
}
```

---

## Tests et validation

### Tester l'API directement

```python
import aiohttp
import asyncio

async def test():
    session = aiohttp.ClientSession()
    api = MullerIntuisAPI(
        "YOUR_CLIENT_ID",
        "YOUR_CLIENT_SECRET",
        session,
        None,  # hass
        "YOUR_HOME_ID"
    )
    
    # Charger les tokens
    await api.async_load_tokens()
    
    # Obtenir le statut
    status = await api.async_get_homestatus()
    print(status)
    
    await session.close()

asyncio.run(test())
```

### Logs de débogage

```yaml
logger:
  logs:
    custom_components.muller_intuis: debug
    custom_components.muller_intuis.api: debug
```

---

## Bonnes pratiques

### Gestion des erreurs

```python
try:
    await api.async_set_thermpoint(room_id, mode, temp)
except Exception as err:
    _LOGGER.error("Erreur lors du changement de température: %s", err)
    raise HomeAssistantError(f"Impossible de changer la température: {err}")
```

### Rate limiting

L'API Netatmo a des limites :
- 500 requêtes / heure / utilisateur
- Le coordinateur interroge toutes les 5 minutes
- Les actions utilisateur ne comptent pas dans ce quota

### Optimisations

1. **Cache** : Le coordinateur met en cache les données
2. **Batching** : Grouper les actions si possible
3. **Refresh conditionnel** : Ne rafraîchir que si nécessaire

---

## Extension de l'intégration

### Ajouter un nouveau capteur

1. **Créer la classe** dans `sensor.py` :
```python
class MullerIntuisNewSensor(MullerIntuisBaseSensor):
    _attr_name = "Mon nouveau capteur"
    
    @property
    def native_value(self):
        return self.room_data.get("nouvelle_valeur")
```

2. **L'ajouter** dans `async_setup_entry()` :
```python
entities.append(MullerIntuisNewSensor(coordinator, room_id, room_name))
```

### Ajouter un nouveau service

1. **Définir** dans `services.yaml`
2. **Implémenter** dans `__init__.py` :
```python
async def handle_new_service(call: ServiceCall):
    # Votre logique
    pass

hass.services.async_register(
    DOMAIN, "new_service", handle_new_service, schema=...
)
```

---

## Contribution

### Workflow de développement

1. Fork le repository
2. Créer une branche : `git checkout -b feature/ma-fonctionnalite`
3. Développer et tester
4. Commit : `git commit -m "feat: ma nouvelle fonctionnalité"`
5. Push : `git push origin feature/ma-fonctionnalite`
6. Créer une Pull Request

### Standards de code

- PEP 8 pour Python
- Type hints obligatoires
- Docstrings pour les fonctions publiques
- Tests pour les nouvelles fonctionnalités

---

## Ressources

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [Netatmo API Documentation](https://dev.netatmo.com/apidocumentation/energy)
- [Python aiohttp](https://docs.aiohttp.org/)
- [Home Assistant Config Flow](https://developers.home-assistant.io/docs/config_entries_config_flow_handler)

---

*Guide de développement - Muller Intuis Connect v1.0*
