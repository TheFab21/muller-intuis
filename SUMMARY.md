# Intégration Muller Intuis Connect pour Home Assistant
## Document récapitulatif

---

## 📋 Vue d'ensemble

Cette intégration Home Assistant complète vous permet de contrôler entièrement vos radiateurs Muller Intuis Connect, basés sur l'API Netatmo Energy. Elle remplace votre flow Node-RED actuel avec une solution native, plus performante et mieux intégrée.

---

## ✨ Fonctionnalités principales

### 🎛️ Contrôle des radiateurs
- ✅ Entité `climate` pour chaque radiateur
- ✅ Contrôle de la température (7-30°C par pas de 0.5°C)
- ✅ Modes : Auto, Heat, Off
- ✅ Presets : Schedule, Away, Frost Protection, Manual
- ✅ État en temps réel (température, puissance de chauffe)

### 📊 Capteurs
- ✅ Température actuelle de chaque pièce
- ✅ Puissance de chauffe instantanée (en Watts)
- ✅ Consommation énergétique journalière (en kWh)
- ✅ Capteur du planning actif
- ✅ Capteur pour chaque planning avec attributs complets

### 📅 Gestion des plannings
- ✅ Sélecteur de planning (`select` entity)
- ✅ Interface web graphique pour éditer les plannings
- ✅ Création, modification, suppression de plannings
- ✅ Gestion des zones et températures
- ✅ Planning hebdomadaire avec créneaux horaires visuels

### 🔧 Services Home Assistant
- ✅ `set_schedule` : Changer le planning actif
- ✅ `sync_schedule` : Mettre à jour un planning
- ✅ `create_schedule` : Créer un nouveau planning
- ✅ `delete_schedule` : Supprimer un planning
- ✅ `rename_schedule` : Renommer un planning
- ✅ `set_room_thermpoint` : Contrôler une pièce
- ✅ `set_home_mode` : Mode global de la maison

---

## 📦 Contenu du package

```
muller_intuis/
├── __init__.py              # Initialisation et coordinateur
├── api.py                   # Client API Netatmo
├── climate.py               # Entités climate
├── config_flow.py           # Configuration via UI
├── const.py                 # Constantes
├── manifest.json            # Métadonnées de l'intégration
├── select.py                # Sélecteur de planning
├── sensor.py                # Capteurs
├── services.yaml            # Définition des services
├── strings.json             # Traductions (EN)
├── hacs.json                # Configuration HACS
├── translations/
│   └── fr.json              # Traductions françaises
├── www/
│   └── muller_planning.html # Interface de gestion des plannings
├── README.md                # Documentation principale
├── INSTALL.md               # Guide d'installation détaillé
├── AUTOMATIONS.md           # Exemples d'automatisations
└── lovelace_examples.md     # Exemples de cartes Lovelace
```

---

## 🚀 Installation rapide

### 1. Copier l'intégration
```bash
cp -r muller_intuis /config/custom_components/
```

### 2. Obtenir les identifiants API
1. Créer une app sur https://dev.netatmo.com/
2. Noter le `Client ID` et `Client Secret`
3. Obtenir un `refresh_token` via le flow OAuth

### 3. Configurer dans Home Assistant
1. Configuration → Intégrations → + Ajouter
2. Rechercher "Muller Intuis Connect"
3. Entrer vos identifiants
4. ✅ Terminé !

### 4. Installer l'interface de plannings
```bash
cp muller_intuis/www/muller_planning.html /config/www/
```

Puis ajouter dans Lovelace :
```yaml
type: iframe
url: /local/muller_planning.html
aspect_ratio: 75%
```

---

## 🔄 Migration depuis Node-RED

### Correspondance des fonctionnalités

| Node-RED (via MQTT) | Home Assistant |
|---------------------|----------------|
| Topic `stat/homestatus` | Capteurs `sensor.muller_intuis_*` |
| Topic `cmnd/set_therm_mode` | Service `muller_intuis.set_home_mode` |
| Topic `plannings/[id]/set` | Service `muller_intuis.sync_schedule` |
| Page HTML Node-RED | `/local/muller_planning.html` |
| Récupération stats conso | Capteurs `*_daily_energy` |

### Avantages de la migration

✅ **Plus de MQTT nécessaire** : Communication directe avec l'API
✅ **Meilleure intégration** : Entités natives Home Assistant
✅ **Interface unifiée** : Tout dans Home Assistant
✅ **Automatisations simplifiées** : Services natifs HA
✅ **Maintenance facilitée** : Mises à jour via HACS
✅ **Performance améliorée** : Moins de latence

---

## 📱 Exemples d'utilisation

### Dashboard de contrôle
```yaml
type: vertical-stack
cards:
  - type: entities
    title: Chauffage
    entities:
      - select.muller_intuis_active_schedule
      - sensor.muller_intuis_active_schedule

  - type: horizontal-stack
    cards:
      - type: button
        name: Auto
        tap_action:
          action: call-service
          service: muller_intuis.set_home_mode
          data:
            mode: schedule
      - type: button
        name: Absent
        tap_action:
          action: call-service
          service: muller_intuis.set_home_mode
          data:
            mode: away

  - type: entities
    entities:
      - climate.muller_intuis_salon
      - climate.muller_intuis_cuisine
      - climate.muller_intuis_chambre_parents
```

