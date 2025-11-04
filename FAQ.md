# ❓ FAQ - Questions Fréquentes

## 🔐 Authentification et Configuration

### Q: Où trouver mon Client ID et Client Secret ?

**R:** Sur le portail développeur Netatmo :
1. Allez sur [dev.netatmo.com](https://dev.netatmo.com)
2. Connectez-vous avec vos identifiants Muller Intuitiv
3. Cliquez sur "Create" pour créer une nouvelle app
4. Une fois créée, vous verrez votre Client ID et Client Secret

### Q: Quelle différence entre Client ID/Secret et Username/Password ?

**R:** 
- **Client ID / Client Secret** : Identifiants de votre **application** créée sur dev.netatmo.com
- **Username / Password** : Vos identifiants **personnels** Muller Intuitiv (ceux de l'app mobile)

### Q: Puis-je utiliser les mêmes identifiants sur plusieurs installations HA ?

**R:** Oui ! Vous pouvez utiliser le même Client ID/Secret et Username/Password sur plusieurs installations Home Assistant. L'API Netatmo gère plusieurs connexions simultanées.

### Q: Mes identifiants sont-ils sécurisés ?

**R:** Oui :
- Ils sont stockés de manière sécurisée dans Home Assistant
- Les mots de passe ne sont jamais affichés dans les logs
- Les tokens sont automatiquement rafraîchis sans exposer vos credentials

## 🔄 Fonctionnement

### Q: À quelle fréquence les données sont-elles mises à jour ?

**R:** Toutes les **5 minutes** par défaut. C'est un bon équilibre entre réactivité et sollicitation de l'API.

### Q: Comment forcer une mise à jour immédiate ?

**R:** Utilisez le service `homeassistant.update_entity` :
```yaml
service: homeassistant.update_entity
target:
  entity_id: climate.muller_salon
```

### Q: Les tokens expirent-ils ?

**R:** Les tokens OAuth2 expirent après ~3 heures, mais l'intégration les rafraîchit **automatiquement** 5 minutes avant expiration. Vous n'avez rien à faire.

### Q: Que se passe-t-il si Home Assistant redémarre ?

**R:** Les tokens sont sauvegardés dans la configuration de l'intégration. Au redémarrage, Home Assistant les récupère et continue à fonctionner normalement.

## 🏠 Fonctionnalités

### Q: Quelles entités sont créées ?

**R:** Pour chaque radiateur/pièce :
- `climate.muller_[nom_piece]` - Contrôle du thermostat
- `sensor.muller_[nom_piece]_temperature` - Température actuelle
- `sensor.muller_[nom_piece]_heating_power_request` - Puissance de chauffe
- `sensor.muller_[nom_piece]_daily_energy` - Consommation journalière

Plus une entité globale :
- `select.muller_intuis_active_schedule` - Planning actif

### Q: Comment changer la température d'un radiateur ?

**R:** Via le service `climate.set_temperature` :
```yaml
service: climate.set_temperature
target:
  entity_id: climate.muller_salon
data:
  temperature: 21
```

### Q: Comment changer de planning ?

**R:** Via l'entité `select` :
```yaml
service: select.select_option
target:
  entity_id: select.muller_intuis_active_schedule
data:
  option: "Planning Jour"
```

### Q: Puis-je créer/modifier des plannings depuis HA ?

**R:** Actuellement, l'intégration permet de :
- ✅ Voir tous les plannings disponibles
- ✅ Changer le planning actif
- ❌ Créer de nouveaux plannings (à venir dans une future version)
- ❌ Modifier les plannings existants (à venir)

Pour créer/modifier des plannings, utilisez l'application mobile Muller Intuitiv.

### Q: Les modes HVAC correspondent à quoi ?

**R:** 
- `auto` → Mode planning (suit le planning actif)
- `heat` → Mode manuel (température fixe)
- `off` → Hors-gel

## 🔧 Problèmes courants

### Q: Erreur "invalid_auth" lors de la configuration

**R:** Vérifiez que :
1. Votre Client ID et Client Secret sont corrects (depuis dev.netatmo.com)
2. Votre email et mot de passe sont ceux de l'app Muller Intuitiv
3. Vous pouvez vous connecter à l'app mobile avec ces identifiants

### Q: Erreur "cannot_connect"

**R:** 
1. Vérifiez votre connexion internet
2. Vérifiez que `https://app.muller-intuitiv.net` est accessible
3. Consultez les logs Home Assistant pour plus de détails

### Q: Erreur "No homes found in account"

**R:** L'API ne trouve pas de maison/radiateurs. Vérifiez :
1. Que vos radiateurs sont bien configurés dans l'app Muller Intuitiv
2. Que vous utilisez les bons identifiants (même compte que l'app mobile)
3. Que vous voyez bien vos radiateurs dans l'app mobile

### Q: Les températures ne se mettent pas à jour

**R:** 
1. Attendez jusqu'à 5 minutes (intervalle de mise à jour)
2. Vérifiez les logs pour des erreurs d'authentification
3. Forcez une mise à jour avec `homeassistant.update_entity`
4. Si le problème persiste, reconfigurer l'intégration

### Q: Erreur 401 (Authentication failed)

**R:** Le token a probablement expiré et n'a pas pu être rafraîchi. Solutions :
1. Attendez 5 minutes (rafraîchissement automatique)
2. Redémarrez Home Assistant
3. Si ça persiste, supprimez et reconfigurez l'intégration

## 🔀 Migration et compatibilité

### Q: Puis-je utiliser l'intégration en même temps que Node-RED ?

**R:** **Oui !** Les deux peuvent fonctionner simultanément sans problème. L'API Netatmo gère plusieurs connexions. C'est idéal pour tester l'intégration avant de migrer complètement.

### Q: Comment migrer depuis Node-RED ?

**R:** Consultez le guide détaillé : [MIGRATION_NODE_RED.md](MIGRATION_NODE_RED.md)

En bref :
1. Récupérez vos identifiants de Node-RED
2. Installez l'intégration HA
3. Testez en parallèle avec Node-RED actif
4. Migrez progressivement vos automatisations
5. Désactivez Node-RED quand tout fonctionne

### Q: L'intégration est-elle compatible avec l'app mobile Muller ?

**R:** **Oui !** Vous pouvez utiliser :
- L'app mobile Muller Intuitiv
- L'intégration Home Assistant
- Node-RED (si vous l'utilisez encore)

Tous en même temps, sans conflit.

## 🌐 API et Technique

### Q: Quelle API est utilisée ?

**R:** L'API Netatmo Energy, qui est le backend de Muller Intuitiv :
- Endpoint OAuth2 : `https://app.muller-intuitiv.net/oauth2/token`
- Grant type : `password` (Resource Owner Password Credentials)
- Scopes : `read_muller write_muller`
- User prefix : `muller`

### Q: Pourquoi utiliser l'API Netatmo ?

**R:** Muller Intuitiv est construit sur la plateforme Netatmo Energy. Les radiateurs Muller utilisent donc nativement l'API Netatmo avec un préfixe spécifique ("muller").

### Q: Y a-t-il des limites de l'API ?

**R:** Netatmo applique des rate limits, mais avec un intervalle de mise à jour de 5 minutes, vous êtes largement en dessous des limites.

### Q: Puis-je utiliser l'intégration sans compte Netatmo ?

**R:** Non, vous devez avoir :
1. Un compte Muller Intuitiv (avec radiateurs configurés)
2. Une application créée sur dev.netatmo.com (utilisant ce même compte)

## 📊 Performance et Logs

### Q: L'intégration consomme-t-elle beaucoup de ressources ?

**R:** Non, très peu :
- Mise à jour toutes les 5 minutes uniquement
- Pas de polling constant
- Gestion intelligente des tokens (pas de requêtes inutiles)

### Q: Comment activer les logs détaillés ?

**R:** Ajoutez dans `configuration.yaml` :
```yaml
logger:
  default: info
  logs:
    custom_components.muller_intuis: debug
```

Puis redémarrez Home Assistant.

### Q: Que dois-je vérifier dans les logs en cas de problème ?

**R:** Recherchez dans les logs :
- `muller_intuis` - Messages généraux
- `Token refresh` - Rafraîchissement des tokens
- `API error` - Erreurs d'API
- `Authentication failed` - Problèmes d'authentification

## 🚀 Améliorations futures

### Q: Quelles fonctionnalités sont prévues ?

**R:** Roadmap envisagée :
- [ ] Création de plannings depuis HA
- [ ] Modification de plannings existants
- [ ] Support des scènes Muller
- [ ] Statistiques de consommation avancées
- [ ] Support du mode boost

Les contributions sont les bienvenues sur GitHub !

## 🆘 Support

### Q: Où obtenir de l'aide ?

**R:** 
1. **Consultez cette FAQ** et le [README.md](README.md)
2. **Vérifiez les logs** Home Assistant
3. **Testez votre authentification** avec `python3 test_auth.py`
4. **Ouvrez une issue** sur [GitHub](https://github.com/TheFab21/muller-intuis/issues)

### Q: Comment contribuer au projet ?

**R:** 
1. Fork le projet sur GitHub
2. Créez une branche pour votre fonctionnalité
3. Testez vos modifications
4. Ouvrez une Pull Request

Toute contribution est appréciée ! 🙏

---

**Une question manquante ?** → Ouvrez une [issue sur GitHub](https://github.com/TheFab21/muller-intuis/issues)
