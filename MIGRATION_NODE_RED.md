# Migration de Node-RED vers Home Assistant

Ce guide vous aide à migrer votre installation Muller Intuitiv de Node-RED vers l'intégration Home Assistant.

## 🔄 Vue d'ensemble de la migration

Votre flux Node-RED actuel gère :
- ✅ L'authentification OAuth2 avec Netatmo
- ✅ Le rafraîchissement automatique des tokens
- ✅ Les appels API vers Muller Intuitiv

L'intégration Home Assistant fait **exactement la même chose** en arrière-plan, mais de manière plus simple et intégrée.

## 📋 Informations à récupérer de Node-RED

Dans votre flux Node-RED, vous avez configuré (dans les variables d'environnement) :

```javascript
{
   "client_id": $env("ClientId"),          // ← À récupérer
   "client_secret": $env("ClientSecret"),  // ← À récupérer
   "username": $env("username"),           // ← À récupérer
   "password": $env("password"),           // ← À récupérer
   "user_prefix": "muller",                // ← Géré automatiquement
   "grant_type": "password",               // ← Géré automatiquement
   "scope": "read_muller write_muller"     // ← Géré automatiquement
}
```

### Comment récupérer ces valeurs dans Node-RED

1. **Ouvrez Node-RED**
2. **Allez dans le menu** (☰) → **Settings** → **Environment Variables**
3. **Notez les valeurs de** :
   - `ClientId`
   - `ClientSecret`
   - `username` (votre email)
   - `password`

**Alternative** : Ces valeurs sont les mêmes que celles que vous avez obtenues sur [dev.netatmo.com](https://dev.netatmo.com)

## 🔧 Équivalence des fonctionnalités

| Fonctionnalité Node-RED | Équivalent Home Assistant |
|-------------------------|---------------------------|
| Flux d'authentification | Automatique (dans `config_flow.py`) |
| Rafraîchissement token | Automatique (dans `__init__.py`) |
| `msg.AccessToken` | Géré en interne par l'intégration |
| `msg.RefreshToken` | Géré en interne par l'intégration |
| Appels API toutes les 5 min | `DataUpdateCoordinator` (5 min) |
| Status des radiateurs | Entités `climate.*` et `sensor.*` |
| Changement de température | Service `climate.set_temperature` |
| Changement de mode | Service `climate.set_hvac_mode` |

## 🚀 Étapes de migration

### Étape 1 : Préparer les identifiants

Récupérez de Node-RED :
- ✅ Client ID
- ✅ Client Secret
- ✅ Username (email)
- ✅ Password

### Étape 2 : Installer l'intégration Home Assistant

Suivez le [README.md](README.md) principal pour installer l'intégration.

### Étape 3 : Tester en parallèle

**Important** : Vous pouvez faire fonctionner Node-RED et Home Assistant **en même temps**.
Les deux systèmes utilisent la même API et peuvent coexister.

1. **Installez et configurez** l'intégration Home Assistant
2. **Gardez Node-RED actif** pendant quelques jours
3. **Comparez** les comportements
4. **Migrez progressivement** vos automatisations

### Étape 4 : Migrer les automatisations

Exemple de migration d'un flow Node-RED :

#### Node-RED (ancien)

```javascript
// Inject node à 07:00
// → Change node
// → HTTP Request pour changer le planning
```

#### Home Assistant (nouveau)

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
```

### Étape 5 : Désactiver Node-RED

Une fois que tout fonctionne bien dans Home Assistant :

1. **Désactivez** le flux Node-RED (bouton "Stop" dans votre flux)
2. **Surveillez** pendant quelques jours
3. **Supprimez** le flux Node-RED si tout va bien

## 🔍 Comparaison détaillée

### Authentification

#### Node-RED
```javascript
// Node "Set param request refresh"
msg.payload = {
   "client_id": $env("ClientId"),
   "user_prefix": "muller",
   "client_secret": $env("ClientSecret"),
   "grant_type": "password",
   "scope": "read_muller write_muller",
   "password": $env("password"),
   "username": $env("username")
}

// HTTP Request vers https://app.muller-intuitiv.net/oauth2/token
```

#### Home Assistant
```python
# Tout est géré automatiquement dans __init__.py
await api_client._refresh_token()
# Les tokens sont rafraîchis automatiquement 5 min avant expiration
```

### Récupération des données

#### Node-RED
```javascript
// HTTP Request toutes les 5 minutes
// avec AccessToken dans le header
```

#### Home Assistant
```python
# DataUpdateCoordinator fait la même chose automatiquement
coordinator = MullerIntuisDataUpdateCoordinator(hass, api_client)
# Update toutes les 5 minutes
```

## 📊 Avantages de la migration

### Node-RED
- ✅ Flexible et personnalisable
- ✅ Vous gardez le contrôle total
- ❌ Maintenance manuelle
- ❌ Gestion des erreurs à implémenter
- ❌ Pas d'intégration native avec HA

### Home Assistant Integration
- ✅ Intégration native dans HA
- ✅ Gestion automatique des tokens
- ✅ Gestion automatique des erreurs
- ✅ Entités climate/sensor/select prêtes à l'emploi
- ✅ Mise à jour automatique
- ✅ Compatible avec toutes les fonctionnalités HA
- ❌ Moins flexible que Node-RED

## 🆘 Dépannage de la migration

### Les deux systèmes interfèrent-ils ?

**Non**, Node-RED et Home Assistant peuvent fonctionner ensemble sans problème.
Ils utilisent tous les deux l'API Muller Intuitiv qui gère plusieurs connexions simultanées.

### Mes automatisations Node-RED complexes

Si vous avez des automatisations très complexes dans Node-RED :

1. **Gardez Node-RED** pour les automatisations complexes
2. **Utilisez Home Assistant** pour le contrôle basique des radiateurs
3. **Connectez les deux** via MQTT si besoin

### Les tokens expirent

L'intégration Home Assistant rafraîchit automatiquement les tokens **5 minutes avant expiration**.
Si vous voyez des erreurs d'authentification :

1. Vérifiez les logs Home Assistant
2. Reconfigurez l'intégration avec les bons identifiants

## 📝 Checklist de migration

- [ ] Récupérer Client ID et Client Secret de Node-RED ou dev.netatmo.com
- [ ] Récupérer username et password
- [ ] Installer l'intégration Home Assistant
- [ ] Configurer l'intégration avec les 4 identifiants
- [ ] Vérifier que les entités apparaissent dans HA
- [ ] Tester le contrôle des radiateurs via HA
- [ ] Migrer les automatisations progressivement
- [ ] Désactiver temporairement Node-RED pour tester
- [ ] Si tout fonctionne, supprimer le flux Node-RED

## 🔗 Ressources

- [README principal](README.md) - Installation et configuration
- [dev.netatmo.com](https://dev.netatmo.com) - Portail développeur Netatmo
- [GitHub du projet](https://github.com/TheFab21/muller-intuis) - Code source

## 💬 Besoin d'aide ?

Si vous rencontrez des problèmes lors de la migration :

1. Consultez les logs Home Assistant (Paramètres → Système → Journaux)
2. Ouvrez une issue sur GitHub
3. Gardez Node-RED actif en backup le temps de résoudre le problème