### Automatisation : Mode absent
```yaml
automation:
  - alias: "Chauffage mode absent auto"
    trigger:
      - platform: state
        entity_id: person.vous
        to: "not_home"
        for:
          hours: 2
    action:
      - service: muller_intuis.set_home_mode
        data:
          mode: away
```

### Script : Boost confort
```yaml
script:
  chauffage_boost:
    sequence:
      - service: climate.set_temperature
        target:
          entity_id: climate.muller_intuis_salon
        data:
          temperature: 22
```

---

## 🎯 Comparaison avec votre flow Node-RED

### Votre flow actuel
- ✅ Connexion API Netatmo
- ✅ Récupération homestatus
- ✅ Pilotage radiateurs
- ✅ Gestion plannings via HTML
- ✅ Statistiques de consommation
- ⚠️ Utilise MQTT pour payloads lourds
- ⚠️ Séparé de Home Assistant
- ⚠️ Configuration manuelle

### L'intégration Home Assistant
- ✅ Toutes les fonctionnalités de Node-RED
- ✅ Intégration native Home Assistant
- ✅ Pas de MQTT nécessaire
- ✅ Configuration via UI
- ✅ Entités automatiques
- ✅ Services natifs
- ✅ Automatisations simplifiées
- ✅ Interface web incluse
- ✅ Compatible HACS

---

## 🔧 Personnalisation

### Modifier l'intervalle de mise à jour
Dans `const.py` :
```python
SCAN_INTERVAL = timedelta(minutes=5)  # Par défaut
```

### Ajouter un nouveau capteur
Dans `sensor.py`, créer une nouvelle classe héritant de `MullerIntuisBaseSensor`.

### Personnaliser l'interface HTML
Éditer `/config/www/muller_planning.html` selon vos besoins.

---

## 📚 Documentation complète

Consultez les fichiers suivants pour plus de détails :

1. **README.md** : Documentation générale
2. **INSTALL.md** : Guide d'installation pas à pas
3. **AUTOMATIONS.md** : Exemples d'automatisations
4. **lovelace_examples.md** : Exemples de cartes UI

---

## 🆘 Support

### En cas de problème

1. **Vérifier les logs**
   - Configuration → Système → Journaux
   - Filtrer par "muller_intuis"

2. **Activer le mode debug**
   ```yaml
   logger:
     logs:
       custom_components.muller_intuis: debug
   ```

3. **Problèmes courants**
   - Token expiré → Régénérer le refresh_token
   - Connexion échouée → Vérifier Client ID/Secret
   - Entités manquantes → Recharger l'intégration

### Obtenir de l'aide
- GitHub Issues : [Votre repo]
- Forum Home Assistant
- Discord Home Assistant FR

---

## 🎁 Bonus

### Templates utiles

**Consommation totale** :
```yaml
template:
  - sensor:
      - name: "Consommation totale chauffage"
        unit_of_measurement: "kWh"
        state: >
          {{ states('sensor.muller_intuis_salon_daily_energy') | float(0) +
             states('sensor.muller_intuis_cuisine_daily_energy') | float(0) +
             states('sensor.muller_intuis_chambre_parents_daily_energy') | float(0) }}
```

**Température moyenne** :
```yaml
template:
  - sensor:
      - name: "Température moyenne maison"
        unit_of_measurement: "°C"
        state: >
          {{ [
            states('sensor.muller_intuis_salon_temperature') | float(0),
            states('sensor.muller_intuis_cuisine_temperature') | float(0)
          ] | average | round(1) }}
```

---

## ✅ Checklist post-installation

- [ ] L'intégration est configurée et fonctionnelle
- [ ] Toutes les entités apparaissent correctement
- [ ] Les radiateurs répondent aux commandes
- [ ] L'interface HTML de plannings fonctionne
- [ ] Les capteurs de consommation remontent les données
- [ ] Le sélecteur de planning change bien le planning actif
- [ ] Au moins une automatisation est créée et testée
- [ ] Les logs ne montrent pas d'erreurs

---

## 🚀 Prochaines étapes

1. **Créer vos automatisations** : Inspirez-vous de `AUTOMATIONS.md`
2. **Personnaliser votre dashboard** : Utilisez `lovelace_examples.md`
3. **Optimiser vos plannings** : Via l'interface web
4. **Surveiller votre consommation** : Créer des graphiques
5. **Désactiver Node-RED** : Une fois tout validé

---

## 📝 Notes importantes

- Les tokens sont rafraîchis automatiquement
- Les données sont mises à jour toutes les 5 minutes
- L'API Netatmo a des limites de requêtes (surveillez les logs)
- Les plannings sont synchronisés avec le cloud Netatmo
- L'interface HTML nécessite JavaScript activé

---

## 🎉 Félicitations !

Vous disposez maintenant d'une intégration complète et professionnelle pour vos radiateurs Muller Intuis Connect dans Home Assistant !

**Profitez de votre maison intelligente ! 🏠🔥**

---

*Créé le 4 novembre 2025*
*Version 1.0.0*
