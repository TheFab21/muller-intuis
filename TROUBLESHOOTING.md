# Guide de dépannage - Muller Intuis Connect

## Table des matières
1. [Problèmes d'installation](#problèmes-dinstallation)
2. [Problèmes d'authentification](#problèmes-dauthentification)
3. [Problèmes de connexion](#problèmes-de-connexion)
4. [Problèmes de mise à jour](#problèmes-de-mise-à-jour)
5. [Problèmes de contrôle](#problèmes-de-contrôle)
6. [Problèmes de plannings](#problèmes-de-plannings)
7. [Problèmes d'interface HTML](#problèmes-dinterface-html)
8. [Diagnostic avancé](#diagnostic-avancé)

---

## Problèmes d'installation

### L'intégration n'apparaît pas dans la liste

**Symptômes** :
- L'intégration n'est pas visible dans Configuration → Intégrations

**Solutions** :

1. **Vérifier l'emplacement des fichiers**
   ```bash
   ls -la /config/custom_components/muller_intuis/
   ```
   Vous devriez voir : `__init__.py`, `manifest.json`, etc.

2. **Vérifier les permissions**
   ```bash
   chmod -R 755 /config/custom_components/muller_intuis/
   ```

3. **Vérifier le fichier manifest.json**
   ```bash
   cat /config/custom_components/muller_intuis/manifest.json
   ```
   Doit être un JSON valide

4. **Redémarrer Home Assistant**
   - Configuration → Système → Redémarrer

5. **Vider le cache du navigateur**
   - Ctrl + F5 (ou Cmd + Shift + R sur Mac)

6. **Vérifier les logs**
   ```
   Configuration → Système → Journaux
   ```
   Rechercher "muller_intuis"

---

### Erreur lors du chargement de l'intégration

**Symptômes** :
```
Setup failed for muller_intuis: Unable to import component
```

**Solutions** :

1. **Vérifier la syntaxe Python**
   ```bash
   python3 -m py_compile /config/custom_components/muller_intuis/*.py
   ```

2. **Vérifier les dépendances**
   Dans `manifest.json`, vérifier :
   ```json
   "requirements": ["aiohttp>=3.8.0"]
   ```

3. **Réinstaller l'intégration**
   ```bash
   rm -rf /config/custom_components/muller_intuis/
   # Puis réinstaller
   ```

4. **Vérifier la version de Home Assistant**
   - Minimum requis : 2023.1.0
   - Votre version : Configuration → À propos

---

## Problèmes d'authentification

### Erreur "invalid_auth"

**Symptômes** :
- Configuration échoue avec "Authentification invalide"

**Causes possibles** :

1. **Refresh token expiré**
   - Les refresh tokens peuvent expirer après 6 mois d'inactivité

**Solution** :
```
1. Aller sur https://dev.netatmo.com/apidocumentation/oauth
2. Cliquer sur "GET TOKEN"
3. Cocher : read_thermostat, write_thermostat
4. Copier le NOUVEAU refresh_token
5. Reconfigurer l'intégration dans HA
```

2. **Client ID / Secret incorrects**

**Vérification** :
```bash
# Logs avec mode debug
tail -f /config/home-assistant.log | grep "muller_intuis"
```

**Solution** :
- Vérifier sur https://dev.netatmo.com/apps
- Copier-coller soigneusement (pas d'espaces)

3. **Application Netatmo désactivée**

**Solution** :
- Vérifier que votre app est "Active" sur dev.netatmo.com
- Si nécessaire, recréer une nouvelle application

---

### Token se rafraîchit constamment

**Symptômes** :
- Logs montrent des rafraîchissements toutes les 5 minutes
- Erreur "Token expired"

**Cause** :
- Le stockage des tokens échoue

**Solution** :

1. **Vérifier les permissions du dossier .storage**
   ```bash
   ls -la /config/.storage/
   chmod 755 /config/.storage/
   ```

2. **Vérifier le fichier de stockage**
   ```bash
   cat /config/.storage/muller_intuis_tokens
   ```

3. **Supprimer et recréer**
   ```bash
   rm /config/.storage/muller_intuis_tokens
   # Reconfigurer l'intégration
   ```

---

## Problèmes de connexion

### Erreur "cannot_connect"

**Symptômes** :
- Impossible de se connecter à l'API

**Solutions** :

1. **Vérifier la connexion Internet**
   ```bash
   ping api.netatmo.com
   ```

2. **Vérifier les DNS**
   ```bash
   nslookup api.netatmo.com
   ```

3. **Vérifier le pare-feu**
   - Port 443 (HTTPS) doit être ouvert sortant

4. **Tester manuellement l'API**
   ```bash
   curl https://api.netatmo.com/api/homestatus \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

5. **Vérifier les proxies**
   - Si vous utilisez un proxy, configurez-le dans HA

---

### Time-out lors des requêtes

**Symptômes** :
```
TimeoutError: Request timed out
```

**Solutions** :

1. **Augmenter le timeout** dans `api.py` :
   ```python
   timeout = aiohttp.ClientTimeout(total=30)
   async with self.session.request(..., timeout=timeout) as response:
   ```

2. **Vérifier la charge de l'API Netatmo**
   - L'API peut être temporairement lente
   - Réessayer plus tard

3. **Vérifier la bande passante**
   - Connexion Internet stable requise

---

## Problèmes de mise à jour

### Les données ne se mettent pas à jour

**Symptômes** :
- Entités "stale" ou "unavailable"
- Données figées

**Solutions** :

1. **Vérifier l'intervalle de mise à jour**
   Dans `const.py` :
   ```python
   SCAN_INTERVAL = timedelta(minutes=5)
   ```

2. **Forcer une mise à jour**
   ```yaml
   service: homeassistant.update_entity
   target:
     entity_id: climate.muller_intuis_salon
   ```

3. **Vérifier les logs d'erreur**
   ```
   Configuration → Système → Journaux
   Filtrer : muller_intuis
   ```

4. **Recharger l'intégration**
   ```
   Configuration → Intégrations → Muller Intuis → ⋮ → Recharger
   ```

---

### Limite de requêtes API atteinte

**Symptômes** :
```
HTTP 429 - Too Many Requests
```

**Cause** :
- API Netatmo : 500 requêtes/heure maximum

**Solutions** :

1. **Augmenter l'intervalle**
   Modifier `SCAN_INTERVAL` dans `const.py` :
   ```python
   SCAN_INTERVAL = timedelta(minutes=10)  # Au lieu de 5
   ```

2. **Identifier les automatisations gourmandes**
   - Vérifier vos automatisations
   - Ne pas interroger trop souvent

3. **Attendre la réinitialisation**
   - Limite réinitialisée toutes les heures

---

## Problèmes de contrôle

### La température ne change pas

**Symptômes** :
- Commande envoyée mais température inchangée

**Diagnostic** :

1. **Vérifier la connectivité du radiateur**
   - Attribut `reachable` doit être `true`
   ```yaml
   {{ state_attr('climate.muller_intuis_salon', 'reachable') }}
   ```

2. **Vérifier le mode**
   - En mode "schedule", la température suit le planning
   - Passer en mode "manual" :
   ```yaml
   service: climate.set_preset_mode
   target:
     entity_id: climate.muller_intuis_salon
   data:
     preset_mode: manual
   ```

3. **Vérifier dans les logs**
   ```
   Rechercher : "set_thermpoint"
   ```

4. **Tester directement sur l'app Netatmo**
   - Si ça fonctionne → Problème d'intégration
   - Si ça ne fonctionne pas → Problème matériel

---

### Le mode ne change pas

**Symptômes** :
- Mode HVAC ou preset ne change pas

**Solutions** :

1. **Vérifier les logs d'API**
   ```
   grep "set_therm_mode" /config/home-assistant.log
   ```

2. **Tester le service directement**
   ```yaml
   service: muller_intuis.set_home_mode
   data:
     mode: away
   ```

3. **Vérifier la réponse de l'API**
   Activer le mode debug :
   ```yaml
   logger:
     logs:
       custom_components.muller_intuis.api: debug
   ```

---

## Problèmes de plannings

### Le planning ne se synchronise pas

**Symptômes** :
- Modifications non enregistrées
- Erreur lors de la sauvegarde

**Solutions** :

1. **Vérifier le format des données**
   - `timetable` doit être une liste
   - `zones` doit être une liste
   - `m_offset` doit être un entier

2. **Vérifier les room_id**
   ```yaml
   # Les room_id doivent exister
   service: muller_intuis.sync_schedule
   data:
     schedule_id: "123"
     zones:
       - id: 0
         name: "Confort"
         rooms_temp:
           - room_id: "VERIFIER_CET_ID"  # ← Doit être valide
             temp: 20
   ```

3. **Tester avec un planning simple**
   ```yaml
   service: muller_intuis.sync_schedule
   data:
     schedule_id: "votre_id"
     timetable:
       - m_offset: 0
         zone_id: 0
     zones:
       - id: 0
         name: "Test"
         rooms_temp:
           - room_id: "room_id_valide"
             temp: 20
   ```

---

### Le sélecteur de planning ne fonctionne pas

**Symptômes** :
- `select.muller_intuis_active_schedule` non disponible
- Changement ne fait rien

**Solutions** :

1. **Vérifier que l'entité existe**
   ```
   Configuration → Entités → Rechercher "muller_intuis_active_schedule"
   ```

2. **Vérifier les plannings disponibles**
   ```yaml
   {{ state_attr('select.muller_intuis_active_schedule', 'options') }}
   ```

3. **Forcer une mise à jour**
   ```yaml
   service: homeassistant.update_entity
   target:
     entity_id: sensor.muller_intuis_active_schedule
   ```

---

## Problèmes d'interface HTML

### La page ne charge pas

**Symptômes** :
- Page blanche
- "ERR_FILE_NOT_FOUND"

**Solutions** :

1. **Vérifier l'emplacement du fichier**
   ```bash
   ls -la /config/www/muller_planning.html
   ```

2. **Vérifier les permissions**
   ```bash
   chmod 644 /config/www/muller_planning.html
   ```

3. **Vérifier l'URL dans la carte**
   ```yaml
   type: iframe
   url: /local/muller_planning.html  # ← Doit être exactement ça
   ```

4. **Vider le cache**
   - Ctrl + F5
   - Ou mode navigation privée

---

### Les plannings ne s'affichent pas

**Symptômes** :
- Liste déroulante vide
- Message d'erreur dans la console

**Solutions** :

1. **Ouvrir la console JavaScript**
   - F12 → Console
   - Rechercher les erreurs

2. **Vérifier l'accès à hass**
   ```javascript
   // Dans la console
   window.parent.document.querySelector('home-assistant').hass
   ```

3. **Vérifier les capteurs**
   ```javascript
   // Dans la console
   Object.keys(window.parent.document.querySelector('home-assistant').hass.states)
     .filter(id => id.startsWith('sensor.muller_intuis_schedule_'))
   ```

4. **Recréer les capteurs**
   - Recharger l'intégration
   - Attendre 5 minutes

---

### Impossible de sauvegarder

**Symptômes** :
- Bouton "Enregistrer" ne fait rien
- Erreur dans les logs

**Solutions** :

1. **Vérifier dans la console**
   - F12 → Console
   - Chercher les erreurs JavaScript

2. **Vérifier le service**
   ```yaml
   # Tester dans Outils de développement
   service: muller_intuis.sync_schedule
   data:
     schedule_id: "test"
     timetable: []
     zones: []
   ```

3. **Vérifier les permissions**
   - L'utilisateur doit pouvoir appeler des services

4. **Version du navigateur**
   - Chrome/Firefox/Safari récent requis

---

## Diagnostic avancé

### Activer le mode debug complet

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.muller_intuis: debug
    custom_components.muller_intuis.api: debug
    custom_components.muller_intuis.climate: debug
    custom_components.muller_intuis.sensor: debug
    custom_components.muller_intuis.select: debug
```

Redémarrer HA, puis consulter :
```bash
tail -f /config/home-assistant.log | grep muller_intuis
```

---

### Tester l'API manuellement

**Script de test** :

```python
# test_api.py
import asyncio
import aiohttp
import json

async def test():
    CLIENT_ID = "VOTRE_CLIENT_ID"
    CLIENT_SECRET = "VOTRE_CLIENT_SECRET"
    REFRESH_TOKEN = "VOTRE_REFRESH_TOKEN"
    
    async with aiohttp.ClientSession() as session:
        # 1. Obtenir un access token
        data = {
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }
        
        async with session.post("https://api.netatmo.com/oauth2/token", data=data) as resp:
            result = await resp.json()
            access_token = result["access_token"]
            print(f"Access token: {access_token[:20]}...")
        
        # 2. Tester homestatus
        headers = {"Authorization": f"Bearer {access_token}"}
        async with session.post("https://api.netatmo.com/api/homestatus", headers=headers) as resp:
            status = await resp.json()
            print(json.dumps(status, indent=2))

asyncio.run(test())
```

Exécuter :
```bash
python3 test_api.py
```

---

### Recréer complètement l'intégration

**Étapes** :

1. **Supprimer l'intégration**
   ```
   Configuration → Intégrations → Muller Intuis → ⋮ → Supprimer
   ```

2. **Supprimer les fichiers de stockage**
   ```bash
   rm /config/.storage/muller_intuis_tokens
   rm /config/.storage/core.config_entries  # Sauvegardez d'abord !
   ```

3. **Redémarrer Home Assistant**

4. **Réinstaller l'intégration**
   - Suivre le guide d'installation

---

### Collecter des informations pour un rapport de bug

**Informations à fournir** :

1. **Version de Home Assistant**
   ```
   Configuration → À propos → Version
   ```

2. **Version de l'intégration**
   ```bash
   cat /config/custom_components/muller_intuis/manifest.json | grep version
   ```

3. **Logs pertinents**
   ```bash
   grep "muller_intuis" /config/home-assistant.log > debug.log
   ```

4. **Configuration sanitisée**
   ```yaml
   # Supprimer les tokens/secrets avant de partager
   ```

5. **Étapes pour reproduire**
   - Décrire précisément les actions effectuées

---

## Cas particuliers

### Migration depuis Node-RED

**Problème** : Les room_id ne correspondent pas

**Solution** :
1. Dans Node-RED, noter vos room_id
2. Dans HA, vérifier les attributs des entités climate
3. Mapper manuellement si nécessaire

---

### Plusieurs maisons Netatmo

**Problème** : Mauvaise maison sélectionnée

**Solution** :
1. Consulter les logs au premier lancement
2. Récupérer le home_id correct
3. Reconfigurer avec le bon home_id

---

### Radiateurs offline

**Problème** : Certains radiateurs "unavailable"

**Causes** :
- Piles faibles
- Signal WiFi faible
- Radiateur éteint

**Solutions** :
1. Vérifier l'app Netatmo
2. Changer les piles
3. Rapprocher du WiFi
4. Redémarrer le radiateur

---

## Support communautaire

### Où obtenir de l'aide ?

1. **GitHub Issues**
   - Créer une issue avec les logs
   - Inclure la version de HA

2. **Forum Home Assistant**
   - Section "Third Party Integrations"
   - En français ou anglais

3. **Discord Home Assistant FR**
   - Canal #développement

---

## Checklist de dépannage

Avant de demander de l'aide, vérifier :

- [ ] Logs consultés (mode debug activé)
- [ ] Version de HA à jour
- [ ] Intégration réinstallée proprement
- [ ] Tokens régénérés
- [ ] API Netatmo fonctionnelle (test manuel)
- [ ] Navigateur à jour (cache vidé)
- [ ] Permissions fichiers correctes
- [ ] Connexion Internet stable

---

## Conclusion

Ce guide couvre les problèmes les plus courants. Si votre problème persiste :

1. Activer le mode debug
2. Collecter les logs
3. Créer une issue GitHub avec tous les détails

**Important** : Ne jamais partager vos tokens/secrets dans les rapports de bug !

---

*Guide de dépannage - Muller Intuis Connect v1.0*
*Dernière mise à jour : 4 novembre 2025*
